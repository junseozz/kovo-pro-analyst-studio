import requests,json
S=requests.Session(); S.headers.update({"Accept-Language":"ko-KR","Origin":"https://kovo.co.kr","Referer":"https://kovo.co.kr/","User-Agent":"Mozilla/5.0 Chrome/120"})
B="https://user-api.kovo.co.kr"
d=json.load(open("../data/kovo_raw.json",encoding="utf-8"))
g=d["v"]["023"]["1"]["schedule"][0]
print({k:g.get(k) for k in ["gnum","seasonCode","leagueCode","round","hcode","acode","gdate","hspoint","aspoint"]})
for params in [{"gcode":"001","seasonCode":"023","leagueCode":"201","gender":"1","round":"1","tcode":"1001","acode":"1005","gdate":"2026-10-31"},
               {"seasonCode":"023","leagueCode":"201","gender":"1","round":"1"},
               {"gcode":"001","seasonCode":"023","leagueCode":"201","gender":"1","round":"1"}]:
    r=S.get(B+"/stat/game-schedule/1",params=params,timeout=40)
    j=r.json(); print(params, j["result"], type(j["payload"]))
    if isinstance(j["payload"],dict): print(list(j["payload"].keys()))
    else: print(str(j["payload"])[:200])
