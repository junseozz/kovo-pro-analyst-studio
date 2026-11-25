#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kovo_raw.json → 앱용 데이터(KOVO_DATA) + GitHub 청크 + 단일 HTML 빌드. (v2 전수판)
- 공식 KOVO API 실측값만 사용. 파생 지표는 원자료로부터 계산.
"""
import json, os, re, hashlib, datetime, sys
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
RAW = os.path.join(ROOT, "data", "kovo_raw.json")
EXT = os.path.join(ROOT, "data", "external.json")
KOVO_NEWS = os.path.join(ROOT, "data", "kovo_news_raw.json")
OUT_HTML = "/workspace/KOVO_PRO_ANALYST_STUDIO.html"
REPO = os.path.join(ROOT, "repo")
TPL = os.path.join(ROOT, "templates")


def load(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def clean_text(s):
    s = re.sub(r"<script[\s\S]*?</script>", " ", s or "", flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return re.sub(r"\s+", " ", s).strip()


def imgs_from(html):
    return re.findall(r'<img[^>]+src="([^"]+)"', html or "")


def n(v):
    try:
        if v is None or v == "":
            return v
        f = float(v)
        return int(f) if f == int(f) else round(f, 4)
    except Exception:
        return v


def dedupe(rows):
    def key(r):
        return r[0] if isinstance(r, (list, tuple)) else r.get("pcode")

    def by(r):
        return (r[6] or 0) if isinstance(r, (list, tuple)) else (r.get("s_count") or 0)

    best, order = {}, []
    for r in rows:
        k = key(r)
        if k not in best:
            best[k] = r; order.append(k)
        elif by(r) > by(best[k]):
            best[k] = r
    return [best[k] for k in order]


PR_FIELDS = ["pcode", "pname", "tcode", "tsname", "bnum", "g_count", "s_count", "point",
             "att", "ats", "atf", "ate", "atsp", "st", "ss", "sf", "bt", "bs", "dt", "ds", "df",
             "sett", "sets", "setf", "rt", "rs", "rf", "err",
             "oat", "oas", "oaf", "oae", "tat", "tas", "taf", "tae",
             "mat", "mas", "maf", "mae", "bat", "bas", "baf", "bae",
             "sat", "sas", "saf", "sae", "csat", "csas", "csaf", "csae",
             "bsp", "ssp", "dsp", "setsp", "rsp", "sasp"]
TEAM_FIELDS = ["g_count", "s_count", "point", "att", "ats", "atf", "ate", "atsp", "st", "ss",
               "sf", "bt", "bs", "dt", "ds", "df", "sett", "sets", "setf", "rt", "rs", "rf", "rsp",
               "err", "bsp", "ssp", "dsp", "setsp", "sasp", "bas", "sas"]
BOX_FIELDS = ["point", "att", "ats", "atf", "ate", "atsp", "st", "ss", "sf", "bt", "bs", "dt", "ds",
              "sett", "sets", "setf", "rt", "rs", "rf", "err", "oat", "oas", "tat", "tas", "mat", "mas",
              "bat", "bas", "sat", "sas", "csat", "csas"]

GEN = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

# 상태 분류 키워드
K_RETIRE = ("은퇴",)
K_ARMY = ("상무", "국군체육부대", "신협상무", "병역", "입대", "군복무")
K_RELEASE = ("자유신분", "임의해지", "방출", "웨이버", "계약해지", "임의탈퇴")
K_FA = ("FA", "자유계약")
K_TRADE = ("이적", "트레이드", "양도", "양수")
K_LOAN = ("임대",)


def classify_history(hist):
    """이력 문자열 → 이벤트 목록"""
    ev = []
    for i, h in enumerate(hist or []):
        h = str(h)
        typ = "등록"
        if "드래프트" in h:
            typ = "드래프트"
        elif "병역의무완료" in h:
            typ = "병역완료"
        elif any(k in h for k in K_RETIRE):
            typ = "은퇴"
        elif any(k in h for k in K_RELEASE):
            typ = "방출"
        elif any(k in h for k in K_ARMY):
            typ = "군복무"
        elif any(k in h for k in K_LOAN):
            typ = "임대"
        elif any(k in h for k in K_FA):
            typ = "FA"
        elif any(k in h for k in K_TRADE):
            typ = "이적"
        elif "계약" in h:
            typ = "계약"
        elif "프로출범등록" in h:
            typ = "등록"
        ev.append({"i": i, "t": typ, "x": h})
    return ev


def team_of_event(h):
    """'2024-2025 흥국생명 계약 (2025.04.24)' → 흥국생명"""
    h = str(h or "")
    m = re.match(r"^\s*(\d{4})(?:-\d{4})?\s+(\S+?)\s+(?:프로출범등록|등록|계약|이적|임대|해외임대|드래프트|자유신분|임의해지|은퇴|입대|제대|복귀|방출)", h)
    if m:
        return m.group(2)
    parts = h.split()
    return parts[1] if len(parts) > 1 else ""


def parse_school(school):
    if not school:
        return {"hs": "", "univ": "", "all": []}
    parts = [x.strip() for x in re.split(r"[/,·]", school) if x.strip()]
    hs = ""
    univ = ""
    for p in parts:
        if re.search(r"(고등학교|고)$", p) and not hs:
            hs = p
        if re.search(r"(대학교|대학|대)$", p) and not univ:
            univ = p
    return {"hs": hs, "univ": univ, "all": parts}


def build():
    raw = load(RAW)
    ext = load(EXT, {})
    kn = load(KOVO_NEWS, [])
    teams = {}
    master = raw.get("teamsMaster") or []
    for t in master:
        tr = {}
        for x in t.get("translations") or []:
            tr[x["languageCode"]] = x
        ko = tr.get("ko") or {}
        if not ko:
            continue
        teams[t["code"]] = {"n": ko.get("shortName") or ko.get("name"), "f": ko.get("name") or ko.get("shortName"),
                            "e": t.get("emblemUrl") or "", "g": "M" if t.get("gender") == "MALE" else ("W" if t.get("gender") == "FEMALE" else ""),
                            "addr": ko.get("address") or "", "hp": t.get("homepageUrl") or "", "tel": t.get("tel") or "",
                            "intro": ko.get("description") or ""}
    # 스탠딩에서 보이는 구단(과거 사명 포함) 보강
    for sc, gd in (raw.get("v") or {}).items():
        for g, d in gd.items():
            for r in d.get("standings") or []:
                c = r.get("tcode")
                if not c:
                    continue
                if c not in teams:
                    teams[c] = {"n": r.get("tsname") or c, "f": r.get("tsname") or c,
                                "e": r.get("emblemUrl") or r.get("emblem") or "", "g": "M" if g == "1" else "W",
                                "addr": "", "hp": "", "tel": "", "intro": ""}
                elif not teams[c].get("e"):
                    teams[c]["e"] = r.get("emblemUrl") or r.get("emblem") or ""
    for code, t in (raw.get("futuresTeams") or {}).items():
        if code not in teams:
            teams[code] = {"n": t["name"], "f": t["name"], "e": t.get("emblem") or "", "g": "", "addr": "", "hp": "", "tel": "", "intro": ""}
        elif not teams[code].get("e"):
            teams[code]["e"] = t.get("emblem") or ""
    # 퓨처스·컵대회 출전팀(실업팀 포함) 보강 — 경기 일정의 공식 팀명/엠블럼 사용
    for src in (raw.get("futures") or {}, raw.get("cup") or {}, raw.get("special") or {}):
        for sc, sd in (src or {}).items():
            for g in ("1", "2"):
                d = (sd or {}).get(g) or {}
                for lc, blk in (d.get("leagues") or {}).items():
                    for x in blk.get("games") or []:
                        for code, short, full, em in ((x.get("hcode"), x.get("hsname"), x.get("hname"), x.get("homeEmblemUrl")),
                                                      (x.get("acode"), x.get("asname"), x.get("aname"), x.get("awayEmblemUrl"))):
                            if not code:
                                continue
                            if code not in teams:
                                teams[code] = {"n": short or full or code, "f": full or short or code, "e": em or "",
                                               "g": "M" if g == "1" else "W", "addr": "", "hp": "", "tel": "", "intro": ""}
                            elif not teams[code].get("e") and em:
                                teams[code]["e"] = em

    sl_v = {s["seasonCode"]: s for s in raw.get("seasonListV") or []}
    seasons = []
    for sc in sorted((raw.get("v") or {}).keys(), reverse=True):
        s = sl_v.get(sc) or {}
        std = (((raw["v"][sc].get("1") or {}).get("standings")) or [])
        seasons.append({"c": sc, "n": s.get("seasonName") or (std[0]["seasonName"] if std else sc),
                        "y": s.get("ryear") or "", "cur": 0})
    if seasons:
        seasons[0]["cur"] = 1  # 최신 시즌(새 시즌이 들어오면 자동으로 이동)
    recent3 = [s["c"] for s in seasons[:3]]
    cupSeasons, futSeasons = [], []
    cm = raw.get("cup_meta_all") or {}
    for sc in sorted((raw.get("cup") or {}).keys(), reverse=True):
        m = cm.get(sc) or raw.get("cup_meta_" + sc) or {}
        cupSeasons.append({"c": sc, "n": m.get("name") or sc, "y": m.get("year") or ""})
    fm = raw.get("futuresMeta") or {}
    for sc in sorted((raw.get("futures") or {}).keys(), reverse=True):
        f = fm.get(sc) or {}
        futSeasons.append({"c": sc, "n": f.get("name") or sc, "y": f.get("year") or ""})

    std, tstat, pr, rk, sch, aw = {}, {}, {}, {}, {}, {}
    for sc, gd in (raw.get("v") or {}).items():
        std[sc], tstat[sc], pr[sc], rk[sc], sch[sc], aw[sc] = {}, {}, {}, {}, {}, {}
        for g, key in (("1", "M"), ("2", "W")):
            d = gd.get(g) or {}
            std[sc][key] = [[n(r.get("rank")), r.get("tcode"), r.get("tsname"), n(r.get("win")), n(r.get("lost")),
                             n(r.get("winp")), n(r.get("swin")), n(r.get("slost")), n(r.get("point")), n(r.get("lpoint")),
                             r.get("con") or "", r.get("udate") or ""] for r in d.get("standings") or []]
            ts = {}
            tr = d.get("teamRecords")
            for r in (tr.get("content") if isinstance(tr, dict) else []) or []:
                ts[r["tcode"]] = [n(r.get(f)) for f in TEAM_FIELDS]
            tstat[sc][key] = ts
            pr[sc][key] = [[n(r.get(f)) if f not in ("pcode", "pname", "tcode", "tsname") else r.get(f) for f in PR_FIELDS]
                           for r in dedupe(d.get("playerRecords") or [])]
            rk[sc][key] = {}
            for rp, rows in (d.get("ranks") or {}).items():
                if not rows:
                    continue
                rk[sc][key][rp] = [[n(r.get("rank")), r.get("pcode"), r.get("pname"), r.get("tcode"), r.get("tsname"),
                                    n(r.get("su")), n(r.get("tr")), n(r.get("co")), n(r.get("fa")), n(r.get("err")),
                                    n(r.get("sup")), n(r.get("vblocking")), n(r.get("g_count")), n(r.get("s_sount")),
                                    r.get("image") or ""] for r in rows[:30]]
            games = [pack_game(x, "201") for x in d.get("schedule") or []]
            for lc, arr in (d.get("playoffs") or {}).items():
                for x in arr:
                    games.append(pack_game(x, lc))
            games.sort(key=lambda x: (x["d"] or "", x["n"] or 0))
            sch[sc][key] = games
            a = d.get("awards") or {}
            aw[sc][key] = {
                "mvp": [[r.get("rank"), r.get("playerName"), r.get("teamName"), r.get("content"), r.get("itemName"), r.get("item2")] for r in (a.get("mvp") or [])],
                "triple": [[r.get("rank"), r.get("playerName"), r.get("position"), r.get("teamName"), r.get("gdate"), n(r.get("point")), n(r.get("awSuc")), n(r.get("bbSuc")), n(r.get("vsuc"))] for r in ((a.get("triple") or {}).get("content") or [])],
                "achieve": [[r.get("rank"), r.get("season"), r.get("teamName"), r.get("awayName"), r.get("gameDate"), r.get("record"), n(r.get("totalRecord")), r.get("unit")] for r in ((a.get("achieve") or {}).get("content") or [])],
            }

    # 퓨처스
    fut = {}
    for sc, f in (raw.get("futures") or {}).items():
        fut[sc] = {"n": (fm.get(sc) or {}).get("name") or sc, "y": (fm.get(sc) or {}).get("year"), "M": {}, "W": {}}
        for g, key in (("1", "M"), ("2", "W")):
            d = f.get(g) or ((f.get("g") or {}).get(g)) or {}
            games = []
            for lc, blk in (d.get("leagues") or {}).items():
                for x in blk.get("games") or []:
                    games.append(pack_game(x, lc))
            games.sort(key=lambda x: (x["d"] or "", x["n"] or 0))
            tr200 = ((d.get("teamRecords") or {}).get("200")) or []
            pr200 = ((d.get("playerRecords") or {}).get("200")) or []
            fut[sc][key] = {
                "leagues": {lc: blk.get("name") for lc, blk in (d.get("leagues") or {}).items()},
                "games": games,
                "teams": [[n(r.get("rank")), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname") or "",
                           n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")), n(r.get("att")), n(r.get("ats")),
                           n(r.get("atsp")), n(r.get("bs")), n(r.get("ss")), n(r.get("ds")), n(r.get("sets")), n(r.get("rs"))] for r in tr200],
                "players": [[r.get("pcode"), r.get("pname"), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname") or "",
                             n(r.get("bnum"))] + [n(r.get(f)) for f in PR_FIELDS[5:]] for r in dedupe(pr200)],
            }

    # 컵대회
    cup = {}
    for sc, c in (raw.get("cup") or {}).items():
        m = cm.get(sc) or raw.get("cup_meta_" + sc) or {}
        cup[sc] = {"n": m.get("name"), "y": m.get("year"), "M": {}, "W": {}}
        for g, key in (("1", "M"), ("2", "W")):
            d = (c.get(g) or {})
            games, seen_g = [], {}
            for lc, blk in (d.get("leagues") or {}).items():
                for x in blk.get("games") or []:
                    gg = pack_game(x, lc)
                    k = (gg["d"], gg["h"], gg["a"], gg["n"])
                    if k in seen_g:
                        # 200(전체 일정)과 세부 리그가 같은 경기를 중복 제공 → 세부 리그 표기를 남긴다
                        if seen_g[k]["lc"] == "200" and lc != "200":
                            games[games.index(seen_g[k])] = gg
                            seen_g[k] = gg
                        continue
                    seen_g[k] = gg
                    games.append(gg)
            games.sort(key=lambda x: (x["d"] or "", x["n"] or 0))
            tr = (d.get("teamRecords") or {}).get("200") or []
            if not tr:
                for lc, arr in (d.get("teamRecords") or {}).items():
                    if arr:
                        tr = arr; break
            prr = (d.get("playerRecords") or {}).get("200") or []
            if not prr:
                for lc, arr in (d.get("playerRecords") or {}).items():
                    if arr:
                        prr = arr; break
            cup[sc][key] = {"leagues": {lc: blk.get("name") for lc, blk in (d.get("leagues") or {}).items()},
                            "games": games,
                            "teams": [[n(r.get("rank")), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname"),
                                       n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")), n(r.get("att")),
                                       n(r.get("ats")), n(r.get("atsp")), n(r.get("bs")), n(r.get("ss")), n(r.get("ds")),
                                       n(r.get("sets")), n(r.get("rs"))] for r in tr],
                            "players": [[r.get("pcode"), r.get("pname"), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname"),
                                         n(r.get("bnum"))] + [n(r.get(f)) for f in PR_FIELDS[5:]] for r in dedupe(prr)]}

    # 국제·특별전 (한일 Top Match·최강전·라이벌매치·한중일·올스타·슈퍼매치)
    intl = {}
    spm = raw.get("specialMeta") or {}
    for key, sdata in (raw.get("special") or {}).items():
        meta = spm.get(key) or {}
        intl[key] = {"n": meta.get("name") or key, "y": meta.get("year"), "gc": meta.get("gcode"), "M": {}, "W": {}}
        for g, gk in (("1", "M"), ("2", "W")):
            d = (sdata or {}).get(g) or {}
            games = []
            for lc, blk in (d.get("leagues") or {}).items():
                for x in blk.get("games") or []:
                    games.append(pack_game(x, lc))
            games.sort(key=lambda x: (x["d"] or "", x["n"] or 0))
            tr = []
            for lc, arr in (d.get("teamRecords") or {}).items():
                if arr:
                    tr = arr; break
            prr = []
            for lc, arr in (d.get("playerRecords") or {}).items():
                if arr:
                    prr = arr; break
            intl[key][gk] = {
                "leagues": {lc: blk.get("name") for lc, blk in (d.get("leagues") or {}).items()},
                "games": games,
                "teams": [[n(r.get("rank")), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname"),
                           n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")), n(r.get("att")), n(r.get("ats")),
                           n(r.get("atsp")), n(r.get("bs")), n(r.get("ss")), n(r.get("ds")), n(r.get("sets")), n(r.get("rs"))] for r in tr],
                "players": [[r.get("pcode"), r.get("pname"), r.get("tcode"), (teams.get(r.get("tcode"), {}) or {}).get("n") or r.get("tsname"),
                             n(r.get("bnum"))] + [n(r.get(f)) for f in PR_FIELDS[5:]] for r in dedupe(prr)],
            }

    # 선수
    latest = seasons[0]["c"] if seasons else ""
    roster_latest = set()
    for g, key in (("1", "M"), ("2", "W")):
        for r in ((std.get(latest) or {}).get(key) or []):
            pass
    # 최신 시즌 등록 선수 = 최신 시즌 선수 기록 + 로스터
    # 최신 시즌 '등록 로스터'만 현역으로 본다. (경기 기록 행은 은퇴·미등록 선수도 포함될 수 있음)
    roster_by_team = {"M": {}, "W": {}}
    for g in ("1", "2"):
        for tc, arr in (((raw.get("v", {}).get(latest, {}).get(g, {}) or {}).get("rosters")) or {}).items():
            for p in arr:
                stt = p.get("status") or []
                if p.get("visible") is False:
                    continue
                if p.get("playerCode") and ("REGISTER" in stt):
                    pc = str(p["playerCode"])
                    roster_latest.add(pc)
                    roster_by_team["M" if g == "1" else "W"].setdefault(tc, []).append(pc)
    players = []
    for pc, p in (raw.get("players") or {}).items():
        d = p.get("detail") or {}
        if not d:
            # 상세가 없으면 최신 기록에서 최소 정보 구성 (추정 아님)
            d = {}
        sr = p.get("seasonRecords") or []
        sr = sorted(sr, key=lambda x: (x.get("seasonDivision") or ""), reverse=True)
        hist = [str(x) for x in (p.get("history") or [])]
        events = classify_history(hist)
        types = [e["t"] for e in events]
        last = events[-1] if events else None
        status = "active" if pc in roster_latest else "former"
        if "은퇴" in types:
            status = "retired"
        elif last and last["t"] == "방출":
            status = "released"
        elif last and last["t"] == "군복무":
            status = "army"
        elif pc not in roster_latest and "은퇴" not in types:
            status = "former"
        if pc in roster_latest:
            status = "active"
            if last and last["t"] == "군복무":
                status = "army"
        honors = (p.get("honor") or {})
        sc_parsed = parse_school(d.get("school"))
        team_names = []
        for e in events:
            tn = team_of_event(e["x"])
            if tn and tn not in team_names and not re.match(r"^\d", tn):
                team_names.append(tn)
        players.append({
            "p": pc, "n": d.get("name"), "t": d.get("teamCode"), "tn": d.get("teamName"),
            "pos": d.get("position"), "no": n(d.get("backNumber")), "birth": d.get("birthDate"),
            "img": d.get("image") or "", "school": d.get("school") or "", "hs": sc_parsed["hs"], "univ": sc_parsed["univ"],
            "nat": d.get("nation") or "", "army": d.get("armyStatus") or "", "h": n(d.get("height")), "w": n(d.get("weight")),
            "st": status, "ev": [[e["t"], e["x"]] for e in events],
            "teams": team_names, "debut": (events[0]["x"][:4] if events else ""),
            "hist": hist,
            "hon": [str(x) for x in (honors.get("awards") or [])],
            "hon2": [str(x) for x in (honors.get("tripleCrowns") or [])],
            "hon3": [str(x) for x in (honors.get("standardRecords") or [])],
            "seasons": [[x.get("leagueDivision"), x.get("seasonDivision"), x.get("teamName"), n(x.get("gameCount")),
                         n(x.get("setCount")), n(x.get("point")), n(x.get("attackTotalSuccess")), n(x.get("blockingSetSuccess")),
                         n(x.get("serveSetSuccess")), n(x.get("setSuccess")), n(x.get("receiveSuccess")),
                         n(x.get("digSetSuccess")), n(x.get("error"))] for x in sr],
        })
    # 상세가 없거나 이름이 빈 선수는 공식 경기 기록의 이름/팀으로 보강
    nm = {}
    for sc in sorted((raw.get("v") or {}).keys(), reverse=True):
        for g in ("1", "2"):
            for r in ((raw["v"][sc].get(g) or {}).get("playerRecords") or []):
                pc = str(r.get("pcode") or "")
                if pc and pc not in nm and r.get("pname"):
                    nm[pc] = (r.get("pname"), r.get("tcode"), r.get("tsname"), r.get("bnum"))
    # 로스터(모든 대회)에서도 이름 보강
    def add_roster_names(rosters, gender):
        for tc, arr in (rosters or {}).items():
            for p in arr or []:
                pc = str(p.get("playerCode") or "")
                if pc and pc not in nm and p.get("name"):
                    nm[pc] = (p.get("name"), tc, (teams.get(tc, {}) or {}).get("n") or p.get("teamName"), p.get("backNumber"))
    for sc, gd in (raw.get("v") or {}).items():
        for g in ("1", "2"):
            add_roster_names(((gd.get(g) or {}).get("rosters")), g)
    for src in (raw.get("cup") or {}, raw.get("futures") or {}, raw.get("special") or {}):
        for key, sd in src.items():
            for g in ("1", "2"):
                d = (sd or {}).get(g) or {}
                add_roster_names(d.get("rosters"), g)
    for p in players:
        if not p.get("n") and p["p"] in nm:
            x = nm[p["p"]]
            p["n"], p["t"], p["tn"], p["no"] = x[0], x[1], x[2], n(x[3])
    # 이름조차 공식 데이터에 없는 항목은 표시할 수 없으므로 제외
    players = [p for p in players if p.get("n")]
    # 상세 없는 선수는 최신 기록으로 이름/팀/포지션 보강
    bycode = {p["p"]: p for p in players}
    for sc in sorted((raw.get("v") or {}).keys(), reverse=True):
        for g in ("1", "2"):
            for r in ((raw["v"][sc].get(g) or {}).get("playerRecords") or []):
                pc = str(r.get("pcode") or "")
                if not pc or pc in bycode:
                    continue
                bycode[pc] = {"p": pc, "n": r.get("pname"), "t": r.get("tcode"), "tn": r.get("tsname"), "pos": "",
                              "no": n(r.get("bnum")), "birth": "", "img": "", "school": "", "hs": "", "univ": "",
                              "nat": "", "army": "", "h": None, "w": None,
                              "st": "active" if pc in roster_latest else "former", "ev": [], "teams": [], "debut": "", "hist": [],
                              "hon": [], "hon2": [], "hon3": [], "seasons": []}
                players.append(bycode[pc])
    # 이름 중복 표시용 (동명이인)
    cnt = {}
    for p in players:
        cnt[p["n"]] = cnt.get(p["n"], 0) + 1
    for p in players:
        p["dup"] = 1 if cnt.get(p["n"], 0) > 1 else 0

    # 박스스코어 (최근 3시즌은 내장, 전체는 시즌별 lazy 청크)
    def trim_box(b, lc, sc):
        gm = b["game"]
        rows = []
        for p in b.get("player") or []:
            rows.append([p.get("tcode"), p.get("pname"), p.get("position"), n(p.get("bnum")), p.get("ynCaptain"),
                         p.get("ynS1"), p.get("ynS2"), p.get("ynS3"), p.get("ynS4"), p.get("ynS5")] +
                        [n(p.get(f)) for f in BOX_FIELDS])
        return {"g": pack_game(gm, lc), "p": rows, "x": ["tcode", "pname", "position", "bnum", "cap", "s1", "s2", "s3", "s4", "s5"] + BOX_FIELDS}

    allbox = raw.get("games") or {}
    box = {}
    boxchunks = {}
    for k, b in allbox.items():
        gm = b.get("game") or {}
        sc = str(gm.get("seasonCode"))
        # 시즌코드가 001~023 형식이면 앞자리 0 제거 비교
        sc3 = sc[-3:].zfill(3)
        rec = trim_box(b, gm.get("leagueCode"), sc3)
        if sc3 in recent3:
            box[k] = rec
        boxchunks.setdefault(sc3, {})[k] = rec

    # 뉴스
    news = {"kovo": [], "press": [], "notice": []}
    raw_news = raw.get("news") or {}
    for kind, items in raw_news.items():
        out = []
        for it in items:
            title = ""
            for t in (it.get("titles") or []):
                if t.get("languageCode") == "ko":
                    title = t.get("title") or ""; break
            body = ""
            for b in (it.get("bodies") or []):
                if b.get("languageCode") == "ko":
                    body = b.get("body") or ""; break
            if not body and it.get("bodies"):
                body = it["bodies"][0].get("body") or ""
            if not title:
                title = clean_text(body)[:70]
            thumbs = [t.get("url") for t in (it.get("thumbnails") or []) if t.get("url")]
            images = thumbs + [u for u in imgs_from(body) if u.startswith("http")][:2]
            out.append({"i": it.get("id"), "d": (it.get("createdAt") or "")[:10], "t": title,
                        "x": clean_text(body)[:1500], "img": images[:1], "ty": kind})
        news[kind] = out
    # KOVO 뉴스 원본(최대 360건) — id 중복 제거 후 병합
    if kn:
        seen = {x["i"] for x in news["kovo"] + news["press"] + news["notice"] if x.get("i")}
        for it in kn:
            if it.get("id") in seen:
                continue
            title = ""
            for t in (it.get("titles") or []):
                if t.get("languageCode") == "ko":
                    title = t.get("title") or ""; break
            body = ""
            for b in (it.get("bodies") or []):
                if b.get("languageCode") == "ko":
                    body = b.get("body") or ""; break
            if not body and it.get("bodies"):
                body = it["bodies"][0].get("body") or ""
            if not title:
                title = clean_text(body)[:70]
            kind = "notice" if "notice" in str(it.get("category") or it.get("type") or "").lower() else "kovo"
            news[kind].append({"i": it.get("id"), "d": (it.get("createdAt") or "")[:10], "t": title,
                               "x": clean_text(body)[:1500],
                               "img": [t.get("url") for t in (it.get("thumbnails") or []) if t.get("url")][:1], "ty": kind})
    for k in news:
        news[k].sort(key=lambda x: (x.get("d") or ""), reverse=True)

    packed_ext = []
    for it in ((ext or {}).get("items") or []):
        d = it.get("d") or ""
        try:
            d = parsedate_to_datetime(d).astimezone().strftime("%Y-%m-%d %H:%M")
        except Exception:
            d = d[:16]
        t = it.get("t") or ""
        src = it.get("s") or ""
        if src and t.endswith(" - " + src):
            t = t[: -len(src) - 3]
        packed_ext.append({"t": t, "u": it.get("u") or "", "d": d, "s": src, "f": it.get("f") or ""})
    packed_ext.sort(key=lambda x: (x.get("d") or ""), reverse=True)

    # 실시간/일정 스냅샷 (최신 시즌 기준)
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    upcoming, today_g, recent_g = {"M": [], "W": []}, {"M": [], "W": []}, {"M": [], "W": []}
    for key in ("M", "W"):
        rows = (sch.get(latest) or {}).get(key) or []
        for g in rows:
            if not g.get("d"):
                continue
            played = (g.get("hs") or 0) + (g.get("as") or 0) > 0
            item = dict(g)
            if g["d"] == today:
                today_g[key].append(item)
            if played:
                recent_g[key].append(item)
            else:
                upcoming[key].append(item)
        recent_g[key] = sorted(recent_g[key], key=lambda x: x["d"], reverse=True)[:10]
    live = {"snapshot_at": GEN, "today": today_g, "upcoming": upcoming, "recent": recent_g,
            "latest_season": latest}

    data = {
        "v": "2.0.0", "gen": GEN,
        "seasons": seasons, "recent3": recent3, "cupSeasons": cupSeasons, "futSeasons": futSeasons,
        "teams": teams,
        "std": std, "tstat": tstat, "pr": pr, "rk": rk, "sch": sch, "aw": aw,
        "box": box, "boxSeasons": sorted(boxchunks.keys(), reverse=True),
        "cup": cup, "fut": fut, "intl": intl,
        "players": players, "roster": sorted(roster_latest), "rosterTeams": roster_by_team,
        "news": news, "ext": packed_ext, "live": live,
        "meta": {
            "generated": GEN, "source": "KOVO 공식 API (user-api.kovo.co.kr)",
            "season_count": len(seasons), "cup_count": len(cupSeasons), "fut_count": len(futSeasons),
            "player_count": len(players), "box_count": len(allbox),
            "box_embedded": len(box),
            "news_count": sum(len(v) for v in news.values()), "ext_count": len(packed_ext),
            "games": sum(len(v[k]) for v in sch.values() for k in v),
            "blocked": (ext or {}).get("blocked", []),
        },
    }
    return data, boxchunks


def pack_game(x, lc):
    s = []
    for i in range(1, 6):
        h, a = x.get("hs%dpoint" % i), x.get("as%dpoint" % i)
        if (h or 0) or (a or 0):
            s.append([n(h), n(a)])
    return {"n": x.get("gnum"), "lc": lc, "r": x.get("round"), "rn": x.get("roundName") or "",
            "d": x.get("gdate"), "t": x.get("gstime") or "", "h": x.get("hcode"), "a": x.get("acode"),
            "hs": n(x.get("hspoint")), "as": n(x.get("aspoint")), "s": s,
            "pl": x.get("place") or "", "sp": n(x.get("spectators")), "g": x.get("gender"),
            "hc": x.get("hsname") or x.get("hn") or "", "ac": x.get("asname") or x.get("an") or ""}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def chunks(data):
    core = {k: data[k] for k in ("v", "gen", "seasons", "recent3", "cupSeasons", "futSeasons", "teams", "std",
                                 "tstat", "pr", "rk", "aw", "meta", "roster", "rosterTeams")}
    games = {k: data[k] for k in ("sch", "box", "boxSeasons", "cup", "fut", "intl")}
    season = {k: data[k] for k in ("players",)}
    news = {k: data[k] for k in ("news", "ext")}
    live = {"live": data.get("live"), "sch": {sc: data["sch"].get(sc) for sc in data["recent3"]}, "gen": data["gen"]}
    return [("core", core), ("games", games), ("season", season), ("news", news), ("live_patch", live)]


def main():
    data, boxchunks = build()
    CH = chunks(data)
    # 앱이 바뀐 청크만 내려받도록 청크 해시를 함께 심는다
    data["hashes"] = {cid: hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
                      for cid, body in CH}
    print("chunk sizes:")
    for cid, body in CH:
        print("  ", cid, len(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()))
    os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
    os.makedirs(os.path.join(REPO, "tools"), exist_ok=True)

    man = {"schema_version": 3, "app_version": data["v"],
           "updated_at": GEN, "checked_at": GEN,
           "data_through": max([g["d"] for s in data["sch"].values() for g in s["M"] + s["W"]
                                if g.get("d") and (g.get("hs") or 0) + (g.get("as") or 0) > 0] or [""]),
           "latest_season": data["seasons"][0]["c"] if data["seasons"] else "",
           "recent3": data["recent3"],
           "note": "앱이 맨 먼저 이 파일을 읽고 sha256 이 바뀐 청크만 내려받습니다. box_* 청크는 경기 박스스코어를 열 때만 내려받습니다.",
           "chunks": []}
    for cid, body in CH:
        jp = os.path.join(REPO, "data", cid + ".json")
        js = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        open(jp, "w", encoding="utf-8").write(js)
        open(os.path.join(REPO, "data", cid + ".js"), "w", encoding="utf-8").write(
            "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % js)
        man["chunks"].append({"id": cid, "path": "data/%s.json" % cid, "js": "data/%s.js" % cid,
                              "sha256": sha256_file(jp), "bytes": os.path.getsize(jp),
                              "updated_at": GEN, "globals": ["KOVO_DATA"]})
        print(" chunk", cid, man["chunks"][-1]["bytes"])
    # 박스스코어 시즌별 lazy 청크
    for sc, body in sorted(boxchunks.items()):
        cid = "box_" + sc
        jp = os.path.join(REPO, "data", cid + ".json")
        js = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        open(jp, "w", encoding="utf-8").write(js)
        open(os.path.join(REPO, "data", cid + ".js"), "w", encoding="utf-8").write(
            "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % js)
        man["chunks"].append({"id": cid, "path": "data/%s.json" % cid, "js": "data/%s.js" % cid,
                              "sha256": sha256_file(jp), "bytes": os.path.getsize(jp), "lazy": 1,
                              "updated_at": GEN, "globals": ["KOVO_BOX"]})
        print(" box chunk", cid, man["chunks"][-1]["bytes"])
    open(os.path.join(REPO, "data", "manifest.json"), "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=1))
    open(os.path.join(REPO, "data", "manifest.js"), "w", encoding="utf-8").write(
        "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % json.dumps(man, ensure_ascii=False, separators=(",", ":")))

    css = open(os.path.join(TPL, "app.css"), encoding="utf-8").read()
    jdir = os.path.join(TPL, "js")
    parts = sorted([f for f in os.listdir(jdir) if f.endswith(".js")]) if os.path.isdir(jdir) else []
    if parts:
        js = "(function(){\n'use strict';\n" + "\n".join(open(os.path.join(jdir, f), encoding="utf-8").read() for f in parts) + "\n})();\n"
    else:
        js = open(os.path.join(TPL, "app.js"), encoding="utf-8").read()
    html_tpl = open(os.path.join(TPL, "app.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out = html_tpl.replace("/*__CSS__*/", css).replace("/*__JS__*/", js).replace("/*__DATA__*/", payload)
    open(OUT_HTML, "w", encoding="utf-8").write(out)
    print("HTML", OUT_HTML, os.path.getsize(OUT_HTML), sha256_file(OUT_HTML))
    print("MD5", hashlib.md5(open(OUT_HTML, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
