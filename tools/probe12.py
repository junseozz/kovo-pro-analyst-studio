import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for q in ["?seasonCode=023&leagueCode=201&gender=1&page=0&size=300","?seasonCode=023&leagueCode=201&gender=1&size=300","?seasonCode=023&leagueCode=201&gender=1&page=1&size=30"]:
    r=S.get(B+"/stat/player-records"+q,timeout=40)
    try:
        p=r.json()["payload"]; print(q,"->",len(p["content"]),p["page"])
    except Exception as e: print(q,r.text[:120])
# game schedule page size
r=S.get(B+"/stat/game-schedule?seasonCode=023&leagueCode=201&gender=1&size=500",timeout=40)
p=r.json()["payload"]; print("games",len(p["content"]),p["page"])
c=p["content"][0]; print(list(c.keys()))
print(json.dumps(c,ensure_ascii=False)[:900])
