import requests,json
S=requests.Session(); S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
sl=S.get(B+"/stat/season-list",params={"gcode":"009"},timeout=25).json()["payload"]
print(json.dumps(sl,ensure_ascii=False)[:1200])
for s in sl:
    sc=s["seasonCode"]
    print("== season",sc,s["seasonName"],[l["leagueCode"]+":"+l["leagueName"] for l in s["leagues"]])
    for lc in [l["leagueCode"] for l in s["leagues"]]:
        for g in ["1","2"]:
            sh=S.get(B+"/stat/game-schedule",params={"gcode":"009","seasonCode":sc,"leagueCode":lc,"gender":g,"size":100},timeout=25).json()["payload"]
            c=sh.get("content",[]) if isinstance(sh,dict) else []
            if c: print("  games",lc,g,len(c),c[0]["hname"],c[0]["aname"],c[0]["gdate"],c[0]["hspoint"],c[0]["aspoint"])
    for g in ["1","2"]:
        tr=S.get(B+"/stat/team-records",params={"gcode":"009","seasonCode":sc,"leagueCode":"200","gender":g},timeout=25).json()["payload"]
        print("  team-records",g,len(tr.get("content",[])))
        pr=S.get(B+"/stat/player-records",params={"gcode":"009","seasonCode":sc,"leagueCode":"200","gender":g,"size":300,"page":0},timeout=25).json()["payload"]
        print("  player-records",g,len(pr.get("content",[])))
        rk=S.get(B+"/stat/league/team-rank",params={"gcode":"009","seasonCode":sc,"leagueCode":sh.get("content",[{}])[0].get("leagueCode","201") if sh.get("content") else "201","gender":g},timeout=25).text
        print("  rank",g,rk[:100])
