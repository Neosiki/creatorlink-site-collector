import csv,re,os,sys,glob,hashlib,urllib.request,collections
from PIL import Image
R=os.path.expanduser('~/mnt/01.컨설팅 업무/02.카페보리_경북청도/류태열_온라인도록_자료수집')
d=glob.glob(f'{R}/{int(sys.argv[1]):02d}_*')[0]; os.chdir(d); print(d.split('/')[-1])
rows=list(csv.reader(open('파일명대응표.csv',encoding='utf-8-sig')))[1:]
files=sorted(os.listdir('이미지')); bad=0
for f in files:
    try: Image.open('이미지/'+f).verify()
    except: bad+=1
ws=[int(r[2]) for r in rows if r[2]]
print('rows',len(rows),'files',len(files),'bad',bad,'w',min(ws) if ws else '-',max(ws) if ws else '-','MB',round(sum(int(r[4]) for r in rows)/1e6,1))
print('caps',collections.Counter((r[9],r[10]) for r in rows if r[10]).most_common(6))
t=open('원본페이지.html',encoding='utf-8').read()
th=list(dict.fromkeys(h.lower() for h in re.findall(r'src="/\d+/([0-9a-f]{32})\.\w+"',t)))
have={r[5]:r[1] for r in rows}; got={}
for r in rows:
    m=re.search(r'([0-9a-f]{32})\.',r[8])
    if m: got[m.group(1)]=1
miss=[h for h in th if h not in got]; stillmiss=[]
for h in miss:
    ok=False
    for ex in ('JPG','jpg','png'):
        try:
            b=urllib.request.urlopen(urllib.request.Request(f'https://storage.googleapis.com/cr-resource/image/6e02e7bfd51bb2c8db8e0e209828c836/rty0102/{h}.{ex}',headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read()
            ok=hashlib.sha1(b).hexdigest()[:12] in have; break
        except Exception: pass
    if not ok: stillmiss.append(h)
seqs=set(re.findall(r'/view/(\d+)',t)); hv=len(os.listdir('상세페이지'))
print('thumbs',len(th),'direct-covered',len(th)-len(miss),'dup-covered',len(miss)-len(stillmiss),'UNCOVERED',stillmiss)
print('detail links',len(seqs),'ok',hv,'dead',len(seqs)-hv)
v='영상/영상목록.csv'
print('videos',open(v,encoding='utf-8-sig').read().strip().split('\n')[1:] if os.path.exists(v) else 0)
print(open('수집완료.txt',encoding='utf-8').read().split('\n')[4:6])
if os.path.exists('목록데이터.json'):
    J=json.load(open('목록데이터.json',encoding='utf-8')) if False else __import__('json').load(open('목록데이터.json',encoding='utf-8'))
    hs=set()
    for r in rows:
        m=re.search(r'([0-9a-f]{32})\.',r[8])
        if m: hs.add(m.group(1))
    api=J['items']; imgs=set(i['image'].split('.')[0].lower() for i in api)
    print('API 작품',len(api),'고유이미지',len(imgs),'CSV미포함(내용중복 제외분)',len(imgs-hs),'목록별(got/total)',[(m['got'],m['total']) for m in J['meta'].values()])
