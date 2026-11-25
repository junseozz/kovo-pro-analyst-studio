import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
def g(u,n=500):
    r=S.get(B+u,timeout=40); print("==",u,r.status_code,len(r.text)); print(r.text[:n].replace("\n"," "))
g("/stat/season-list?gcode=001&seasonCode=023",1500)
g("/stat/team-records?gcode=002&seasonCode=023&leagueCode=212&gender=1",400)
g("/stat/game-schedule?gcode=002&seasonCode=023&leagueCode=212&gender=1",400)
g("/stat/game-schedule?gcode=002&seasonCode=022&leagueCode=212&gender=1",300)
g("/stat/season-list?gcode=002",1500)
