#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KOVO 퓨처스 챔프전(gcode=009) 전수 수집 → data/kovo_raw.json 의 'futures' 병합."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "data", "kovo_raw.json")
BASE = "https://user-api.kovo.co.kr"
S = requests.Session()
S.headers.update({"Accept-Language": "ko-KR", "Origin": "https://kovo.co.kr", "Referer": "https://kovo.co.kr/",
                  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
GC = "009"

def api(path, params=None, retries=3):
    for i in range(retries):
        try:
            j = S.get(BASE + path, params=params, timeout=45).json()
            if (j.get("result") or {}).get("status") == 200:
                return j.get("payload")
        except Exception:
            pass
        time.sleep(0.6)
    return None

def detail(g):
    return g, api("/stat/game-schedule/%s" % g["gnum"], {
        "gcode": GC, "seasonCode": g["seasonCode"], "leagueCode": g["leagueCode"],
        "gender": g["gender"], "round": g.get("round") or ""})

def main():
    d = json.load(open(PATH, encoding="utf-8"))
    sl = api("/stat/season-list", {"gcode": GC}) or []
    d["futuresSeasons"] = sl
    fut = {}
    tasks = []
    for s in sl:
        sc = s["seasonCode"]
        fut[sc] = {"name": s["seasonName"], "year": s.get("ryear"), "leagues": s["leagues"], "g": {}}
        for g in ("1", "2"):
            dd = {"leagues": {}, "teamRecords": {}, "playerRecords": {}}
            for lg in s["leagues"]:
                sh = api("/stat/game-schedule", {"gcode": GC, "seasonCode": sc, "leagueCode": lg["leagueCode"],
                                                "gender": g, "size": 100}) or {}
                games = sh.get("content", []) if isinstance(sh, dict) else []
                dd["leagues"][lg["leagueCode"]] = {"name": lg["leagueName"], "games": games}
                for x in games:
                    y = dict(x); y["gender"] = g; y["gcode"] = GC
                    tasks.append(y)
            for lc in ("200", "212", "213", "214"):
                tr = api("/stat/team-records", {"gcode": GC, "seasonCode": sc, "leagueCode": lc, "gender": g}) or {}
                dd["teamRecords"][lc] = tr.get("content", []) if isinstance(tr, dict) else []
                pr = api("/stat/player-records", {"gcode": GC, "seasonCode": sc, "leagueCode": lc,
                                                 "gender": g, "size": 300, "page": 0}) or {}
                dd["playerRecords"][lc] = pr.get("content", []) if isinstance(pr, dict) else []
            fut[sc]["g"][g] = dd
            print(sc, g, {k: len(v["games"]) for k, v in dd["leagues"].items()},
                  "tr200", len(dd["teamRecords"]["200"]), "pr200", len(dd["playerRecords"]["200"]))
    d["futures"] = fut

    print("boxscores", len(tasks))
    box = d.setdefault("futuresGames", {})
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for f in as_completed([ex.submit(detail, t) for t in tasks]):
            g, p = f.result(); done += 1
            if p and p.get("game"):
                key = "%s-%s-%s-%s" % (g["seasonCode"], g["gender"], g["leagueCode"], g["gnum"])
                box[key] = {"game": p.get("game"), "player": p.get("player") or [], "team": p.get("team") or []}
    print("saved", len(box))

    # 퓨처스 참가팀(실업팀 포함) 이름 정리
    names = {}
    for sc, s in fut.items():
        for g, dd in s["g"].items():
            for lc, blk in dd["leagues"].items():
                for x in blk["games"]:
                    names[x["hcode"]] = (x["hname"], x.get("homeEmblemUrl"))
                    names[x["acode"]] = (x["aname"], x.get("awayEmblemUrl"))
    d["futuresTeams"] = {k: {"name": v[0], "emblem": v[1]} for k, v in names.items()}
    json.dump(d, open(PATH + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(PATH + ".tmp", PATH)
    print("futures teams", len(names), "size", os.path.getsize(PATH))

if __name__ == "__main__":
    main()
