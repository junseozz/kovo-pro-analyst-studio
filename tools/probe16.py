import requests,json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
pos=set()
for t in ["1001","1002","1003","1004","1005","1006","1008","1009","2001","2002","2003","2004","2005","2006","2007","2008"]:
    r=S.get(f"{B}/teams/{t}/players?seasonCode=023",timeout=30); p=r.json()["payload"]
    print(t,len(p),[x["name"]+":"+str(x["position"]) for x in p][:3])
    for x in p: pos.add(x["position"])
print("positions",pos)
r=S.get(B+"/teams/1001/players?seasonCode=023",timeout=30); print(json.dumps(r.json()["payload"][0],ensure_ascii=False))
