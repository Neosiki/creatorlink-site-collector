import sys,os,re,html,hashlib,csv,time,json,urllib.request,urllib.parse
from concurrent.futures import ThreadPoolExecutor
BASE='https://rty0102.creatorlink.net'
ROOT=os.path.expanduser('~/mnt/01.컨설팅 업무/02.카페보리_경북청도/류태열_온라인도록_자료수집')
UA={'User-Agent':'Mozilla/5.0'}
NAV={'Toggle navigation','불교사진가류태열','해브 갤러리','구례 대 화엄사','해인사','흑백마애불 암각화 봉정사 통도사','운주사','선암사','법주사 존재시리즈','MORE GALLERIES판매작품','flower연꽃사진','Exhibion View 장승','네팔  캄보디아  미얀마','風景 landscape','도서발간','동영상','단 사진','우포','을릉도','ARTISTS Ryu tae-yeol','게시판','전시소식'}
def q(u):
    if u.startswith('//'): u='https:'+u
    p=urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme,p.netloc,urllib.parse.quote(urllib.parse.unquote(p.path),safe='/%'),p.query,''))
def fetch(u,binary=False,tries=3):
    for i in range(tries):
        try:
            r=urllib.request.urlopen(urllib.request.Request(q(u),headers=UA),timeout=60)
            d=r.read(); return (d,r.headers.get('Content-Type','')) if binary else d.decode('utf-8','replace')
        except Exception as e:
            err=e; time.sleep(1.5)
    raise err
IMG_LH=re.compile(r'(?:https?:)?//lh3\.googleusercontent\.com/[A-Za-z0-9_\-]+(?:=[A-Za-z0-9\-]+)?')
IMG_ST=re.compile(r'(?:https?:)?//storage\.googleapis\.com/cr-resource/image/[^"\'\s)\\<>]+')
VID=re.compile(r'(?:https?:)?//[^"\'\s)\\<>]+\.(?:mp4|webm|mov|m3u8)[^"\'\s)\\<>]*',re.I)
EMB=re.compile(r'(?:https?:)?//(?:www\.)?(?:youtube\.com/(?:embed|watch)[^"\'\s)\\<>]*|youtu\.be/[^"\'\s)\\<>]*|player\.vimeo\.com/video/[^"\'\s)\\<>]*|vimeo\.com/\d+[^"\'\s)\\<>]*)')
EXCL=('favicon','screen-thumb','profile_default','/fonts/')
LOGO='5df5a7ca1f8d92f202b33e880e40add1'
ACCT='6e02e7bfd51bb2c8db8e0e209828c836'
OWNER='rty0102'
ST_FULL=re.compile(r'cr-resource/image/([0-9a-f]{32})/'+OWNER+r'/(?:(\d+)/)?([0-9a-f]{32})\.(jpe?g|png|gif|webp)',re.I)
ST_REL=re.compile(r'src="/(\d+)/([0-9a-f]{32})\.(jpe?g|png|gif|webp)"',re.I)
SIZES=['', '1920/', '800/', '700/', '670/']
def media(t):
    out=[]
    for m in IMG_LH.finditer(t):
        u=m.group(0); base=u.split('=')[0]
        if base.endswith('googleusercontent.com'): continue
        out.append(('lh3','lh3:'+base,[base+'=s0'],t[max(0,m.start()-300):m.start()]))
    for m in ST_FULL.finditer(t):
        acct,sz,h,ex=m.groups()
        if h.lower()==LOGO: continue
        out.append(('st','st:'+h.lower(),[f'https://storage.googleapis.com/cr-resource/image/{acct}/{OWNER}/{z}{h}.{ex}' for z in SIZES],t[max(0,m.start()-300):m.start()]))
    for m in ST_REL.finditer(t):
        sz,h,ex=m.groups()
        if h.lower()==LOGO: continue
        out.append(('st','st:'+h.lower(),[f'https://storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/{z}{h}.{ex}' for z in SIZES],''))
    return out
def ext_of(data,ct):
    if data[:3]==b'\xff\xd8\xff': return '.jpg'
    if data[:8]==b'\x89PNG\r\n\x1a\n': return '.png'
    if data[:4]==b'GIF8': return '.gif'
    if data[:4]==b'RIFF' and data[8:12]==b'WEBP': return '.webp'
    return '.bin'
def dims(data):
    try:
        from PIL import Image; import io
        im=Image.open(io.BytesIO(data)); return im.size
    except Exception: return ('','')

def api_items(html0):
    dec=json.JSONDecoder(); pids={}
    for m in re.finditer(r'"list":\[',html0):
        try: lst,_=dec.raw_decode(html0[m.end()-1:])
        except Exception: continue
        for i in lst: pids.setdefault(i['pid'],(i['page'],[]))[1].append(i)
    out=[]; meta={}
    for pid,(pg,first) in pids.items():
        got=None
        for tr in range(3):
            try:
                u=f'{BASE}/template/gallery/list/pid/{pid}/sid/{OWNER}/spage/{urllib.parse.quote(pg)}/view/1000'
                data=urllib.parse.urlencode({'g_mode':'gallery','visible':'true','sfl':'category','stx':'','orderby':''}).encode()
                r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers={'User-Agent':'Mozilla/5.0','X-Requested-With':'XMLHttpRequest'}),timeout=60)
                got=json.loads(r.read().decode()); break
            except Exception as e: time.sleep(1.5)
        lst=got['list'] if got else first
        tot=got['total']['list_total'] if got and isinstance(got['total'],dict) else (got['total'] if got else len(first))
        meta[pid]={'page':pg,'total':tot,'got':len(lst),'api_ok':got is not None}
        out+=lst
    return out,meta

def main(idx,display,path):
    safe=re.sub(r'[\\/:*?"<>|]',' ',display).strip().replace(' ','_')
    mdir=f'{ROOT}/{idx:02d}_{safe}'
    for sub in ('이미지','영상','상세페이지'): os.makedirs(f'{mdir}/{sub}',exist_ok=True)
    pages={BASE+'/'+path:'메뉴페이지'}
    html0=fetch(BASE+'/'+path)
    open(f'{mdir}/원본페이지.html','w',encoding='utf-8').write(html0)
    # detail pages: /view/ links and sub-paths of this menu
    pu=urllib.parse.unquote(path)
    det=set()
    for h in re.findall(r'href="([^"#]+)"',html0):
        hu=urllib.parse.unquote(h)
        if hu.startswith(BASE): hu=hu[len(BASE):]
        if hu.startswith('/'+pu+'/') or (hu.startswith('/'+pu) and '/view/' in hu): det.add(hu)
    detlist=sorted(det)
    texts={BASE+'/'+path:html0}
    def gd(h):
        try: return h,fetch(BASE+h)
        except Exception as e: return h,None
    fails=[]
    with ThreadPoolExecutor(6) as ex:
        for h,t in ex.map(gd,detlist):
            if t is None: fails.append(h)
            else:
                texts[BASE+h]=t
                open(f'{mdir}/상세페이지/'+re.sub(r'[^0-9A-Za-z가-힣._-]+','_',h.strip('/'))+'.html','w',encoding='utf-8').write(t)
    apiit,apimeta=api_items(html0)
    json.dump({'meta':apimeta,'items':apiit},open(f'{mdir}/목록데이터.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    # collect media in page order
    items=[]; seen=set(); vids=[]
    order=[k for k in texts if k!=BASE+'/'+path]+[BASE+'/'+path]
    for it in apiit:
        h=it['image'].split('.')[0].lower(); ex=it['image'].split('.')[-1]
        if h==LOGO or not re.fullmatch(r'[0-9a-f]{32}',h) or 'st:'+h in seen: continue
        seen.add('st:'+h)
        items.append((BASE+'/'+path+'  (목록데이터)','st','st:'+h,[f'https://storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/{z}{h}.{ex}' for z in SIZES],'seq'+it['seq']))
    for pg in order:
        t=texts[pg]; b=t
        for kind,base,dl,ctx in media(b):
            if base in seen: continue
            seen.add(base)
            el=re.findall(r'user(?:EL|ADD)\d+',ctx)
            items.append((pg,kind,base,dl,el[-1] if el else ''))
        for m in list(VID.finditer(t))+list(EMB.finditer(t)):
            u=re.sub(r'^//','https://',m.group(0))
            if u not in [v[1] for v in vids]: vids.append((pg,u))
    caps={}
    for pg,t in texts.items():
        mi=re.search(r'<meta property="og:image" content="[^"]*?([0-9a-f]{32})\.[A-Za-z]+"',t)
        mt=re.search(r'<meta property="og:title" content="(.*?)" data-dynamic',t,re.S); md=re.search(r'<meta property="og:description" content="(.*?)" data-dynamic',t,re.S)
        if mi and '/view/' in pg and '텍스트를 변경할 수 있습니다' not in (md.group(1) if md else ''): caps[mi.group(1).lower()]=(html.unescape(mt.group(1)).strip() if mt else '',re.sub(r'\s+',' ',html.unescape(md.group(1))).strip() if md else '')
    for it in apiit:
        h=it['image'].split('.')[0].lower()
        ti=html.unescape(it['title']).strip(); cp=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',it['caption']+' '+it['content']))).strip()
        if '텍스트를 변경할 수 있습니다' in cp: cp=''
        if ti=='제목': ti=''
        if ti or cp: caps[h]=(ti,cp)
    os.makedirs(ROOT+'/00_공통',exist_ok=True)
    lp=ROOT+'/00_공통/사이트_헤더로고_5df5a7ca.jpg'
    if not os.path.exists(lp):
        try: open(lp,'wb').write(fetch(f'https://storage.googleapis.com/cr-resource/image/{ACCT}/{OWNER}/{LOGO}.JPG',binary=True)[0])
        except Exception as e: print('logo fail',e)
    # download
    CACHE=os.path.expanduser('~/cb/cache'); os.makedirs(CACHE,exist_ok=True)
    T0=time.time(); BUDGET=float(os.environ.get('BUDGET','140'))
    def dlr(it):
        pg,kind,base,dl,el=it
        key=hashlib.md5(base.encode()).hexdigest(); cf=f'{CACHE}/{key}.bin'; cu=f'{CACHE}/{key}.url'
        if os.path.exists(cf) and os.path.exists(cu):
            return it,open(cf,'rb').read(),'',None,open(cu,encoding='utf-8').read()
        if time.time()-T0>BUDGET: return it,'DEFER','',None,''
        last=None
        for cand in dl:
            try:
                d,ct=fetch(cand,binary=True,tries=2)
                open(cf,'wb').write(d); open(cu,'w',encoding='utf-8').write(cand)
                return it,d,ct,None,cand
            except Exception as e: last=str(e)
        open(cf,'wb').write(b''); open(cu,'w',encoding='utf-8').write('FAIL '+dl[0]+' '+str(last))
        return it,None,'',last,dl[0]
    rows=[]; n=0; shas={}; dup=0; dfail=[]
    with ThreadPoolExecutor(14) as ex:
        res=list(ex.map(dlr,items))
    nd=sum(1 for r in res if r[1]=='DEFER')
    if nd:
        print(f'PARTIAL {len(res)-nd}/{len(res)} downloaded; rerun to continue'); return
    for it,d,ct,err,used in res:
        pg,kind,base,dl,el=it
        if d is None or d==b'': dfail.append((used,err or 'cached-fail')); continue
        sha=hashlib.sha1(d).hexdigest()
        if sha in shas: dup+=1; continue
        n+=1; ext=ext_of(d,ct); fn=f'{safe}_{n:03d}{ext}'
        open(f'{mdir}/이미지/{fn}','wb').write(d); shas[sha]=fn
        w,h=dims(d)
        hh=re.search(r'([0-9a-f]{32})\.[A-Za-z]+$',used.split('?')[0]); cp=caps.get(hh.group(1).lower(),('','')) if hh else ('','')
        rows.append([n,fn,w,h,len(d),sha[:12],el,pg.replace(BASE,''),used,cp[0],cp[1]])
    with open(f'{mdir}/파일명대응표.csv','w',encoding='utf-8-sig',newline='') as f:
        wr=csv.writer(f); wr.writerow(['번호','파일명','가로px','세로px','바이트','해시','페이지요소','출처페이지','원본URL','작품제목','작품캡션']); wr.writerows(rows)
    if vids:
        with open(f'{mdir}/영상/영상목록.csv','w',encoding='utf-8-sig',newline='') as f:
            wr=csv.writer(f); wr.writerow(['출처페이지','영상URL']); wr.writerows([[p.replace(BASE,''),u] for p,u in vids])
    # text
    lines=[]
    for pg,t in texts.items():
        b=t[t.find('<body'):]
        b=re.sub(r'<script.*?</script>','',b,flags=re.S); b=re.sub(r'<style.*?</style>','',b,flags=re.S)
        b=re.sub(r'<(?:br|/p|/div|/h\d|/li)[^>]*>','\n',b); tx=html.unescape(re.sub(r'<[^>]+>','\n',b))
        title=re.search(r'<title>(.*?)</title>',t,re.S)
        lines.append('=== '+pg.replace(BASE,'')+' ('+(html.unescape(title.group(1).strip()) if title else '')+') ===')
        prev=None
        for l in tx.split('\n'):
            l=l.replace('‌','').strip()
            if not l or l in NAV or l==prev: continue
            lines.append(l); prev=l
        lines.append('')
    open(f'{mdir}/작품설명.txt','w',encoding='utf-8').write('\n'.join(lines))
    tot=sum(m['total'] for m in apimeta.values()) if apimeta else 0
    rep=f'메뉴: {display}\n경로: /{pu}\n수집일시: {time.strftime("%Y-%m-%d %H:%M:%S")}\n메뉴페이지 1개 + 상세페이지 {len(texts)-1}개 (실패 {len(fails)})\n이미지 후보 {len(items)}건 → 저장 {n}장 (중복 제외 {dup}장, 다운로드 실패 {len(dfail)})\n영상/임베드 {len(vids)}건\n목록 API 작품수 {tot} (목록 {len(apimeta)}개, API 실패 {sum(1 for m in apimeta.values() if not m["api_ok"])})\n'
    if fails: rep+='상세페이지 실패: '+', '.join(fails)+'\n'
    if dfail: rep+='이미지 실패: '+'; '.join(f'{u} ({e})' for u,e in dfail)+'\n'
    open(f'{mdir}/수집완료.txt','w',encoding='utf-8').write(rep)
    print(rep); print(mdir)
if __name__=='__main__': main(int(sys.argv[1]),sys.argv[2],sys.argv[3])
