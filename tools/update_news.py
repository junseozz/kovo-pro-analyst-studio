#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""배구 뉴스 자동 갱신기 — data/news.json 을 최신 기사로 갱신한다.
소스: 구글 뉴스 RSS(배구·프로배구·V-리그·남자배구·여자배구·KOVO·대표팀·KOVO컵), 연합뉴스 스포츠,
      KOVO 공식 뉴스/보도자료/공지 API.
- 추정/합성 기사 0건. 실제 RSS/API 응답만 저장한다.
- 실행: python3 tools/update_news.py
"""
import json, os, re, html, datetime, hashlib, sys
from urllib.parse import quote
from xml.etree import ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
NEWS = os.path.join(DATA, "news.json")
MAN = os.path.join(DATA, "manifest.json")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
     "Accept-Language": "ko-KR,ko;q=0.9"}
KOVO = "https://user-api.kovo.co.kr"

FEEDS = [
    ("배구", "https://news.google.com/rss/search?q=" + quote("배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("프로배구", "https://news.google.com/rss/search?q=" + quote("프로배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("V-리그", "https://news.google.com/rss/search?q=" + quote("V-리그 배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("남자배구", "https://news.google.com/rss/search?q=" + quote("남자배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("여자배구", "https://news.google.com/rss/search?q=" + quote("여자배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("KOVO", "https://news.google.com/rss/search?q=" + quote("KOVO 배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("배구대표팀", "https://news.google.com/rss/search?q=" + quote("배구 대표팀") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("KOVO컵", "https://news.google.com/rss/search?q=" + quote("KOVO컵 배구") + "&hl=ko&gl=KR&ceid=KR:ko"),
    ("연합뉴스", "https://www.yna.co.kr/rss/sports.xml"),
]
VOLLEY = re.compile(r"배구|V-리그|V리그|KOVO|코보|흥국생명|대한항공|현대캐피탈|우리카드|KB손해|한국전력|OK저축|삼성화재|GS칼텍스|도로공사|현대건설|IBK|정관장|페퍼|SOOP")


def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def fetch_ext():
    out, sources, blocked = [], [], []
    seen = set()
    for name, url in FEEDS:
        try:
            r = requests.get(url, headers=H, timeout=25)
            root = ET.fromstring(r.content)
            n = 0
            for it in root.iter("item"):
                t = clean(it.findtext("title"))
                if not t:
                    continue
                desc = clean(it.findtext("description"))[:300]
                if name == "연합뉴스" and not VOLLEY.search(t + " " + desc):
                    continue
                key = re.sub(r"\W", "", t)[:50]
                if key in seen:
                    continue
                seen.add(key)
                src = it.find("{*}source")
                pub = (it.findtext("pubDate") or "").strip()
                out.append({"t": t, "u": (it.findtext("link") or "").strip(), "d": pub,
                            "s": clean(src.text if src is not None else "") or ("연합뉴스" if name == "연합뉴스" else name),
                            "f": name, "x": desc})
                n += 1
            sources.append({"name": name, "status": r.status_code, "items": n})
        except Exception as e:
            blocked.append({"name": name, "error": type(e).__name__ + ":" + str(e)[:100]})
    return out, sources, blocked


def fetch_kovo():
    S = requests.Session(); S.headers.update({"Accept-Language": "ko-KR", "Origin": "https://kovo.co.kr",
                                             "Referer": "https://kovo.co.kr/", "User-Agent": H["User-Agent"]})
    news = {"kovo": [], "press": [], "notice": []}
    for kind, path in (("kovo", "/contents/news/kovo/news"), ("press", "/contents/news/kovo/press"), ("notice", "/contents/news/notice")):
        for pg in range(3):
            try:
                j = S.get(KOVO + path, params={"page": pg, "size": 30, "sort": "id,desc"}, timeout=25).json()
                arr = (j.get("payload") or {}).get("content") or []
            except Exception:
                arr = []
            for it in arr:
                title = ""
                for t in (it.get("titles") or []):
                    if t.get("languageCode") == "ko":
                        title = t.get("title") or ""; break
                body = ""
                for b in (it.get("bodies") or []):
                    if b.get("languageCode") == "ko":
                        body = b.get("body") or ""; break
                news[kind].append({"i": it.get("id"), "d": (it.get("createdAt") or "")[:10], "t": title or clean(body)[:70],
                                   "x": clean(body)[:1500], "img": [t.get("url") for t in (it.get("thumbnails") or []) if t.get("url")][:1], "ty": kind})
    for k in news:
        news[k].sort(key=lambda x: (x.get("d") or ""), reverse=True)
    return news


def main():
    cur = json.load(open(NEWS, encoding="utf-8")) if os.path.exists(NEWS) else {"news": {"kovo": [], "press": [], "notice": []}, "ext": []}
    ext, sources, blocked = fetch_ext()
    # 기존 항목 + 신규 → URL/제목 중복 제거, 최신순 600건
    merged, seen = [], set()
    for it in ext + (cur.get("ext") or []):
        key = (it.get("u") or "") or re.sub(r"\W", "", it.get("t", ""))[:50]
        if key in seen:
            continue
        seen.add(key)
        merged.append(it)

    def ts(x):
        try:
            return datetime.datetime.strptime((x.get("d") or "")[:25].strip(), "%a, %d %b %Y %H:%M:%S").timestamp()
        except Exception:
            return 0
    merged.sort(key=ts, reverse=True)
    cur["ext"] = merged[:600]
    kn = fetch_kovo()
    for k in kn:
        if kn[k]:
            cur.setdefault("news", {})[k] = kn[k]
    body = json.dumps(cur, ensure_ascii=False, separators=(",", ":"))
    open(NEWS, "w", encoding="utf-8").write(body)
    open(os.path.join(DATA, "news.js"), "w", encoding="utf-8").write("window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % body)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    h = hashlib.sha256(body.encode()).hexdigest()
    man = json.load(open(MAN, encoding="utf-8"))
    for c in man["chunks"]:
        if c["id"] == "news":
            c["bytes"] = len(body.encode()); c["sha256"] = h; c["updated_at"] = now
    man["updated_at"] = now; man["checked_at"] = now
    json.dump(man, open(MAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(DATA, "manifest.js"), "w", encoding="utf-8").write(
        "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % json.dumps(man, ensure_ascii=False, separators=(",", ":")))
    print("ext", len(cur["ext"]), "kovo", {k: len(v) for k, v in cur["news"].items()}, "sources", sources, "blocked", blocked)
    print("최신", cur["ext"][0]["d"] if cur["ext"] else "-", (cur["ext"][0]["t"][:70] if cur["ext"] else ""))


if __name__ == "__main__":
    main()
