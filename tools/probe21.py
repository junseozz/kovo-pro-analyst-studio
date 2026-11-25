import requests,json
S=requests.Session(); S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for gc in ["003","004","005","006","007","008","010","011","012"]:
    r=S.get(B+"/stat/season-list",params={"gcode":gc},timeout=25)
    try:
        p=r.json()["payload"]
        print(gc, "seasons", len(p), [x["seasonName"] for x in p[-2:]] if p else "")
    except Exception as e: print(gc,"ERR",r.text[:80])
