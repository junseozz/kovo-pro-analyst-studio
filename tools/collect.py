#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOVO 공식 API 전수 수집기 v2 (재개 가능·캐시 기반)
- user-api.kovo.co.kr 실측 데이터만 사용. 추정/합성 없음.
- 원본은 tools/cache/ 아래에 단위별 JSON 으로 저장하고, 마지막에 kovo_raw.json 으로 병합.
사용: python3 tools/collect.py [seasons|cup|futures|rosters|players|boxes|news|merge|all]
"""
import json, os, sys, time, datetime, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(HERE, "..", "data")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

BASE = "https://user-api.kovo.co.kr"
HEADERS = {
    "Accept-Language": "ko-KR", "Origin": "https://kovo.co.kr", "Referer": "https://kovo.co.kr/",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}
FAILS = []
T0 = time.time()
NREQ = [0]


def sess():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


S = sess()


def api(path, params=None, timeout=40, retries=4, quiet=False):
    last = None
    for i in range(retries):
        try:
            NREQ[0] += 1
            r = S.get(BASE + path, params=params, timeout=timeout)
            j = r.json()
            res = j.get("result") or {}
            if res.get("status") == 200:
                return j.get("payload")
            last = "%s %s" % (res.get("status"), res.get("message"))
            if res.get("status") in (400, 404):
                return None
        except Exception as e:
            last = type(e).__name__ + ":" + str(e)[:70]
        time.sleep(0.5 * (i + 1))
    if not quiet:
        FAILS.append({"path": path, "params": params, "error": last})
        print("  !! FAIL", path, params, last, file=sys.stderr)
    return None


def cpath(name):
    return os.path.join(CACHE, name + ".json")


def cached(name, fn, force=False):
    p = cpath(name)
    if not force and os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    v = fn()
    tmp = p + ".tmp"
    json.dump(v, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, p)
    return v


def season_lists():
    sl_v = cached("seasonListV", lambda: api("/stat/season-list", {"gcode": "001", "seasonCode": "023"}) or [], True)
    sl_cup = cached("seasonListCup", lambda: api("/stat/season-list", {"gcode": "002"}) or [], True)
    sl_fut = cached("seasonListFut", lambda: api("/stat/season-list", {"gcode": "009"}) or [], True)
    teams = cached("teams_master", lambda: api("/teams") or [], True)
    return sl_v, sl_cup, sl_fut, teams


RPARTS = ["point", "at", "s", "b", "r", "d", "set", "oa", "ta", "ma", "ba", "sa", "csa"]


def collect_season(sc, g):
    """V-리그 한 시즌/성별 단위"""
    name = "v_%s_%s" % (sc, g)

    def work():
        d = {}
        d["standings"] = api("/stat/league/team-rank", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or []
        d["teamRecords"] = api("/stat/team-records", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {}
        d["teamRecordsTotal"] = api("/stat/team-records", {"seasonCode": sc, "leagueCode": "200", "gender": g}) or {}
        pr = api("/stat/player-records", {"seasonCode": sc, "leagueCode": "201", "gender": g, "page": 0, "size": 400}) or {}
        d["playerRecords"] = pr.get("content", []) if isinstance(pr, dict) else []
        d["ranks"] = {}
        for rp in RPARTS:
            rr = api("/stat/league/player-rank", {"seasonCode": sc, "leagueCode": "201", "gender": g, "rpart": rp, "size": 100})
            d["ranks"][rp] = rr.get("content", []) if isinstance(rr, dict) else (rr or [])
        sched = api("/stat/game-schedule", {"gcode": "001", "seasonCode": sc, "leagueCode": "201", "gender": g, "size": 500}) or {}
        d["schedule"] = sched.get("content", []) if isinstance(sched, dict) else []
        d["playoffs"] = {}
        for lc in ("204", "202", "203"):
            sh = api("/stat/game-schedule", {"gcode": "001", "seasonCode": sc, "leagueCode": lc, "gender": g, "size": 200}) or {}
            d["playoffs"][lc] = sh.get("content", []) if isinstance(sh, dict) else []
        d["awards"] = {
            "mvp": api("/stat/mvp-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or [],
            "triple": api("/stat/triple-crown-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {},
            "achieve": api("/stat/achive-list", {"seasonCode": sc, "leagueCode": "201", "gender": g}) or {},
        }
        # 로스터 (해당 시즌 참가 구단)
        codes = sorted({r.get("tcode") for r in d["standings"] if r.get("tcode")})
        ros = {}
        for tc in codes:
            pl = api("/teams/%s/players" % tc, {"seasonCode": sc}, quiet=True)
            ros[tc] = pl or []
        d["rosters"] = ros
        return d

    return name, cached(name, work)


def collect_cup(sc, g, leagues):
    name = "cup_%s_%s" % (sc, g)

    def work():
        d = {"leagues": {}, "teamRecords": {}, "playerRecords": {}}
        for lg in leagues:
            lc = lg["leagueCode"]
            sh = api("/stat/game-schedule", {"gcode": "002", "seasonCode": sc, "leagueCode": lc, "gender": g, "size": 300}) or {}
            d["leagues"][lc] = {"name": lg.get("leagueName"), "games": sh.get("content", []) if isinstance(sh, dict) else []}
        for lc in {"200", "201", "211", "212", "213", "214"} | {x["leagueCode"] for x in leagues}:
            tr = api("/stat/team-records", {"gcode": "002", "seasonCode": sc, "leagueCode": lc, "gender": g}, quiet=True) or {}
            d["teamRecords"][lc] = tr.get("content", []) if isinstance(tr, dict) else []
            pr = api("/stat/player-records", {"gcode": "002", "seasonCode": sc, "leagueCode": lc, "gender": g,
                                              "page": 0, "size": 400}, quiet=True) or {}
            d["playerRecords"][lc] = pr.get("content", []) if isinstance(pr, dict) else []
        codes = set()
        for lc, blk in d["leagues"].items():
            for x in blk["games"]:
                codes.add(x["hcode"]); codes.add(x["acode"])
        ros = {}
        for tc in sorted(codes):
            pl = api("/teams/%s/players" % tc, {"seasonCode": sc}, quiet=True)
            ros[tc] = pl or []
        d["rosters"] = ros
        return d

    return name, cached(name, work)


def collect_fut(sc, g, leagues):
    name = "fut_%s_%s" % (sc, g)

    def work():
        d = {"leagues": {}, "teamRecords": {}, "playerRecords": {}}
        for lg in leagues:
            lc = lg["leagueCode"]
            sh = api("/stat/game-schedule", {"gcode": "009", "seasonCode": sc, "leagueCode": lc, "gender": g, "size": 200}) or {}
            d["leagues"][lc] = {"name": lg.get("leagueName"), "games": sh.get("content", []) if isinstance(sh, dict) else []}
        for lc in ("200", "212", "213", "214"):
            tr = api("/stat/team-records", {"gcode": "009", "seasonCode": sc, "leagueCode": lc, "gender": g}, quiet=True) or {}
            d["teamRecords"][lc] = tr.get("content", []) if isinstance(tr, dict) else []
            pr = api("/stat/player-records", {"gcode": "009", "seasonCode": sc, "leagueCode": lc, "gender": g,
                                              "page": 0, "size": 300}, quiet=True) or {}
            d["playerRecords"][lc] = pr.get("content", []) if isinstance(pr, dict) else []
        codes = set()
        for lc, blk in d["leagues"].items():
            for x in blk["games"]:
                codes.add(x["hcode"]); codes.add(x["acode"])
        ros = {}
        for tc in sorted(codes):
            pl = api("/teams/%s/players" % tc, {"seasonCode": sc}, quiet=True)
            ros[tc] = pl or []
        d["rosters"] = ros
        return d

    return name, cached(name, work)


def collect_special(gc, sc, g, leagues):
    name = "sp_%s_%s_%s" % (gc, sc, g)

    def work():
        d = {"leagues": {}, "teamRecords": {}, "playerRecords": {}}
        for lg in leagues:
            lc = lg["leagueCode"]
            sh = api("/stat/game-schedule", {"gcode": gc, "seasonCode": sc, "leagueCode": lc, "gender": g, "size": 200}, quiet=True) or {}
            d["leagues"][lc] = {"name": lg.get("leagueName"), "games": sh.get("content", []) if isinstance(sh, dict) else []}
        for lc in {"200", "211", "902", "791", "793", "904"} | {x["leagueCode"] for x in leagues}:
            tr = api("/stat/team-records", {"gcode": gc, "seasonCode": sc, "leagueCode": lc, "gender": g}, quiet=True) or {}
            d["teamRecords"][lc] = tr.get("content", []) if isinstance(tr, dict) else []
            pr = api("/stat/player-records", {"gcode": gc, "seasonCode": sc, "leagueCode": lc, "gender": g, "page": 0, "size": 300}, quiet=True) or {}
            d["playerRecords"][lc] = pr.get("content", []) if isinstance(pr, dict) else []
        return d

    return name, cached(name, work)


def collect_players(pcodes, workers=8):
    todo = [p for p in pcodes if not os.path.exists(cpath("p_" + p))]
    print("  선수 상세 대상", len(pcodes), "신규", len(todo))
    if not todo:
        return

    def one(pc):
        d = api("/players/%s" % pc, quiet=True)
        h = api("/players/%s/history" % pc, quiet=True)
        o = api("/players/%s/honor" % pc, quiet=True)
        s = api("/players/%s/season-records" % pc, quiet=True)
        return pc, {"detail": d, "history": h, "honor": o, "seasonRecords": s}

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, pc) for pc in todo]
        for f in as_completed(futs):
            pc, d = f.result()
            p = cpath("p_" + pc)
            json.dump(d, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
            os.replace(p + ".tmp", p)
            done += 1
            if done % 100 == 0:
                print("   players", done, "/", len(todo), round(time.time() - T0, 1), "s")


def box_task(task):
    g = task
    p = api("/stat/game-schedule/%s" % g["gnum"], {
        "gcode": g.get("gcode") or "001", "seasonCode": g["seasonCode"], "leagueCode": g["leagueCode"],
        "gender": g["gender"], "round": g.get("round") or ""}, quiet=True)
    return g, p


def collect_boxes(games, name, workers=8):
    """games: list of schedule rows (완료 경기). 저장: cache/box_{name}.json"""
    p = cpath("box_" + name)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    out = {}
    if not games:
        json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        return out

    def one(g):
        pp = api("/stat/game-schedule/%s" % g["gnum"], {
            "gcode": g.get("gcode") or "001", "seasonCode": g["seasonCode"], "leagueCode": g["leagueCode"],
            "gender": g["gender"], "round": g.get("round") or ""}, quiet=True)
        return g, pp

    done = 0
    lock = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, g) for g in games]
        for f in as_completed(futs):
            g, pp = f.result()
            done += 1
            if pp and pp.get("game"):
                key = "%s-%s-%s-%s" % (g["seasonCode"], g.get("gender"), g.get("leagueCode"), g["gnum"])
                out[key] = {"game": pp.get("game"), "player": pp.get("player") or [],
                            "team": pp.get("team") or [], "ranking": pp.get("ranking") or {}}
            if done % 100 == 0:
                print("   box", name, done, "/", len(games), round(time.time() - T0, 1), "s")
    json.dump(out, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(p + ".tmp", p)
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[2:]  # optional season filters
    sl_v, sl_cup, sl_fut, teams_master = season_lists()
    V = [s["seasonCode"] for s in sl_v if s.get("seasonCode")]
    CUP = [s for s in sl_cup if s.get("seasonCode")]
    FUT = [s for s in sl_fut if s.get("seasonCode")]
    if only:
        V = [x for x in V if x in only]
    print("V seasons", len(V), "cup", len(CUP), "fut", len(FUT), "teams", len(teams_master))

    if cmd in ("seasons", "all"):
        print("[seasons]")
        jobs = [(sc, g) for sc in sorted(V, reverse=True) for g in ("1", "2")]
        with ThreadPoolExecutor(max_workers=6) as ex:
            for name, d in ex.map(lambda a: collect_season(*a), jobs):
                print("  ", name, "rank", len(d.get("standings") or []), "pr", len(d.get("playerRecords") or []),
                      "sch", len(d.get("schedule") or []), "N", NREQ[0], round(time.time() - T0, 1), "s")

    if cmd in ("cup", "all"):
        print("[cup]")
        jobs = [(cs["seasonCode"], g, cs.get("leagues") or []) for cs in CUP for g in ("1", "2")]
        with ThreadPoolExecutor(max_workers=6) as ex:
            for name, d in ex.map(lambda a: collect_cup(*a), jobs):
                print("  ", name, round(time.time() - T0, 1), "s")

    if cmd in ("futures", "all"):
        print("[futures]")
        jobs = [(fs["seasonCode"], g, fs.get("leagues") or []) for fs in FUT for g in ("1", "2")]
        with ThreadPoolExecutor(max_workers=4) as ex:
            for name, d in ex.map(lambda a: collect_fut(*a), jobs):
                print("  ", name, round(time.time() - T0, 1), "s")

    if cmd in ("special", "all"):
        print("[special]")
        SPEC = {}
        for gc in ("003", "004", "005", "006", "007", "008"):
            SPEC[gc] = api("/stat/season-list", {"gcode": gc}) or []
        json.dump(SPEC, open(cpath("specialSeasons"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        jobs = []
        for gc, sl in SPEC.items():
            for s in sl:
                for g in ("1", "2"):
                    jobs.append((gc, s["seasonCode"], g, s.get("leagues") or []))
        with ThreadPoolExecutor(max_workers=4) as ex:
            for name, d in ex.map(lambda a: collect_special(*a), jobs):
                print("  ", name, round(time.time() - T0, 1), "s")

    if cmd in ("players", "all"):
        print("[players]")
        pcs = set()
        for fn in sorted(os.listdir(CACHE)):
            if not fn.startswith(("v_", "cup_", "fut_", "sp_")):
                continue
            d = json.load(open(os.path.join(CACHE, fn), encoding="utf-8"))
            if isinstance(d.get("playerRecords"), list):
                for r in d["playerRecords"]:
                    if r.get("pcode"):
                        pcs.add(str(r["pcode"]))
                    if r.get("playerCode"):
                        pcs.add(str(r["playerCode"]))
            elif isinstance(d.get("playerRecords"), dict):
                for arr in d["playerRecords"].values():
                    for r in arr:
                        if r.get("pcode"):
                            pcs.add(str(r["pcode"]))
                        if r.get("playerCode"):
                            pcs.add(str(r["playerCode"]))
            for tc, arr in (d.get("rosters") or {}).items():
                for x in arr:
                    code = x.get("playerCode") or x.get("pcode")
                    if code:
                        pcs.add(str(code))
        print("  전체 선수 코드", len(pcs))
        json.dump(sorted(pcs), open(cpath("pcodes"), "w", encoding="utf-8"))
        collect_players(sorted(pcs))

    if cmd in ("boxes", "all"):
        print("[boxes]")
        units = []
        for fn in sorted(os.listdir(CACHE)):
            if not fn.endswith(".json") or not fn.startswith(("v_", "cup_", "fut_", "sp_")):
                continue
            base = fn[:-5]
            parts = base.split("_")
            src = parts[0]
            if only and len(parts) > 1 and parts[1] not in only:
                continue
            d = json.load(open(os.path.join(CACHE, fn), encoding="utf-8"))
            games = []
            gcode = ({"v": "001", "cup": "002", "fut": "009"}.get(src) or (parts[1] if src == "sp" else "001"))
            if src == "v":
                rows = list(d.get("schedule") or [])
                for lc, arr in (d.get("playoffs") or {}).items():
                    for x in arr:
                        y = dict(x); y.setdefault("leagueCode", lc); rows.append(y)
                for x in rows:
                    if (x.get("hspoint") or 0) + (x.get("aspoint") or 0) <= 0:
                        continue
                    y = {k: x.get(k) for k in ("gnum", "seasonCode", "leagueCode", "gender", "round")}
                    y["gcode"] = gcode
                    games.append(y)
            else:
                for lc, blk in (d.get("leagues") or {}).items():
                    for x in blk.get("games") or []:
                        if (x.get("hspoint") or 0) + (x.get("aspoint") or 0) <= 0:
                            continue
                        y = {k: x.get(k) for k in ("gnum", "seasonCode", "leagueCode", "gender", "round")}
                        y["gcode"] = gcode
                        games.append(y)
            if games:
                units.append((base, games))
        print("  box 단위", len(units), "경기", sum(len(u[1]) for u in units))

        def run_unit(u):
            name, games = u
            collect_boxes(games, name)
            return name, len(games)

        with ThreadPoolExecutor(max_workers=3) as ex:
            for name, n in ex.map(run_unit, units):
                print("   box done", name, n, round(time.time() - T0, 1), "s")

    if cmd == "merge":
        merge()

    print("[DONE]", cmd, "requests", NREQ[0], "fails", len(FAILS), round(time.time() - T0, 1), "s")
    if FAILS:
        json.dump(FAILS, open(cpath("fails_%s" % cmd), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def loadc(name):
    p = cpath(name)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return None


def merge():
    """캐시 → data/kovo_raw.json (기존 파일의 퓨처스/뉴스/live 는 유지하며 v 확장)"""
    old = {}
    op = os.path.join(DATA, "kovo_raw.json")
    if os.path.exists(op):
        old = json.load(open(op, encoding="utf-8"))
    sl_v, sl_cup, sl_fut, teams_master = season_lists()
    out = dict(old)
    out["seasonListV"] = sl_v
    out["seasonListCup"] = sl_cup
    out["futuresSeasons"] = sl_fut
    out["teamsMaster"] = teams_master
    # v
    v = {}
    for fn in sorted(os.listdir(CACHE)):
        if fn.startswith("v_") and fn.endswith(".json"):
            _, sc, g = fn[:-5].split("_")
            v.setdefault(sc, {})[g] = json.load(open(os.path.join(CACHE, fn), encoding="utf-8"))
    if v:
        out["v"] = v
    cup = {}
    cup_meta = {}
    for cs in sl_cup:
        cup_meta[cs["seasonCode"]] = {"name": cs.get("seasonName"), "year": cs.get("ryear"), "leagues": cs.get("leagues")}
        for g in ("1", "2"):
            d = loadc("cup_%s_%s" % (cs["seasonCode"], g))
            if d:
                cup.setdefault(cs["seasonCode"], {})[g] = d
    if cup:
        out["cup"] = cup
        out["cup_meta_all"] = cup_meta
        for k, m in cup_meta.items():
            out["cup_meta_" + k] = m
    sp = {}
    sp_meta = {}
    try:
        sl_sp = loadc("specialSeasons") or {}
        for gc, sl in sl_sp.items():
            for s in sl:
                key = gc + s["seasonCode"]
                sp_meta[key] = {"name": s.get("seasonName"), "year": s.get("ryear"), "gcode": gc}
                for g in ("1", "2"):
                    d = loadc("sp_%s_%s_%s" % (gc, s["seasonCode"], g))
                    if d:
                        sp.setdefault(key, {})[g] = d
        if sp:
            out["special"] = sp
            out["specialMeta"] = sp_meta
    except Exception as e:
        print("special merge skip", e)
    fut = {}
    fut_meta = {}
    for fs in sl_fut:
        fut_meta[fs["seasonCode"]] = {"name": fs.get("seasonName"), "year": fs.get("ryear"), "leagues": fs.get("leagues")}
        for g in ("1", "2"):
            d = loadc("fut_%s_%s" % (fs["seasonCode"], g))
            if d:
                fut.setdefault(fs["seasonCode"], {})[g] = d
    if fut:
        out["futures"] = fut
        out["futuresMeta"] = fut_meta
    # players
    pl = {}
    for fn in os.listdir(CACHE):
        if fn.startswith("p_") and fn.endswith(".json"):
            pc = fn[2:-5]
            pl[pc] = json.load(open(os.path.join(CACHE, fn), encoding="utf-8"))
    if pl:
        out["players"] = pl
    # boxes (시즌별 캐시 병합)
    boxes = {}
    for fn in os.listdir(CACHE):
        if fn.startswith("box_") and fn.endswith(".json"):
            boxes.update(json.load(open(os.path.join(CACHE, fn), encoding="utf-8")))
    if boxes:
        out["games"] = boxes
    out["meta"] = out.get("meta") or {}
    out["meta"]["merged_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    out["meta"]["cache_counts"] = {
        "v_season_gender": len(v) and sum(len(x) for x in v.values()),
        "cup_season_gender": sum(len(x) for x in cup.values()),
        "fut_season_gender": sum(len(x) for x in fut.values()),
        "players": len(pl),
        "boxes": len(boxes),
    }
    json.dump(out, open(op + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(op + ".tmp", op)
    print("merged", op, os.path.getsize(op), out["meta"]["cache_counts"])


if __name__ == "__main__":
    main()
