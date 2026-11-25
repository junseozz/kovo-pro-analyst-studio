import requests,json,re
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
r=S.get(B+"/contents/news/kovo/news?page=0&size=6&sort=id,desc",timeout=30)
p=r.json()["payload"]; c=p["content"]
print("keys",list(c[0].keys()))
for it in c:
    body=it["bodies"][0]["body"] if it.get("bodies") else ""
    txt=re.sub('<[^>]+>','',body)[:120].replace("\n"," ")
    print(it["id"], it["createdAt"][:10], len(body), txt)
print("total", p["page"])
for path in ["/contents/news/kovo/press","/contents/news/notice"]:
    r=S.get(B+path+"?page=0&size=4&sort=id,desc",timeout=30); p=r.json()["payload"]
    print(path, p["page"] if isinstance(p,dict) else "list")
    for it in (p["content"] if isinstance(p,dict) else p)[:3]:
        b=it.get("bodies",[{}])[0].get("body","")
        print("  ",it["id"],it["createdAt"][:10], re.sub('<[^>]+>','',b)[:80].replace("\n"," "))
