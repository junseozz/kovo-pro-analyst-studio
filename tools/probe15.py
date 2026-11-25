import requests,json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
r=S.get(B+"/teams?gender=MALE",timeout=30); p=r.json()["payload"]
print(len(p)); print(list(p[0].keys())); print(json.dumps(p[0],ensure_ascii=False)[:800])
r=S.get(B+"/teams?gender=WOMAN",timeout=30); p2=r.json()["payload"]; print("women",len(p2),[x.get("code") for x in p2])
print("teams all", len(S.get(B+"/teams",timeout=30).json()["payload"]))
