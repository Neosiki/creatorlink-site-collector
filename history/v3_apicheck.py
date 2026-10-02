import sys,os,glob,csv,re,json
sys.argv=['x']; import menu
R=menu.ROOT
for n in range(1,14):
    d=glob.glob(f'{R}/{n:02d}_*')[0]
    t=open(d+'/원본페이지.html',encoding='utf-8').read()
    it,meta=menu.api_items(t)
    rows=list(csv.reader(open(d+'/파일명대응표.csv',encoding='utf-8-sig')))[1:]
    hs=set()
    for r in rows:
        m=re.search(r'([0-9a-f]{32})\.',r[8])
        if m: hs.add(m.group(1))
    miss=[i for i in it if i['image'].split('.')[0].lower() not in hs]
    print(n,os.path.basename(d),'api items',len(it),'meta',[(m['got'],m['total']) for m in meta.values()],'saved',len(rows),'not-in-csv',len(miss))
