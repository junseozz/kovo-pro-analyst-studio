import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for sc in ["022","023"]:
  for lc in ["205","206","207","208","210"]:
    r=S.get(f"{B}/stat/team-records?seasonCode={sc}&leagueCode={lc}&gender=1",timeout=30)
    p=r.json()["payload"]; c=p.get("content",[]) if isinstance(p,dict) else []
    print(sc,lc,"team-records",len(c), (c[0].get("leagueName") if c else None))
print("---- cup rank")
for sc in ["021","022","023"]:
  for g in ["1","2"]:
    r=S.get(f"{B}/stat/cup/team-rank?seasonCode={sc}&leagueCode=201&gender={g}",timeout=30)
    p=r.json()["payload"]; print(sc,g,type(p).__name__, (len(p.get("content",[])) if isinstance(p,dict) else len(p)))
print("---- games cup?")
for sc in ["022","023"]:
  for lc in ["205","206","207"]:
    r=S.get(f"{B}/stat/game-schedule?seasonCode={sc}&leagueCode={lc}&gender=1",timeout=40)
    p=r.json()["payload"]; c=p.get("content",[])
    print(sc,lc,len(c),(c[0].get("leagueName") if c else None),(c[0].get("gdate") if c else None))
