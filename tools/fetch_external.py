#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보조 뉴스 수집 — 구글뉴스 RSS(배구 전 주제), 연합뉴스 스포츠 RSS, KOVO 자체 뉴스.
실패한 소스는 blocked 에 정직하게 기록한다. 추정/합성 기사 없음."""
import json, os, re, datetime, html, sys
import requests
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "external.json")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
     "Accept-Language": "ko-KR,ko;q=0.9"}

def gq(q):
    from urllib.parse import quote
    return "https://news.google.com/rss/search?q=" + quote(q) + "&hl=ko&gl=KR&ceid=KR:ko"

FEEDS = [
    ("배구", gq("배구")),
    ("프로배구", gq("프로배구")),
    ("V-리그", gq("V-리그 배구")),
    ("남자배구", gq("남자배구")),
    ("여자배구", gq("여자배구")),
    ("KOVO", gq("KOVO 배구")),
    ("배구대표팀", gq("배구 대표팀")),
    ("KOVO컵", gq("KOVO컵 배구")),
    ("연합뉴스 스포츠", "https://www.yna.co.kr/rss/sports.xml"),
]
VOLLEY = re.compile(r"배구|V-리그|V리그|KOVO|코보|세터|리베로|아웃사이드|미들블로커|흥국생명|대한항공|현대캐피탈|우리카드|KB손해|한국전력|OK저축|삼성화재|GS칼텍스|도로공사|현대건설|IBK|정관장|페퍼|SOOP")

def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def main():
    out = {"fetched_at": datetime.datetime.now().isoformat(timespec="seconds"), "sources": [], "items": [], "blocked": []}
    seen = set()
    for name, url in FEEDS:
        try:
            r = requests.get(url, headers=H, timeout=30)
            root = ET.fromstring(r.content)
            n = 0
            for it in root.iter("item"):
                t = clean(it.findtext("title"))
                link = (it.findtext("link") or "").strip()
                pub = (it.findtext("pubDate") or "").strip()
                desc = clean(it.findtext("description"))[:300]
                src = it.find("{*}source")
                srcname = clean(src.text if src is not None else "")
                if not t:
                    continue
                if name == "연합뉴스 스포츠" and not VOLLEY.search(t + " " + desc):
                    continue
                key = re.sub(r"\W", "", t)[:50]
                if key in seen:
                    continue
                seen.add(key)
                out["items"].append({"t": t, "u": link, "d": pub, "s": srcname or ("연합뉴스" if "연합" in name else name),
                                     "f": name, "x": desc})
                n += 1
            out["sources"].append({"name": name, "status": r.status_code, "items": n})
        except Exception as e:
            out["blocked"].append({"name": name, "error": type(e).__name__ + ":" + str(e)[:120]})
    # KOVO 자체 뉴스 더 깊게
    try:
        S = requests.Session(); S.headers.update({"Accept-Language": "ko-KR", "Origin": "https://kovo.co.kr",
                                                 "Referer": "https://kovo.co.kr/", "User-Agent": H["User-Agent"]})
        kn = []
        for path in ("/contents/news/kovo/news", "/contents/news/kovo/press", "/contents/news/notice"):
            for pg in range(4):
                j = S.get("https://user-api.kovo.co.kr" + path, params={"page": pg, "size": 30, "sort": "id,desc"}, timeout=30).json()
                pl = j.get("payload") or {}
                arr = pl.get("content") if isinstance(pl, dict) else []
                kn.extend(arr or [])
        json.dump(kn, open(os.path.join(HERE, "..", "data", "kovo_news_raw.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        out["sources"].append({"name": "KOVO 뉴스/보도/공지", "status": 200, "items": len(kn)})
    except Exception as e:
        out["blocked"].append({"name": "KOVO 뉴스", "error": type(e).__name__ + ":" + str(e)[:120]})

    def ts(x):
        try:
            return datetime.datetime.strptime(x["d"][:25].strip(), "%a, %d %b %Y %H:%M:%S").timestamp()
        except Exception:
            return 0
    out["items"].sort(key=ts, reverse=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("items", len(out["items"]), "sources", out["sources"], "blocked", len(out["blocked"]))
    print("최신", [(x["d"][:25], x["t"][:60]) for x in out["items"][:5]])

if __name__ == "__main__":
    main()
