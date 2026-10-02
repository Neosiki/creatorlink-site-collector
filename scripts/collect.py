#!/usr/bin/env python3
"""creatorlink-site-collector

Creatorlink(애드블록) 계열 포트폴리오 사이트의 이미지·영상 주소·설명 글을 메뉴 단위로 수집한다.
Python 3.8+ 표준 라이브러리만 사용하며, 이미지 크기 측정과 검증에만 Pillow를 선택적으로 쓴다.

하위 명령
  discover   홈 화면의 메뉴 목록을 찾아 출력한다.
  collect    메뉴 하나(또는 전체)를 완결 형태로 수집한다.
  verify     수집 결과를 점검한다(파일·대응표 일치, 목록 API 대조, 열림 검사).
  master     메뉴별 대응표를 한 파일로 합친다.

수집 대상은 사이트 운영자가 허락한 자료로 한정해 쓴다. 저작권은 원 작가에게 있다.
"""
import argparse, csv, hashlib, html, io, json, os, re, shutil, sys, time
import urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

VERSION = '1.0.0'
UA = 'Mozilla/5.0 (compatible; creatorlink-site-collector/%s)' % VERSION
SIZES = ['', '1920/', '800/', '700/', '670/']          # 원본 → 큰 변형 → 작은 변형 순서
PLACEHOLDER_CAPTIONS = ('텍스트를 변경할 수 있습니다', 'Phasellus vulputate', 'Lorem ipsum')
PLACEHOLDER_TITLES = ('제목', 'Title')
SYSTEM_PREFIX = ('/css', '/js', '/config', '/template', '/img', '/fonts', '/_', '/login', '/join', '/logout', '/sitemap', '/robots')

LABELS = {
    'ko': dict(images='이미지', videos='영상', details='상세페이지', mapping='파일명대응표.csv', text='작품설명.txt',
               source='원본페이지.html', listdata='목록데이터.json', done='수집완료.txt', undone='수집미완료.txt',
               videolist='영상목록.csv', common='00_공통', stale='_이전파일',
               cols=['번호', '파일명', '가로px', '세로px', '바이트', '해시', '페이지요소', '출처페이지', '원본URL', '작품제목', '작품캡션'],
               vcols=['출처페이지', '영상URL']),
    'en': dict(images='images', videos='videos', details='detail_pages', mapping='mapping.csv', text='description.txt',
               source='source.html', listdata='list_data.json', done='COMPLETE.txt', undone='INCOMPLETE.txt',
               videolist='video_list.csv', common='00_common', stale='_stale',
               cols=['no', 'file', 'width', 'height', 'bytes', 'sha1_12', 'element', 'source_page', 'source_url', 'title', 'caption'],
               vcols=['source_page', 'video_url']),
}

# ---------------------------------------------------------------- 네트워크
def quote_url(u):
    if u.startswith('//'):
        u = 'https:' + u
    p = urllib.parse.urlsplit(u)
    path = urllib.parse.quote(urllib.parse.unquote(p.path), safe='/%')
    return urllib.parse.urlunsplit((p.scheme, p.netloc, path, p.query, ''))

class NotFound(Exception):
    pass

def fetch(url, data=None, binary=False, tries=3, headers=None, timeout=60):
    """GET/POST. 404는 즉시 NotFound(재시도 없음), 그 밖의 오류는 tries회 재시도."""
    last = None
    for _ in range(tries):
        try:
            h = {'User-Agent': UA}
            h.update(headers or {})
            req = urllib.request.Request(quote_url(url), data=data, headers=h)
            r = urllib.request.urlopen(req, timeout=timeout)
            body = r.read()
            return (body, r.headers.get('Content-Type', '')) if binary else body.decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                raise NotFound(str(e))
            last = e
        except Exception as e:
            last = e
        time.sleep(1.5)
    raise last

# ---------------------------------------------------------------- 사이트 해석
def strip_tags(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

def discover_menus(base):
    """홈 화면 링크에서 메뉴(이름, 경로)를 찾는다. 자산·시스템 경로와 상세 보기 링크는 제외."""
    t = fetch(base + '/')
    seen, out = set(), []
    for m in re.finditer(r'<a[^>]+href="(/[^"#?]*)"[^>]*>(.*?)</a>', t, re.S):
        path = urllib.parse.unquote(m.group(1))
        if path == '/' or path.startswith(SYSTEM_PREFIX) or '/view/' in path or re.search(r'\.\w{2,4}$', path):
            continue
        if path in seen:
            continue
        seen.add(path)
        name = strip_tags(m.group(2)) or path.strip('/')
        out.append((name, path.strip('/')))
    return out, t

def detect_site(home_html):
    """소유자 id, 계정 해시, 사이트 공통 로고 해시를 홈 화면에서 찾는다."""
    m = re.search(r'cr-resource/image/([0-9a-f]{32})/([A-Za-z0-9_\-]+)/', home_html)
    acct, owner = (m.group(1), m.group(2)) if m else ('', '')
    if not owner:
        m2 = re.search(r'"sid":"([A-Za-z0-9_\-]+)"', home_html)
        owner = m2.group(1) if m2 else ''
    logo = ''
    if owner:
        body = home_html[home_html.find('<body'):]
        m3 = re.search(r'<img[^>]+src="[^"]*cr-resource/image/[0-9a-f]{32}/%s/(?:\d+/)?([0-9a-f]{32})\.\w+"[^>]*data-attach' % re.escape(owner), body)
        logo = m3.group(1).lower() if m3 else ''
    return dict(owner=owner, acct=acct, logo=logo)

def api_items(base, owner, page_html, delay=0.0):
    """페이지에 박힌 갤러리 목록(첫 화면 일부)을 찾고, 사이트가 '더보기'에 쓰는 요청으로 전체 목록을 받는다."""
    dec = json.JSONDecoder()
    groups = {}
    for m in re.finditer(r'"list":\[', page_html):
        try:
            lst, _ = dec.raw_decode(page_html[m.end() - 1:])
        except Exception:
            continue
        for it in lst:
            groups.setdefault(it['pid'], (it['page'], []))[1].append(it)
    items, meta = [], {}
    for pid, (page, first) in groups.items():
        got = None
        for _ in range(3):
            try:
                url = '%s/template/gallery/list/pid/%s/sid/%s/spage/%s/view/5000' % (base, pid, owner, urllib.parse.quote(page))
                form = urllib.parse.urlencode({'g_mode': 'gallery', 'visible': 'true', 'sfl': 'category', 'stx': '', 'orderby': ''}).encode()
                got = json.loads(fetch(url, data=form, headers={'X-Requested-With': 'XMLHttpRequest'}, tries=1))
                break
            except Exception:
                time.sleep(1.5)
        lst = got['list'] if got else first
        total = (got['total']['list_total'] if isinstance(got['total'], dict) else got['total']) if got else len(first)
        meta[pid] = dict(page=page, total=total, got=len(lst), api_ok=got is not None)
        items += lst
        if delay:
            time.sleep(delay)
    return items, meta

def media_candidates(text, owner, acct, logo):
    """페이지 문자열에서 이미지 후보를 뽑는다. (키, 내려받기 후보 주소 목록, 주변 요소 id)
    - 소유자 폴더의 사진만 쓴다(템플릿 견본 이미지 제외).
    - 같은 사진의 크기 변형은 해시로 묶고, 원본 → 1920 → 800 → 700 → 670 순으로 시도한다.
    - lh3.googleusercontent.com 이미지는 =s0(원본 크기)로 요청한다."""
    out = []
    for m in re.finditer(r'(?:https?:)?//lh3\.googleusercontent\.com/([A-Za-z0-9_\-]+)(?:=[A-Za-z0-9\-]+)?', text):
        out.append(('lh3:' + m.group(1), ['https://lh3.googleusercontent.com/%s=s0' % m.group(1)], text[max(0, m.start() - 300):m.start()]))
    full = re.compile(r'cr-resource/image/([0-9a-f]{32})/%s/(?:(\d+)/)?([0-9a-f]{32})\.(jpe?g|png|gif|webp)' % re.escape(owner), re.I)
    for m in full.finditer(text):
        a, _, h, ex = m.groups()
        if h.lower() == logo:
            continue
        out.append(('st:' + h.lower(), ['https://storage.googleapis.com/cr-resource/image/%s/%s/%s%s.%s' % (a, owner, z, h, ex) for z in SIZES],
                    text[max(0, m.start() - 300):m.start()]))
    for m in re.finditer(r'src="/(\d+)/([0-9a-f]{32})\.(jpe?g|png|gif|webp)"', text, re.I):
        _, h, ex = m.groups()
        if h.lower() == logo or not acct:
            continue
        out.append(('st:' + h.lower(), ['https://storage.googleapis.com/cr-resource/image/%s/%s/%s%s.%s' % (acct, owner, z, h, ex) for z in SIZES], ''))
    return out

VIDEO_RE = re.compile(r'(?:https?:)?//[^"\'\s)\\<>]+\.(?:mp4|webm|mov|m3u8)[^"\'\s)\\<>]*', re.I)
EMBED_RE = re.compile(r'(?:https?:)?//(?:www\.)?(?:youtube\.com/(?:embed|watch)[^"\'\s)\\<>]*|youtu\.be/[^"\'\s)\\<>]*|'
                      r'player\.vimeo\.com/video/[^"\'\s)\\<>]*|vimeo\.com/\d+[^"\'\s)\\<>]*)')

def clean_caption(item):
    title = html.unescape(item.get('title', '')).strip()
    cap = strip_tags((item.get('caption', '') or '') + ' ' + (item.get('content', '') or ''))
    if any(p in cap for p in PLACEHOLDER_CAPTIONS):
        cap = ''
    if title in PLACEHOLDER_TITLES:
        title = ''
    return title, cap

def sniff_ext(d):
    if d[:3] == b'\xff\xd8\xff': return '.jpg'
    if d[:8] == b'\x89PNG\r\n\x1a\n': return '.png'
    if d[:4] == b'GIF8': return '.gif'
    if d[:4] == b'RIFF' and d[8:12] == b'WEBP': return '.webp'
    return '.bin'

def dims(d):
    try:
        from PIL import Image
        return Image.open(io.BytesIO(d)).size
    except Exception:
        return ('', '')

def page_text(t, nav_names):
    b = t[t.find('<body'):]
    b = re.sub(r'<script.*?</script>', '', b, flags=re.S)
    b = re.sub(r'<style.*?</style>', '', b, flags=re.S)
    b = re.sub(r'<(?:br|/p|/div|/h\d|/li)[^>]*>', '\n', b)
    lines, prev = [], None
    for l in html.unescape(re.sub(r'<[^>]+>', '\n', b)).split('\n'):
        l = l.replace('‌', '').strip()
        if not l or l in nav_names or l == prev:
            continue
        lines.append(l); prev = l
    return lines

# ---------------------------------------------------------------- 메뉴 수집
def safe_name(s):
    return re.sub(r'[\\/:*?"<>|]', ' ', s).strip().replace(' ', '_')

def collect_menu(base, site, idx, name, path, out, lang='ko', workers=12, budget=140.0,
                 cache_dir=None, nav_names=(), delay=0.0, log=print):
    L = LABELS[lang]
    owner, acct, logo = site['owner'], site['acct'], site['logo']
    mdir = os.path.join(out, '%02d_%s' % (idx, safe_name(name)))
    for sub in (L['images'], L['videos'], L['details']):
        os.makedirs(os.path.join(mdir, sub), exist_ok=True)
    cache_dir = cache_dir or os.path.join(out, '.cache')
    os.makedirs(cache_dir, exist_ok=True)
    menu_url = '%s/%s' % (base, path)
    home = fetch(menu_url)
    open(os.path.join(mdir, L['source']), 'w', encoding='utf-8').write(home)
    # 1) 상세 페이지(열리는 것만 저장, 404는 기록)
    pu = urllib.parse.unquote(path)
    det = sorted({urllib.parse.unquote(h)[len(base):] if urllib.parse.unquote(h).startswith(base) else urllib.parse.unquote(h)
                  for h in re.findall(r'href="([^"#]+)"', home)
                  if urllib.parse.unquote(h).lstrip('/').startswith(pu + '/') or ('/view/' in h and pu in urllib.parse.unquote(h))})
    texts, dead = {menu_url: home}, []
    def get_detail(h):
        try:
            return h, fetch(base + h, tries=2)
        except Exception:
            return h, None
    with ThreadPoolExecutor(min(workers, 6)) as ex:
        for h, t in ex.map(get_detail, det):
            if t is None:
                dead.append(h); continue
            texts[base + h] = t
            open(os.path.join(mdir, L['details'], re.sub(r'[^0-9A-Za-z가-힣._-]+', '_', h.strip('/')) + '.html'), 'w', encoding='utf-8').write(t)
    # 2) 전체 목록 API
    api, meta = api_items(base, owner, home, delay)
    json.dump({'meta': meta, 'items': api}, open(os.path.join(mdir, L['listdata']), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 3) 이미지·영상 후보(목록 API → 상세 페이지 → 메뉴 페이지 순)
    items, seen, vids = [], set(), []
    for it in api:
        h, _, ex_ = it['image'].partition('.')
        h = h.lower()
        if h == logo or not re.fullmatch(r'[0-9a-f]{32}', h) or 'st:' + h in seen:
            continue
        seen.add('st:' + h)
        items.append((menu_url + ' (list)', 'st:' + h,
                      ['https://storage.googleapis.com/cr-resource/image/%s/%s/%s%s.%s' % (acct, owner, z, h, ex_ or 'jpg') for z in SIZES], 'seq' + str(it.get('seq', ''))))
    for pg in [k for k in texts if k != menu_url] + [menu_url]:
        t = texts[pg]
        for key, cands, ctx in media_candidates(t, owner, acct, logo):
            if key in seen:
                continue
            seen.add(key)
            el = re.findall(r'user(?:EL|ADD)\d+', ctx)
            items.append((pg, key, cands, el[-1] if el else ''))
        for m in list(VIDEO_RE.finditer(t)) + list(EMBED_RE.finditer(t)):
            u = re.sub(r'^//', 'https://', m.group(0))
            if u not in [v[1] for v in vids]:
                vids.append((pg, u))
    # 4) 캡션
    caps = {}
    for pg, t in texts.items():
        mi = re.search(r'<meta property="og:image" content="[^"]*?([0-9a-f]{32})\.[A-Za-z]+"', t)
        mt = re.search(r'<meta property="og:title" content="(.*?)" data-dynamic', t, re.S)
        md = re.search(r'<meta property="og:description" content="(.*?)" data-dynamic', t, re.S)
        if mi and '/view/' in pg:
            cap = {'title': mt.group(1) if mt else '', 'caption': md.group(1) if md else '', 'content': ''}
            ti, cp = clean_caption(cap)
            if ti or cp:
                caps[mi.group(1).lower()] = (ti, cp)
    for it in api:
        ti, cp = clean_caption(it)
        if ti or cp:
            caps[it['image'].split('.')[0].lower()] = (ti, cp)
    # 5) 공통 로고는 한 번만 따로 저장
    if logo:
        common = os.path.join(out, L['common']); os.makedirs(common, exist_ok=True)
        lp = os.path.join(common, 'site_logo_%s.jpg' % logo[:8])
        if not os.path.exists(lp):
            for ext in ('JPG', 'jpg', 'png'):
                try:
                    open(lp, 'wb').write(fetch('https://storage.googleapis.com/cr-resource/image/%s/%s/%s.%s' % (acct, owner, logo, ext), binary=True)[0]); break
                except Exception:
                    pass
    # 6) 내려받기(캐시·시간 예산·이어받기)
    T0 = time.time()
    def download(it):
        pg, key, cands, el = it
        k = hashlib.md5(key.encode()).hexdigest()
        cf, cu = os.path.join(cache_dir, k + '.bin'), os.path.join(cache_dir, k + '.url')
        if os.path.exists(cf) and os.path.exists(cu):
            return it, open(cf, 'rb').read(), open(cu, encoding='utf-8').read(), None
        if time.time() - T0 > budget:
            return it, 'DEFER', '', None
        err = None
        for c in cands:
            try:
                d, _ = fetch(c, binary=True, tries=2)
                open(cf, 'wb').write(d); open(cu, 'w', encoding='utf-8').write(c)
                return it, d, c, None
            except NotFound as e:
                err = str(e)                       # 404는 다음 크기 변형으로
            except Exception as e:
                return it, None, cands[0], str(e)  # 일시 오류는 캐시하지 않고 다음 실행에서 재시도
        open(cf, 'wb').write(b''); open(cu, 'w', encoding='utf-8').write('NOTFOUND ' + cands[0])
        return it, None, cands[0], err
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(download, items))
    deferred = sum(1 for r in res if r[1] == 'DEFER')
    status = dict(menu=name, path=path, version=VERSION, candidates=len(items), deferred=deferred,
                  api_lists=len(meta), api_total=sum(m['total'] for m in meta.values()),
                  api_failed=sum(1 for m in meta.values() if not m['api_ok']), detail_dead=len(dead), detail_ok=len(texts) - 1)
    if deferred:
        status['state'] = 'partial'
        log('PARTIAL %d/%d downloaded; 같은 명령을 다시 실행하면 이어서 받습니다' % (len(res) - deferred, len(res)))
        json.dump(status, open(os.path.join(mdir, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        return status
    # 7) 저장·중복 제거·대응표
    rows, shas, dup, failed, n = [], {}, 0, [], 0
    imgdir = os.path.join(mdir, L['images'])
    keep = set()
    for it, d, used, err in res:
        pg, key, cands, el = it
        if d is None or d == b'':
            failed.append((used, err or 'not found')); continue
        sha = hashlib.sha1(d).hexdigest()
        if sha in shas:
            dup += 1; continue
        n += 1
        fn = '%s_%03d%s' % (safe_name(name), n, sniff_ext(d))
        tmp = os.path.join(imgdir, fn + '.part')
        open(tmp, 'wb').write(d); os.replace(tmp, os.path.join(imgdir, fn))
        shas[sha] = fn; keep.add(fn)
        w, h = dims(d)
        hh = re.search(r'([0-9a-f]{32})\.[A-Za-z]+$', used.split('?')[0])
        ti, cp = caps.get(hh.group(1).lower(), ('', '')) if hh else ('', '')
        rows.append([n, fn, w, h, len(d), sha[:12], el, pg.replace(base, ''), used, ti, cp])
    stale = [f for f in os.listdir(imgdir) if f not in keep]
    if stale:                                              # 이전 실행의 남은 파일은 지우지 않고 따로 옮긴다
        sd = os.path.join(mdir, L['stale']); os.makedirs(sd, exist_ok=True)
        for f in stale:
            shutil.move(os.path.join(imgdir, f), os.path.join(sd, f))
    with open(os.path.join(mdir, L['mapping']), 'w', encoding='utf-8-sig', newline='') as f:
        w_ = csv.writer(f); w_.writerow(L['cols']); w_.writerows(rows)
    if vids:
        with open(os.path.join(mdir, L['videos'], L['videolist']), 'w', encoding='utf-8-sig', newline='') as f:
            w_ = csv.writer(f); w_.writerow(L['vcols']); w_.writerows([[p.replace(base, ''), u] for p, u in vids])
    lines = []
    for pg, t in texts.items():
        title = re.search(r'<title>(.*?)</title>', t, re.S)
        lines.append('=== %s (%s) ===' % (pg.replace(base, ''), html.unescape(title.group(1).strip()) if title else ''))
        lines += page_text(t, set(nav_names)); lines.append('')
    open(os.path.join(mdir, L['text']), 'w', encoding='utf-8').write('\n'.join(lines))
    status.update(saved=n, duplicates=dup, download_failed=len(failed), videos=len(vids), stale_moved=len(stale))
    status['state'] = 'complete' if status['api_failed'] == 0 else 'incomplete'
    rep = ['menu: %s' % name, 'path: /%s' % pu, 'time: %s' % time.strftime('%Y-%m-%d %H:%M:%S'),
           'state: %s' % status['state'], 'images: candidates %d -> saved %d (content duplicates %d, failed %d)' % (len(items), n, dup, len(failed)),
           'videos/embeds: %d' % len(vids), 'list API items: %d (lists %d, API failures %d)' % (status['api_total'], status['api_lists'], status['api_failed']),
           'detail pages: ok %d, dead(404) %d' % (status['detail_ok'], len(dead))]
    if failed:
        rep.append('failed images: ' + '; '.join('%s (%s)' % x for x in failed))
    open(os.path.join(mdir, L['done'] if status['state'] == 'complete' else L['undone']), 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
    json.dump(status, open(os.path.join(mdir, 'status.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log('\n'.join(rep))
    return status

# ---------------------------------------------------------------- 검증 / 합치기
def verify_menu(mdir, lang='ko', cache_dir=None):
    L = LABELS[lang]
    rows = list(csv.reader(open(os.path.join(mdir, L['mapping']), encoding='utf-8-sig')))[1:]
    files = set(os.listdir(os.path.join(mdir, L['images'])))
    names = {r[1] for r in rows}
    bad = 0
    try:
        from PIL import Image
        for f in files:
            try: Image.open(os.path.join(mdir, L['images'], f)).verify()
            except Exception: bad += 1
    except ImportError:
        bad = None
    rep = dict(menu=os.path.basename(mdir), rows=len(rows), files=len(files), orphans=sorted(files - names), missing=sorted(names - files),
               unreadable=bad, total_mb=round(sum(int(r[4]) for r in rows) / 1e6, 1))
    lp = os.path.join(mdir, L['listdata'])
    if os.path.exists(lp):
        J = json.load(open(lp, encoding='utf-8'))
        in_csv = {m.group(1) for r in rows for m in [re.search(r'([0-9a-f]{32})\.', r[8])] if m}
        have_sha = {r[5] for r in rows}
        uncovered, dup_cov, src_missing = [], 0, 0
        for h in sorted({i['image'].split('.')[0].lower() for i in J['items']} - in_csv):
            k = hashlib.md5(('st:' + h).encode()).hexdigest()
            cf = os.path.join(cache_dir or os.path.join(os.path.dirname(mdir), '.cache'), k + '.bin')
            if os.path.exists(cf):
                d = open(cf, 'rb').read()
                if d == b'': src_missing += 1
                elif hashlib.sha1(d).hexdigest()[:12] in have_sha: dup_cov += 1
                else: uncovered.append(h)
            else:
                uncovered.append(h)
        rep.update(api_items=len(J['items']), api_unique=len({i['image'].split('.')[0].lower() for i in J['items']}),
                   covered_by_content_duplicate=dup_cov, source_file_missing=src_missing, UNCOVERED=uncovered,
                   lists=[(m['got'], m['total']) for m in J['meta'].values()])
    rep['ok'] = not rep['orphans'] and not rep['missing'] and not rep.get('UNCOVERED') and not rep['unreadable']
    return rep

def build_master(out, lang='ko'):
    L = LABELS[lang]
    rows = []
    for d in sorted(os.listdir(out)):
        p = os.path.join(out, d, L['mapping'])
        if os.path.exists(p):
            rows += [[d] + r for r in list(csv.reader(open(p, encoding='utf-8-sig')))[1:]]
    with open(os.path.join(out, 'master_' + L['mapping']), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['menu'] + L['cols']); w.writerows(rows)
    return len(rows)

# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('discover', 'collect'):
        p = sub.add_parser(name); p.add_argument('--base', required=True, help='예: https://example.creatorlink.net')
    c = sub.choices['collect']
    c.add_argument('--out', required=True); c.add_argument('--menu', action='append', help='메뉴 경로(예: 해인사). 여러 번 지정 가능')
    c.add_argument('--all', action='store_true', help='홈에서 찾은 모든 메뉴를 차례로 수집')
    c.add_argument('--lang', choices=['ko', 'en'], default='ko'); c.add_argument('--workers', type=int, default=12)
    c.add_argument('--budget', type=float, default=140.0, help='한 번 실행에서 내려받기에 쓸 최대 초(초과분은 다음 실행에서 이어받음)')
    c.add_argument('--delay', type=float, default=0.0, help='목록 요청 사이 대기(초)')
    v = sub.add_parser('verify'); v.add_argument('--out', required=True); v.add_argument('--lang', choices=['ko', 'en'], default='ko')
    m = sub.add_parser('master'); m.add_argument('--out', required=True); m.add_argument('--lang', choices=['ko', 'en'], default='ko')
    a = ap.parse_args(argv)
    if a.cmd == 'discover':
        menus, home = discover_menus(a.base.rstrip('/'))
        print(json.dumps(dict(site=detect_site(home), menus=[dict(index=i + 1, name=n, path=p) for i, (n, p) in enumerate(menus)]), ensure_ascii=False, indent=1))
    elif a.cmd == 'collect':
        base = a.base.rstrip('/')
        menus, home = discover_menus(base)
        site = detect_site(home)
        if not site['owner']:
            sys.exit('소유자 id를 찾지 못했습니다. 홈 화면 형식을 확인하세요.')
        nav = {n for n, _ in menus} | {'Toggle navigation'}
        if a.menu:
            want = [urllib.parse.unquote(x).strip('/') for x in a.menu]
            pick = [(i + 1, n, p) for i, (n, p) in enumerate(menus) if p in want]
            missing = [w for w in want if w not in [p for _, p in menus]]
            if missing: sys.exit('홈 메뉴에 없는 경로: %s' % missing)
        elif a.all:
            pick = [(i + 1, n, p) for i, (n, p) in enumerate(menus)]
        else:
            sys.exit('--menu 또는 --all을 지정하세요.')
        rc = 0
        for i, n, p in pick:
            print('=== %02d %s ===' % (i, n))
            st = collect_menu(base, site, i, n, p, a.out, a.lang, a.workers, a.budget, nav_names=nav, delay=a.delay)
            if st['state'] != 'complete': rc = 2
        sys.exit(rc)
    elif a.cmd == 'verify':
        L = LABELS[a.lang]; bad = 0
        for d in sorted(os.listdir(a.out)):
            p = os.path.join(a.out, d)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, L['mapping'])):
                r = verify_menu(p, a.lang); bad += 0 if r['ok'] else 1
                print(json.dumps(r, ensure_ascii=False))
        sys.exit(1 if bad else 0)
    elif a.cmd == 'master':
        print('rows:', build_master(a.out, a.lang))

if __name__ == '__main__':
    main()
