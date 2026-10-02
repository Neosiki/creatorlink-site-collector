import csv,re,os,sys,glob,json,html,hashlib,urllib.request
R=os.path.expanduser('~/mnt/01.컨설팅 업무/02.카페보리_경북청도/류태열_온라인도록_자료수집')
def run(n):
    d=glob.glob(f'{R}/{n:02d}_*')[0]
    t=open(d+'/원본페이지.html',encoding='utf-8').read()
    dec=json.JSONDecoder(); items={}
    for m in re.finditer(r'"list":\[',t):
        try: lst,_=dec.raw_decode(t[m.end()-1:])
        except Exception: continue
        for i in lst: items[i['seq']]=i
    rows=list(csv.reader(open(d+'/파일명대응표.csv',encoding='utf-8-sig')))
    hdr,body=rows[0],rows[1:]
    byhash={}
    for r in body:
        m=re.search(r'([0-9a-f]{32})\.',r[8])
        if m: byhash[m.group(1)]=r
    have={r[5] for r in body}
    unc=[];filled=0
    for it in items.values():
        h=it['image'].split('.')[0].lower()
        ti=html.unescape(it['title']).strip(); cp=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',it['caption']+' '+it['content']))).strip()
        if '텍스트를 변경할 수 있습니다' in cp: cp=''
        if ti=='제목': ti=''
        r=byhash.get(h)
        if r is None:
            ok=False
            for ex in (it['image'].split('.')[-1],'JPG','jpg','png'):
                try:
                    b=urllib.request.urlopen(urllib.request.Request(f'https://storage.googleapis.com/cr-resource/image/6e02e7bfd51bb2c8db8e0e209828c836/rty0102/{h}.{ex}',headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
                    s=hashlib.sha1(b).hexdigest()[:12]; r=next((x for x in body if x[5]==s),None); ok=r is not None; break
                except Exception: pass
            if not ok: unc.append(it['image'])
        if r is not None and (ti or cp):
            while len(r)<11: r.append('')
            if not r[9] and ti: r[9]=ti; filled+=1
            if not r[10] and cp: r[10]=cp
    csv.writer(open(d+'/파일명대응표.csv','w',encoding='utf-8-sig',newline='')).writerows([hdr]+body)
    print(n,os.path.basename(d),'json items',len(items),'uncovered',unc,'caption-filled',filled)
for n in map(int,sys.argv[1:]): run(n)
