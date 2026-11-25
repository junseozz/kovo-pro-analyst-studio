import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for lc in ["212","213","214"]:
  for sc in ["022","023"]:
    r=S.get(f"{B}/stat/team-records?seasonCode={sc}&leagueCode={lc}&gender=1",timeout=30)
    p=r.json()["payload"]; c=p.get("content",[]) if isinstance(p,dict) else []
    print(sc,lc,len(c), (c[0].get("leagueName") if c else None),(c[0].get("seasonName") if c else None))
r=S.get(f"{B}/stats/teams?teamType=MEN&page=0&size=30&leagueCode=201&seasonCode=023",timeout=30)
print("stats/teams",r.status_code,r.text[:300])
r=S.get(f"{B}/stat/game-schedule?seasonCode=023&leagueCode=212&gender=1",timeout=40)
p=r.json()["payload"]; print("games212",len(p.get("content",[])), p["content"][0]["leagueName"] if p.get("content") else None)
