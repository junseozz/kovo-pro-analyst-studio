import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
r=S.get(B+"/stat/player-records?seasonCode=023&leagueCode=201&gender=1",timeout=40); p=r.json()["payload"]
print("player-records", type(p), p.keys() if isinstance(p,dict) else len(p))
c=p["content"] if isinstance(p,dict) else p
print("count",len(c))
print(json.dumps(c[5],ensure_ascii=False,indent=1)[:2500])
r=S.get(B+"/stat/team-records?seasonCode=023&leagueCode=201&gender=1",timeout=40); p=r.json()["payload"]
print("team fields", list(p["content"][0].keys()))
print(json.dumps(p["content"][0],ensure_ascii=False)[:1500])
print("=== coaches")
for u in ["/teams/coaches?tcode=1006","/teams/coaches?gender=MALE","/teams/coaches?seasonCode=023&tcode=1006"]:
    r=S.get(B+u,timeout=30); print(u,r.text[:300])
print("=== players season param")
r=S.get(B+"/teams/1006/players?seasonCode=022",timeout=30); p=r.json()["payload"]; print(len(p), p[0] if p else None)
r=S.get(B+"/teams/1006/players",timeout=30); p=r.json()["payload"]; print("noparam",len(p))
