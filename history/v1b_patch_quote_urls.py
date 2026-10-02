s=open('crawl.py',encoding='utf-8').read()
s=s.replace("""def get(u,tries=3):
    for i in range(tries):""","""def q(u):
    p=urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((p.scheme,p.netloc,urllib.parse.quote(urllib.parse.unquote(p.path),safe='/%'),urllib.parse.quote(p.query,safe='=&%'),''))
def get(u,tries=3):
    u=q(u)
    for i in range(tries):""")
head=s.split("seen={}; queue")[0]
body=open('body.txt',encoding='utf-8').read()
open('crawl2.py','w',encoding='utf-8').write(head+body)
