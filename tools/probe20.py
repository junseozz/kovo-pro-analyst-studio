import requests,re,json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
u="https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/schedule/"
r=requests.get(u,headers=H,timeout=30); t=r.text
print(r.status_code,len(t))
for kw in ["__NEXT_DATA__","Korea","api.volleyballworld","application/json"]:
    print(kw, t.count(kw))
m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.{0,300})',t)
print(m.group(1)[:300] if m else "no next data")
i=t.find("Korea"); print(t[max(0,i-300):i+300] if i>0 else "no korea")
# try api
for api in ["https://api.volleyballworld.com/api/v1/competitions","https://en.volleyballworld.com/api/schedule"]:
    try:
        rr=requests.get(api,headers=H,timeout=15); print(api,rr.status_code,rr.text[:150])
    except Exception as e: print(api,"ERR",str(e)[:80])
