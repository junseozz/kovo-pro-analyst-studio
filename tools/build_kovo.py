#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kovo_raw.json → 앱용 압축 데이터(KOVO_DATA) + GitHub 청크 + 단일 HTML 빌드.
"""
import json, os, re, hashlib, datetime, sys
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
RAW = os.path.join(ROOT, "data", "kovo_raw.json")
EXT = os.path.join(ROOT, "data", "external.json")
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

GEN = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

def build():
    raw = load(RAW)
    ext = load(EXT, {})
    teams = {}
    for code, t in raw["teams"].items():
        tr = t.get("tr") or {}
        ko = tr.get("ko") or {}
        teams[code] = {
            "n": ko.get("short") or ko.get("name") or code,
            "f": ko.get("name") or ko.get("short") or code,
            "e": t.get("emblem") or "",
            "g": "M" if t.get("gender") == "MALE" else "W",
            "addr": ko.get("address") or "",
            "hp": t.get("homepage") or "",
            "tel": t.get("tel") or "",
            "intro": ko.get("description") or "",
        }
    for code, t in (raw.get("futuresTeams") or {}).items():
        if code in teams:
            continue
        teams[code] = {"n": t["name"], "f": t["name"], "e": t.get("emblem") or "", "g": "", "addr": "", "hp": "", "tel": "", "intro": ""}

    # 시즌 목록 (최신 우선)
    sl_v = {s["seasonCode"]: s for s in raw.get("seasonListV") or []}
    seasons = []
    for sc in sorted(raw["v"].keys(), reverse=True):
        s = sl_v.get(sc) or {}
        seasons.append({"c": sc, "n": s.get("seasonName") or (raw["v"][sc]["1"]["standings"][0]["seasonName"] if raw["v"][sc]["1"]["standings"] else sc),
                        "y": s.get("ryear") or "", "cur": 1 if sc == "023" else 0})
    cupSeasons = []
    for sc in sorted(raw["cup"].keys(), reverse=True):
        m = raw.get("cup_meta_" + sc) or {}
        cupSeasons.append({"c": sc, "n": m.get("name") or sc, "y": m.get("year") or ""})
    futSeasons = []
    for sc in sorted((raw.get("futures") or {}).keys(), reverse=True):
        f = raw["futures"][sc]
        futSeasons.append({"c": sc, "n": f.get("name") or sc, "y": f.get("year") or ""})

    std, tstat, pr, rk, sch = {}, {}, {}, {}, {}
    for sc, gd in raw["v"].items():
        std[sc], tstat[sc], pr[sc], rk[sc], sch[sc] = {}, {}, {}, {}, {}
        for g, key in (("1", "M"), ("2", "W")):
            d = gd[g]
            std[sc][key] = [[n(r.get("rank")), r["tcode"], r.get("tsname"), n(r.get("win")), n(r.get("lost")),
                             n(r.get("winp")), n(r.get("swin")), n(r.get("slost")), n(r.get("point")), n(r.get("lpoint")),
                             r.get("con") or "", r.get("udate") or ""] for r in d["standings"]]
            ts = {}
            for r in (d["teamRecords"].get("content") if isinstance(d["teamRecords"], dict) else []) or []:
                ts[r["tcode"]] = [n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")), n(r.get("att")), n(r.get("ats")),
                                  n(r.get("atf")), n(r.get("ate")), n(r.get("atsp")), n(r.get("st")), n(r.get("ss")),
                                  n(r.get("sf")), n(r.get("bt")), n(r.get("bs")), n(r.get("dt")), n(r.get("ds")), n(r.get("df")),
                                  n(r.get("sett")), n(r.get("sets")), n(r.get("setf")), n(r.get("rt")), n(r.get("rs")),
                                  n(r.get("rf")), n(r.get("rsp")), n(r.get("err")), n(r.get("bsp")), n(r.get("ssp")),
                                  n(r.get("dsp")), n(r.get("setsp")), n(r.get("sasp")), n(r.get("bas")), n(r.get("sas"))]
            tstat[sc][key] = ts
            pr[sc][key] = [[r.get("pcode"), r.get("pname"), r["tcode"], r.get("tsname"), n(r.get("bnum")),
                            n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")),
                            n(r.get("att")), n(r.get("ats")), n(r.get("atf")), n(r.get("ate")), n(r.get("atsp")),
                            n(r.get("st")), n(r.get("ss")), n(r.get("sf")),
                            n(r.get("bt")), n(r.get("bs")), n(r.get("dt")), n(r.get("ds")), n(r.get("df")),
                            n(r.get("sett")), n(r.get("sets")), n(r.get("setf")),
                            n(r.get("rt")), n(r.get("rs")), n(r.get("rf")), n(r.get("err")),
                            n(r.get("oat")), n(r.get("oas")), n(r.get("oaf")), n(r.get("oae")),
                            n(r.get("tat")), n(r.get("tas")), n(r.get("taf")), n(r.get("tae")),
                            n(r.get("mat")), n(r.get("mas")), n(r.get("maf")), n(r.get("mae")),
                            n(r.get("bat")), n(r.get("bas")), n(r.get("baf")), n(r.get("bae")),
                            n(r.get("sat")), n(r.get("sas")), n(r.get("saf")), n(r.get("sae")),
                            n(r.get("csat")), n(r.get("csas")), n(r.get("csaf")), n(r.get("csae")),
                            n(r.get("bsp")), n(r.get("ssp")), n(r.get("dsp")), n(r.get("setsp")), n(r.get("rsp")),
                            n(r.get("sasp")), n(r.get("warning"))]
                           for r in d["playerRecords"]]
            rk[sc][key] = {}
            for rp, rows in d["ranks"].items():
                if not rows:
                    continue
                rk[sc][key][rp] = [[n(r.get("rank")), r.get("pcode"), r.get("pname"), r.get("tcode"), r.get("tsname"),
                                    n(r.get("su")), n(r.get("tr")), n(r.get("co")), n(r.get("fa")), n(r.get("err")),
                                    n(r.get("sup")), n(r.get("vblocking")), n(r.get("g_count")), n(r.get("s_sount")),
                                    r.get("image") or ""] for r in rows[:30]]
            games = []
            for x in d["schedule"]:
                games.append(pack_game(x, "201"))
            for lc, arr in d["playoffs"].items():
                for x in arr:
                    games.append(pack_game(x, lc))
            sch[sc][key] = games

    # 박스스코어
    box = {}
    PB = ["tcode", "pname", "position", "bnum", "cap", "s1", "s2", "s3", "s4", "s5"]
    NUMS = ["point", "att", "ats", "atf", "ate", "atsp", "oat", "oas", "oaf", "oae", "tat", "tas", "taf", "tae",
            "mat", "mas", "maf", "mae", "bat", "bas", "baf", "bae", "sat", "sas", "saf", "sae", "csat", "csas",
            "csaf", "csae", "st", "ss", "sf", "bt", "bs", "dt", "ds", "df", "sett", "sets", "setf", "rt", "rs", "rf", "err"]
    BX = PB + NUMS
    for k, b in raw["games"].items():
        gm = b["game"]
        box[k] = {
            "g": pack_game(gm, gm.get("leagueCode")),
            "p": [[p.get("tcode"), p.get("pname"), p.get("position"), n(p.get("bnum")), p.get("ynCaptain"),
                   p.get("ynS1"), p.get("ynS2"), p.get("ynS3"), p.get("ynS4"), p.get("ynS5")]
                  + [n(p.get(f)) for f in NUMS] for p in b["player"]],
            "x": BX,
        }
    # 퓨처스
    fut = {}
    for sc, f in (raw.get("futures") or {}).items():
        fut[sc] = {"n": f.get("name"), "y": f.get("year"), "M": {}, "W": {}}
        for g, key in (("1", "M"), ("2", "W")):
            d = f["g"][g]
            games = []
            for lc, blk in d["leagues"].items():
                for x in blk["games"]:
                    games.append(pack_game(x, lc))
            games.sort(key=lambda x: (x["d"] or "", x["n"]))
            tr200 = d["teamRecords"].get("200") or []
            pr200 = d["playerRecords"].get("200") or []
            fut[sc][key] = {
                "leagues": {lc: blk["name"] for lc, blk in d["leagues"].items()},
                "games": games,
                "teams": [[n(r.get("rank")), r["tcode"], (teams.get(r["tcode"], {}) or {}).get("n") or r.get("tsname") or "", n(r.get("g_count")), n(r.get("s_count")),
                           n(r.get("point")), n(r.get("att")), n(r.get("ats")), n(r.get("atsp")), n(r.get("bs")),
                           n(r.get("ss")), n(r.get("ds")), n(r.get("sets")), n(r.get("rs"))] for r in tr200],
                "players": [[r.get("pcode"), r.get("pname"), r["tcode"], (teams.get(r["tcode"], {}) or {}).get("n") or r.get("tsname") or "", n(r.get("bnum")),
                             n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")),
                             n(r.get("att")), n(r.get("ats")), n(r.get("atf")), n(r.get("ate")), n(r.get("atsp")),
                             n(r.get("st")), n(r.get("ss")), n(r.get("sf")), n(r.get("bt")), n(r.get("bs")),
                             n(r.get("dt")), n(r.get("ds")), n(r.get("df")), n(r.get("sett")), n(r.get("sets")),
                             n(r.get("setf")), n(r.get("rt")), n(r.get("rs")), n(r.get("rf")), n(r.get("err"))]
                            for r in pr200],
            }
    fbox = {}
    for k, b in (raw.get("futuresGames") or {}).items():
        gm = b["game"]
        fbox[k] = {"g": pack_game(gm, gm.get("leagueCode")),
                   "p": [[p.get("tcode"), p.get("pname"), p.get("position"), n(p.get("bnum")), p.get("ynCaptain"),
                          p.get("ynS1"), p.get("ynS2"), p.get("ynS3"), p.get("ynS4"), p.get("ynS5")]
                         + [n(p.get(f)) for f in NUMS] for p in b.get("player") or []], "x": BX}

    # 컵대회
    cup = {}
    for sc, c in raw["cup"].items():
        meta = raw.get("cup_meta_" + sc) or {}
        cup[sc] = {"n": meta.get("name"), "y": meta.get("year"), "M": {}, "W": {}}
        for g, key in (("1", "M"), ("2", "W")):
            d = c[g]
            games = []
            for lc, blk in d["leagues"].items():
                for x in blk["games"]:
                    games.append(pack_game(x, lc))
            games.sort(key=lambda x: (x["d"] or "", x["n"]))
            tr = d.get("teamRecords") or []
            prr = d.get("playerRecords") or []
            cup[sc][key] = {"leagues": {lc: blk["name"] for lc, blk in d["leagues"].items()}, "games": games,
                            "teams": [[n(r.get("rank")), r["tcode"], r.get("tsname"), n(r.get("g_count")), n(r.get("s_count")),
                                       n(r.get("point")), n(r.get("att")), n(r.get("ats")), n(r.get("atsp")),
                                       n(r.get("bs")), n(r.get("ss")), n(r.get("ds")), n(r.get("sets")), n(r.get("rs"))] for r in tr],
                            "players": [[r.get("pcode"), r.get("pname"), r["tcode"], (teams.get(r["tcode"], {}) or {}).get("n") or r.get("tsname") or "", n(r.get("bnum")),
                                         n(r.get("g_count")), n(r.get("s_count")), n(r.get("point")), n(r.get("att")),
                                         n(r.get("ats")), n(r.get("atf")), n(r.get("ate")), n(r.get("atsp")),
                                         n(r.get("st")), n(r.get("ss")), n(r.get("sf")), n(r.get("bt")), n(r.get("bs")),
                                         n(r.get("dt")), n(r.get("ds")), n(r.get("df")), n(r.get("sett")), n(r.get("sets")),
                                         n(r.get("setf")), n(r.get("rt")), n(r.get("rs")), n(r.get("rf")), n(r.get("err"))]
                                        for r in prr]}

    # 선수
    players = []
    for pc, p in raw["players"].items():
        d = p.get("detail") or {}
        if not d:
            continue
        sr = p.get("seasonRecords") or []
        players.append({
            "p": pc, "n": d.get("name"), "t": d.get("teamCode"), "pos": d.get("position"), "no": n(d.get("backNumber")),
            "birth": d.get("birthDate"), "img": d.get("image") or "", "school": d.get("school") or "",
            "nat": d.get("nation") or "", "army": d.get("armyStatus") or "", "h": n(d.get("height")), "w": n(d.get("weight")),
            "hist": [str(x) for x in (p.get("history") or [])],
            "hon": [str(x) for x in ((p.get("honor") or {}).get("awards") or [])],
            "seasons": [[x.get("leagueDivision"), x.get("seasonDivision"), x.get("teamName"), n(x.get("gameCount")),
                         n(x.get("setCount")), n(x.get("point")), n(x.get("attackTotalSuccess")), n(x.get("blockingSetSuccess")),
                         n(x.get("serveSetSuccess")), n(x.get("setSuccess")), n(x.get("receiveSuccess")),
                         n(x.get("digSetSuccess")), n(x.get("error"))] for x in sr],
        })

    # 시상/기록
    aw = {}
    for sc, gd in raw["awards"].items():
        aw[sc] = {}
        for g, key in (("1", "M"), ("2", "W")):
            d = gd[g]
            aw[sc][key] = {
                "mvp": [[r.get("rank"), r.get("playerName"), r.get("teamName"), r.get("content"), r.get("itemName"), r.get("item2")] for r in (d.get("mvp") or [])],
                "triple": [[r.get("rank"), r.get("playerName"), r.get("teamName"), r.get("gdate"), n(r.get("point")), n(r.get("awSuc")), n(r.get("bbSuc")), n(r.get("vsuc"))] for r in ((d.get("triple") or {}).get("content") or [])],
                "achieve": [[r.get("rank"), r.get("season"), r.get("teamName"), r.get("awayName"), r.get("gameDate"), r.get("record"), n(r.get("totalRecord")), r.get("unit")] for r in ((d.get("achieve") or {}).get("content") or [])],
            }

    # 뉴스
    news = {"kovo": [], "press": [], "notice": []}
    for kind, items in raw["news"].items():
        out = []
        for it in items:
            title = ""
            for t in (it.get("titles") or []):
                if t.get("languageCode") == "ko":
                    title = t.get("title") or ""
                    break
            body = ""
            for b in (it.get("bodies") or []):
                if b.get("languageCode") == "ko":
                    body = b.get("body") or ""
                    break
            if not body and it.get("bodies"):
                body = it["bodies"][0].get("body") or ""
            if not title:
                title = clean_text(body)[:70]
            thumbs = [t.get("url") for t in (it.get("thumbnails") or []) if t.get("url")]
            images = thumbs + [u for u in imgs_from(body) if u.startswith("http")][:2]
            out.append({"i": it.get("id"), "d": (it.get("createdAt") or "")[:10], "t": title,
                        "x": clean_text(body)[:1500], "img": images[:1], "ty": kind})
        news[kind] = out

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

    data = {
        "v": "1.0.0",
        "gen": GEN,
        "seasons": seasons, "cupSeasons": cupSeasons, "futSeasons": futSeasons,
        "teams": teams,
        "std": std, "tstat": tstat, "pr": pr, "rk": rk, "sch": sch,
        "box": box, "bx": BX,
        "cup": cup, "fut": fut, "fbox": fbox,
        "players": players, "aw": aw,
        "news": news, "ext": packed_ext,
        "live": raw.get("live"),
        "meta": {
            "generated": GEN,
            "source": "KOVO 공식 API",
            "season_count": len(seasons),
            "team_count": len(set([r[1] for r in std.get("023", {}).get("M", [])] + [r[1] for r in std.get("023", {}).get("W", [])])),
            "player_count": len(players),
            "box_count": len(box),
            "fut_box_count": len(fbox),
            "news_count": sum(len(v) for v in news.values()),
            "ext_count": len((ext or {}).get("items", [])),
            "blocked": (ext or {}).get("blocked", []),
        },
    }
    return data

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
            "hc": x.get("hn") or "", "ac": x.get("an") or ""}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def chunks(data):
    core = {k: data[k] for k in ("v", "gen", "seasons", "cupSeasons", "futSeasons", "teams", "std", "tstat", "pr", "rk", "aw", "meta")}
    games = {k: data[k] for k in ("sch", "box", "bx", "cup", "fut", "fbox")}
    season = {k: data[k] for k in ("players",)}
    news = {k: data[k] for k in ("news", "ext")}
    live = {"live": data.get("live"), "gen": data["gen"]}
    return [("core", core), ("games", games), ("season", season), ("news", news), ("live_patch", live)]

def main():
    data = build()
    print("data keys", {k: (len(json.dumps(v, ensure_ascii=False)) if not isinstance(v, str) else len(v)) for k, v in data.items()})
    os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
    os.makedirs(os.path.join(REPO, "tools"), exist_ok=True)

    man = {"schema_version": 2, "app_version": "v1.0.0",
           "updated_at": GEN, "checked_at": GEN,
           "data_through": max([g["d"] for s in data["sch"].values() for g in s["M"] if g.get("d")] or [""]),
           "note": "KOVO 분석 스튜디오 앱이 맨 먼저 이 파일을 읽고 sha256 이 바뀐 청크만 내려받습니다. <id>.json(정본)과 window.KOVO_RECEIVE(...) 로 감싼 <id>.js 가 같은 내용입니다.",
           "chunks": []}
    for cid, body in chunks(data):
        jp = os.path.join(REPO, "data", cid + ".json")
        js = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        open(jp, "w", encoding="utf-8").write(js)
        open(os.path.join(REPO, "data", cid + ".js"), "w", encoding="utf-8").write(
            "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % js)
        man["chunks"].append({"id": cid, "path": "data/%s.json" % cid, "js": "data/%s.js" % cid,
                              "sha256": sha256_file(jp), "bytes": os.path.getsize(jp),
                              "updated_at": GEN, "globals": ["KOVO_DATA"]})
        print(" chunk", cid, man["chunks"][-1]["bytes"])
    open(os.path.join(REPO, "data", "manifest.json"), "w", encoding="utf-8").write(json.dumps(man, ensure_ascii=False, indent=1))
    open(os.path.join(REPO, "data", "manifest.js"), "w", encoding="utf-8").write(
        "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % json.dumps(man, ensure_ascii=False, separators=(",", ":")))

    # HTML
    css = open(os.path.join(TPL, "app.css"), encoding="utf-8").read()
    js = open(os.path.join(TPL, "app.js"), encoding="utf-8").read()
    html_tpl = open(os.path.join(TPL, "app.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out = html_tpl.replace("/*__CSS__*/", css).replace("/*__JS__*/", js).replace("/*__DATA__*/", payload)
    open(OUT_HTML, "w", encoding="utf-8").write(out)
    print("HTML", OUT_HTML, os.path.getsize(OUT_HTML), sha256_file(OUT_HTML))

if __name__ == "__main__":
    main()
