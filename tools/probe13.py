import requests
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
def t(u,n=200,extra=None):
    try:
        r=requests.get(u,headers={**H,**(extra or {})},timeout=20)
        print("==",u,r.status_code,len(r.text)); print(r.text[:n].replace("\n"," "))
    except Exception as e: print("==",u,"ERR",type(e).__name__,str(e)[:100])
t("https://api-gw.sports.naver.com/volleyball/schedule?category=volleyball&year=2026&month=11")
t("https://api-gw.sports.naver.com/volleyball/teams?category=volleyball")
t("https://m.sports.naver.com/volleyball/index")
t("https://www.fivb.com/en/volleyball/calendar")
t("https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/schedule/")
