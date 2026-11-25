import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
B="https://user-api.kovo.co.kr"
def g(u,n=350):
    try:
        r=S.get(B+u,timeout=30); t=r.text
        print("==",u,r.status_code,len(t)); print(t[:n].replace("\n"," "))
    except Exception as e: print("==",u,"ERR",str(e)[:120])
g("/stat/season-list?gcode=201&seasonCode=023",1200)
g("/players?gender=MAN&initial=ALL",300)
g("/players?gender=MAN",300)
g("/stats/player-records?seasonCode=023&leagueCode=201&gender=1&size=5&page=0",400)
g("/team-vs-records/ranking?seasonCode=023&leagueCode=201&gender=1",300)
g("/stat/game-schedule?seasonCode=023&leagueCode=202&gender=1",400)
g("/teams/coaches?seasonCode=023",300)
g("/teams?tcode=1006",1400)
