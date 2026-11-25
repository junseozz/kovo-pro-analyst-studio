import requests,re
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept-Language":"ko-KR,ko;q=0.9"}
def t(u,n=400,h=None):
    try:
        r=requests.get(u,headers={**H,**(h or {})},timeout=25)
        print("==",u,r.status_code,len(r.text)); print(r.text[:n].replace("\n"," "))
        return r
    except Exception as e: print("==",u,"ERR",type(e).__name__,str(e)[:100])
t("https://news.google.com/rss/search?q=%ED%94%84%EB%A1%9C%EB%B0%B0%EA%B5%AC&hl=ko&gl=KR&ceid=KR:ko",600)
t("https://sports.news.naver.com/volleyball/index",300)
t("https://api.sports.naver.com/volleyball/news?page=1&size=10",300)
t("https://www.volleyballworld.com/volleyball/competitions/volleyball-nations-league/schedule/",200)
