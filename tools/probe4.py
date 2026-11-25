import requests, json
S=requests.Session()
S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
B="https://user-api.kovo.co.kr"
def g(u):
    try:
        r=S.get(B+u,timeout=30); t=r.text
        print("==",u,r.status_code,len(t)); print(t[:350].replace("\n"," "))
    except Exception as e: print("==",u,"ERR",str(e)[:120])
for u in ["/stat/season-list?leagueCode=201&gender=1",
          "/teams/coaches",
          "/teams?tcode=1006",
          "/players?initial=ALL&gender=1",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=point",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=b",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=s",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=rd",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=set",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=d",
          "/stat/league/player-rank?seasonCode=023&leagueCode=201&gender=1&rpart=r",
          "/stat/game-schedule?seasonCode=023&leagueCode=203&gender=1",
          "/stat/mvp-list?seasonCode=022&leagueCode=201&gender=1",
          ]:
    g(u)
