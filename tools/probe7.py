import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for lc in ["200","201","202","203","204"]:
    r=S.get(f"{B}/stat/team-records?seasonCode=022&leagueCode={lc}&gender=1",timeout=30)
    try:
        p=r.json()["payload"]; c=p.get("content",[])
        print(lc, "team-records", len(c), (c[0].get("leagueName") if c else None), (c[0].get("seasonName") if c else None))
    except Exception as e: print(lc,"ERR",r.text[:80])
for lc in ["200","201","202","203"]:
    r=S.get(f"{B}/stat/game-schedule?seasonCode=022&leagueCode={lc}&gender=1",timeout=40)
    try:
        p=r.json()["payload"]; c=p.get("content",[])
        print(lc,"games",len(c), (c[0].get("leagueName") if c else None))
    except Exception as e: print(lc,"ERR",r.text[:80])
for sc in ["001","010","015","018","019","020","021","022","023"]:
    r=S.get(f"{B}/stat/league/team-rank?seasonCode={sc}&leagueCode=201&gender=1",timeout=30)
    p=r.json()["payload"]
    print("season",sc,len(p), p[0]["tsname"] if p else None, p[0]["udate"] if p else None)
