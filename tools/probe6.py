import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
B="https://user-api.kovo.co.kr"
def g(u,n=300):
    try:
        r=S.get(B+u,timeout=30); t=r.text
        print("==",u,r.status_code,len(t)); print(t[:n].replace("\n"," "))
    except Exception as e: print("==",u,"ERR",str(e)[:120])
for u in ["/stat/season-list","/stat/season-list?gcode=201","/stat/season-list?gcode=200",
          "/stat/season-list?gcode=201&seasonCode=023&gender=1",
          "/players?gender=MALE&initial=ALL","/players?gender=1&initial=ALL","/players?gender=MAN&initial=%EC%A0%84%EC%B2%B4",
          "/players?page=0&size=5&gender=MAN","/players/search?name=%EC%8B%A0%EC%98%81%EC%84%9D",
          "/main/game/season","/main/game/league/team-rank?gender=1&leagueCode=201",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=oa",
          "/stat/cup/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=at",
          "/players/0000872/honor","/players/0000872/rankings","/players/0000872/records"]:
    g(u)
