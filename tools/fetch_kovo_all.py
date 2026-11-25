#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOVO(한국배구연맹) 공식 API 전수 수집기
- user-api.kovo.co.kr 실측 데이터만 사용한다. 추정/가상 값 없음.
- 출력: work_tmp/kovo_v1/data/kovo_raw.json
"""
import json, os, re, sys, time, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUTDIR = os.path.join(HERE, "..", "data")
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

BASE = "https://user-api.kovo.co.kr"
HEADERS = {
    "Accept-Language": "ko-KR",
    "Origin": "https://kovo.co.kr",
    "Referer": "https://kovo.co.kr/",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}
S = requests.Session()
S.headers.update(HEADERS)

V_SEASONS = ["023", "022", "021", "020", "019", "018", "017"]
RPARTS = ["point", "at", "s", "b", "r", "d", "set", "oa", "ta", "ma", "ba", "sa", "csa"]
GENDERS = ["1", "2"]
FAILS = []

def api(path, params=None, timeout=50, retries=4):
    last = None
    for i in range(retries):
        try:
            r = S.get(BASE + path, params=params, timeout=timeout)
            j = r.json()
            res = j.get("result") or {}
            if res.get("status") == 200:
                return j.get("payload")
            last = res.get("message")
            if res.get("status") in (400, 404):
                return None
        except Exception as e:
            last = type(e).__name__ + ":" + str(e)[:80]
        time.sleep(0.7 * (i + 1))
    FAILS.append({"path": path, "params": params, "error": last})
    print("  !! FAIL", path, params, last, file=sys.stderr)
    return None

def fetch_detail(task):
    """경기 박스스코어 상세"""
    g = task
    p = api("/stat/game-schedule/%s" % g["gnum"], {
        "gcode": g.get("gcode") or "001", "seasonCode": g["seasonCode"], "leagueCode": g["leagueCode"],
        "gender": g["gender"], "round": g.get("round") or ""})
    return g, p

def fetch_player(pcode, want_seasons=True):
    d = api("/players/%s" % pcode)
    h = api("/players/%s/history" % pcode)
    o = api("/players/%s/honor" % pcode)
    s = api("/players/%s/season-records" % pcode) if want_seasons else None
    return pcode, {"detail": d, "history": h, "honor": o, "seasonRecords": s}

def main():
    t0 = time.time()
    out = {"meta": {}, "seasonListV": [], "seasonListCup": [], "teams": {}, "v": {}, "cup": {},
           "games": {}, "players": {}, "rosters": {}, "awards": {}, "news": {}, "live": None}

    print("[1] 시즌 목록")
    sl_v = api("/stat/season-list", {"gcode": "001", "seasonCode": "023"}) or []
    sl_cup = api("/stat/season-list", {"gcode": "002"}) or []
    out["seasonListV"] = sl_v
    out["seasonListCup"] = sl_cup
    print("  V-리그 시즌", len(sl_v), "컵대회", len(sl_cup))

    print("[2] 팀 마스터")
    teams_raw = api("/teams") or []
    # V-리그 참가 구단 코드 수집
    team_codes = set()
    for sc in V_SEASONS:
        for g in GENDERS:
            rows = api("/stat/league/team-rank", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or []
            for r in rows:
                team_codes.add(r["tcode"])
    for t in teams_raw:
        if t["code"] in team_codes:
            tr = {}
            for x in (t.get("translations") or []):
                tr[x["languageCode"]] = {"name": x.get("name"), "short": x.get("shortName"),
                                         "middle": x.get("middleName"), "address": x.get("address"),
                                         "description": x.get("description")}
            out["teams"][t["code"]] = {"code": t["code"], "type": t.get("type"), "gender": t.get("gender"),
                                       "emblem": t.get("emblemUrl"), "homepage": t.get("homepageUrl"),
                                       "tel": t.get("tel"), "tr": tr}
    print("  구단", len(out["teams"]))

    print("[3] V-리그 시즌별 기록")
    for sc in V_SEASONS:
        out["v"][sc] = {}
        for g in GENDERS:
            key = "/v/%s/%s" % (sc, g)
            d = {}
            d["standings"] = api("/stat/league/team-rank", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or []
            d["teamRecords"] = api("/stat/team-records", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {}
            d["teamRecordsTotal"] = api("/stat/team-records", {"seasonCode": sc, "leagueCode": "200", "gender": g}) or {}
            pr = api("/stat/player-records", {"seasonCode": sc, "leagueCode": "201", "gender": g, "page": 0, "size": 400}) or {}
            d["playerRecords"] = pr.get("content", []) if isinstance(pr, dict) else []
            d["ranks"] = {}
            for rp in RPARTS:
                rr = api("/stat/league/player-rank", {"seasonCode": sc, "leagueCode": "201", "gender": g,
                                                     "rpart": rp, "size": 100})
                d["ranks"][rp] = rr.get("content", []) if isinstance(rr, dict) else (rr or [])
            sched = api("/stat/game-schedule", {"gcode": "001", "seasonCode": sc, "leagueCode": "201",
                                               "gender": g, "size": 500}) or {}
            d["schedule"] = sched.get("content", []) if isinstance(sched, dict) else []
            d["playoffs"] = {}
            for lc in ("204", "202", "203"):
                sh = api("/stat/game-schedule", {"gcode": "001", "seasonCode": sc, "leagueCode": lc,
                                                "gender": g, "size": 200}) or {}
                d["playoffs"][lc] = sh.get("content", []) if isinstance(sh, dict) else []
            out["v"][sc][g] = d
            print("  %s g%s 순위%d 선수%d 경기%d (PO %s)" % (sc, g, len(d["standings"]), len(d["playerRecords"]),
                  len(d["schedule"]), sum(len(v) for v in d["playoffs"].values())))

    print("[4] KOVO컵 최근 2개 대회")
    for cs in [c for c in sl_cup if c.get("seasonCode")][-2:]:
        sc = cs["seasonCode"]
        out["cup_meta_" + sc] = {"name": cs["seasonName"], "year": cs.get("ryear"), "leagues": cs["leagues"]}
        out["cup"][sc] = {}
        for g in GENDERS:
            d = {"leagues": {}}
            for lg in cs["leagues"]:
                lc = lg["leagueCode"]
                sh = api("/stat/game-schedule", {"gcode": "002", "seasonCode": sc, "leagueCode": lc,
                                                "gender": g, "size": 300}) or {}
                d["leagues"][lc] = {"name": lg["leagueName"],
                                    "games": sh.get("content", []) if isinstance(sh, dict) else []}
            tr = api("/stat/team-records", {"gcode": "002", "seasonCode": sc, "leagueCode": "200", "gender": g}) or {}
            d["teamRecords"] = tr.get("content", []) if isinstance(tr, dict) else []
            pr = api("/stat/player-records", {"gcode": "002", "seasonCode": sc, "leagueCode": "200",
                                             "gender": g, "page": 0, "size": 400}) or {}
            d["playerRecords"] = pr.get("content", []) if isinstance(pr, dict) else []
            out["cup"][sc][g] = d
            print("  컵 %s g%s 경기%d 선수%d" % (sc, g, sum(len(x["games"]) for x in d["leagues"].values()), len(d["playerRecords"])))

    print("[5] 주요 기록 / 수상")
    for sc in ("023", "022", "021"):
        out["awards"][sc] = {}
        for g in GENDERS:
            out["awards"][sc][g] = {
                "mvp": api("/stat/mvp-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or [],
                "triple": api("/stat/triple-crown-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {},
                "achieve": api("/stat/achive-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {},
            }

    print("[6] 로스터")
    for sc in ("023", "022"):
        out["rosters"][sc] = {}
        for tc in sorted(team_codes):
            pl = api("/teams/%s/players" % tc, {"seasonCode": sc})
            if not pl and sc == "023":
                pl = api("/teams/%s/players" % tc)
            out["rosters"][sc][tc] = pl or []
    nro = {sc: sum(len(v) for v in out["rosters"][sc].values()) for sc in out["rosters"]}
    print("  로스터", nro)

    print("[7] 경기 박스스코어 (023 전체 + 022 전체)")
    tasks = []
    for sc in ("023", "022"):
        for g in GENDERS:
            d = out["v"].get(sc, {}).get(g)
            if not d:
                continue
            games = list(d["schedule"])
            for lc, arr in d["playoffs"].items():
                for x in arr:
                    y = dict(x); y.setdefault("leagueCode", lc); games.append(y)
            for x in games:
                if (x.get("hspoint") or 0) + (x.get("aspoint") or 0) <= 0:
                    continue
                y = dict(x); y["gender"] = g; y["gcode"] = "001"
                tasks.append(y)
    print("  대상 경기", len(tasks))
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_detail, t) for t in tasks]
        for f in as_completed(futs):
            g, p = f.result()
            done += 1
            if p and p.get("game"):
                key = "%s-%s-%s-%s" % (g["seasonCode"], g["gender"], g.get("leagueCode"), g["gnum"])
                out["games"][key] = {"game": p.get("game"), "player": p.get("player") or [],
                                     "team": p.get("team") or [], "ranking": p.get("ranking") or {}}
            if done % 40 == 0:
                print("   ...", done, "/", len(tasks))
    print("  박스스코어", len(out["games"]))

    print("[8] 선수 상세")
    pcodes = set()
    for sc in ("023", "022"):
        for g in GENDERS:
            for r in out["v"].get(sc, {}).get(g, {}).get("playerRecords", []):
                if r.get("pcode"):
                    pcodes.add(r["pcode"])
    for sc in out["rosters"]:
        for tc, arr in out["rosters"][sc].items():
            for p in arr:
                if p.get("playerCode"):
                    pcodes.add(p["playerCode"])
    print("  대상 선수", len(pcodes))
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_player, pc) for pc in sorted(pcodes)]
        for f in as_completed(futs):
            pc, d = f.result()
            out["players"][pc] = d
            done += 1
            if done % 60 == 0:
                print("   ...", done, "/", len(pcodes))

    print("[9] 뉴스")
    for kind, path in (("kovo", "/contents/news/kovo/news"), ("press", "/contents/news/kovo/press"),
                       ("notice", "/contents/news/notice")):
        items = []
        for pg in range(2):
            p = api(path, {"page": pg, "size": 20, "sort": "id,desc"}) or {}
            items.extend(p.get("content", []) if isinstance(p, dict) else [])
        out["news"][kind] = items
        print("  ", kind, len(items))

    print("[10] 실시간")
    rt = api("/stat/real-time", timeout=90)
    if isinstance(rt, dict) and isinstance(rt.get("game"), dict):
        gm = rt["game"]
        out["live"] = {"game": gm, "recentGames": rt.get("recentGames") or [], "feed": rt.get("feed") or [],
                       "fetched_at": datetime.datetime.now().isoformat(timespec="seconds")}
    print("  live:", (out["live"] or {}).get("game", {}).get("gameDate"))

    out["meta"] = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": "KOVO 공식 API (user-api.kovo.co.kr)",
        "seasons_v": V_SEASONS,
        "seasons_cup": list(out["cup"].keys()),
        "counts": {
            "seasons": len(V_SEASONS),
            "teams": len(out["teams"]),
            "players": len(out["players"]),
            "games_box": len(out["games"]),
            "news_kovo": len(out["news"].get("kovo", [])),
            "news_press": len(out["news"].get("press", [])),
            "news_notice": len(out["news"].get("notice", [])),
            "player_records": sum(len(out["v"][s][g]["playerRecords"]) for s in out["v"] for g in out["v"][s]),
            "schedule_games": sum(len(out["v"][s][g]["schedule"]) for s in out["v"] for g in out["v"][s]),
        },
        "failures": FAILS,
    }
    path = os.path.join(OUTDIR, "kovo_raw.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)
    print("[DONE]", path, os.path.getsize(path), "bytes", round(time.time() - t0, 1), "s", "fails:", len(FAILS))

if __name__ == "__main__":
    main()
