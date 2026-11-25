import requests,json
S=requests.Session(); S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
for gc in ["009","013","014","015","016","020","100","101","102","103","104","105","106","107","108","109","110","111","112"]:
    r=S.get(B+"/stat/season-list",params={"gcode":gc},timeout=20)
    p=r.json().get("payload") or []
    if p: print(gc, len(p), [x["seasonName"] for x in p[-3:]])
print("=== menus")
r=S.get(B+"/menus",timeout=30); print(r.status_code, len(r.text))
t=r.text
for kw in ["퓨처스","FUTURES"]:
    i=t.find(kw); print(kw, i, t[max(0,i-200):i+200] if i>0 else "")
