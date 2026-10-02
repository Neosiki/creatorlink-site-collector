import re, json, sys, time, urllib.request, urllib.parse, html, collections
HOST='rty0102.creatorlink.net'; BASE='https://'+HOST
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36'}
def get(u,tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(u,headers=UA)
            with urllib.request.urlopen(req,timeout=40) as r:
                return r.read(), r.headers.get('Content-Type','')
        except Exception as e:
            err=e; time.sleep(1.5)
    return None, str(err)
def norm(u,page):
    u=html.unescape(u.strip())
    if u.startswith('//'): u='https:'+u
    return urllib.parse.urljoin(page,u)
IMG_RE=re.compile(r'''(?:https?:)?//storage\.googleapis\.com/cr-resource/image/[^"'\s)<>\\]+''')
GUC_RE=re.compile(r'''https://lh3\.googleusercontent\.com/[^"'\s)<>\\]+''')
VID_RE=re.compile(r'''(?:https?:)?//[^"'\s)<>\\]+\.(?:mp4|webm|mov|m3u8)(?:\?[^"'\s)<>\\]*)?''',re.I)
EMB_RE=re.compile(r'''(?:https?:)?//(?:www\.)?(?:youtube\.com/embed/|youtube-nocookie\.com/embed/|player\.vimeo\.com/video/|youtu\.be/)[^"'\s)<>\\]+''')
YT_RE=re.compile(r'''(?:https?:)?//(?:www\.)?youtube\.com/watch\?v=[^"'\s)<>\\&]+''')
seen={}; queue=collections.deque([BASE+'/']); pages={}
imgs=collections.defaultdict(set); vids=collections.defaultdict(set); embeds=collections.defaultdict(set)
SKIP=re.compile(r'(/css/|/js/|/config|/login|/join|/logout|/sitemap|\.(css|js|png|jpg|jpeg|gif|ico|svg|pdf)(\?|$))',re.I)
while queue:
    u=queue.popleft().split('#')[0]
    if u in seen: continue
    seen[u]=1; print(len(seen),len(queue),urllib.parse.unquote(u),flush=True)
    data,ct=get(u)
    if data is None: print('FAIL',u,ct); continue
    if 'html' not in ct: continue
    t=data.decode('utf-8','replace')
    title=re.search(r'<title>(.*?)</title>',t,re.S); pages[u]=html.unescape(title.group(1).strip()) if title else ''
    for m in IMG_RE.findall(t): imgs[u].add(norm(m,u))
    for m in GUC_RE.findall(t): imgs[u].add(norm(m,u))
    for m in VID_RE.findall(t): vids[u].add(norm(m,u))
    for m in EMB_RE.findall(t)+YT_RE.findall(t): embeds[u].add(norm(m,u))
    for h in re.findall(r'href=["\']([^"\']+)["\']',t):
        h=norm(h,u)
        p=urllib.parse.urlparse(h)
        if p.netloc!=HOST or SKIP.search(p.path): continue
        h=urllib.parse.urlunparse((p.scheme,p.netloc,p.path,'',p.query,''))
        if h not in seen: queue.append(h)
    if len(seen)>400: break
out={'pages':pages,'imgs':{k:sorted(v) for k,v in imgs.items()},'vids':{k:sorted(v) for k,v in vids.items()},'embeds':{k:sorted(v) for k,v in embeds.items()}}
json.dump(out,open('manifest_raw.json','w'),ensure_ascii=False,indent=1)
print('pages',len(pages)); allimg=set(x for v in imgs.values() for x in v); print('unique img urls',len(allimg))
print('vids',sum(len(v) for v in vids.values()),'embeds',sum(len(v) for v in embeds.values()))
for u,t in pages.items(): print(len(imgs.get(u,())),len(vids.get(u,())),len(embeds.get(u,())),urllib.parse.unquote(u),'|',t[:40])
