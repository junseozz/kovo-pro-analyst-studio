import requests,json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
r=S.get(B+"/stat/real-time",timeout=60); p=r.json()["payload"]
print(type(p), list(p.keys()))
for k,v in p.items():
    print(k, type(v).__name__, len(json.dumps(v,ensure_ascii=False)))
g=p["game"]; print(json.dumps(g,ensure_ascii=False)[:1200])
print("teams?", [x for x in p.keys()])
r=S.get(B+"/teams/1003/players",timeout=30); print("1003 no param", len(r.json()["payload"]))
r=S.get(B+"/teams/2007/players",timeout=30); print("2007 no param", len(r.json()["payload"]))
r=S.get(B+"/contents/news/kovo/news?page=0&size=2&sort=id,desc",timeout=30); it=r.json()["payload"]["content"][0]
print(it["titles"]); print(it.get("thumbnails"))
