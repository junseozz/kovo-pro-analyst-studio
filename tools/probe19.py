import requests,json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
cup=S.get(B+"/stat/season-list?gcode=002",timeout=30).json()["payload"]
print(len(cup)); print([(c["seasonCode"],c["seasonName"]) for c in cup[-4:]])
last=cup[-1]; sc=last["seasonCode"]; print("leagues",last["leagues"])
for lc in ["211","212","213","214","200"]:
    r=S.get(B+"/stat/team-records",params={"gcode":"002","seasonCode":sc,"leagueCode":lc,"gender":"1"},timeout=30)
    p=r.json()["payload"]; c=p.get("content",[])
    print(lc,len(c),c[0]["tsname"] if c else None)
r=S.get(B+"/stat/game-schedule",params={"gcode":"002","seasonCode":sc,"leagueCode":"212","gender":"1"},timeout=30)
p=r.json()["payload"]; print("games",len(p["content"]), p["content"][0]["leagueName"] if p["content"] else None)
print([ (c["seasonCode"],c["seasonName"]) for c in cup if c["ryear"] and c["ryear"].startswith("2025")])
