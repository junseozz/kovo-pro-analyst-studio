#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보조 소스 수집 — 구글뉴스 RSS(배구), KOVO 외 배구 소식. 실패는 정직하게 기록."""
import json, os, re, datetime, html, sys
import requests
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data", "external.json")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
     "Accept-Language": "ko-KR,ko;q=0.9"}

FEEDS = [
    ("프로배구", "https://news.google.com/rss/search?q=%ED%94%84%EB%A1%9C%EB%B0%B0%EA%B5%AC&hl=ko&gl=KR&ceid=KR:ko"),
    ("V-리그", "https://news.google.com/rss/search?q=V-%EB%A6%AC%EA%B7%B8+%EB%B0%B0%EA%B5%AC&hl=ko&gl=KR&ceid=KR:ko"),
    ("배구대표팀", "https://news.google.com/rss/search?q=%EB%B0%B0%EA%B5%AC+%EB%8C%80%ED%91%9C%ED%8C%80&hl=ko&gl=KR&ceid=KR:ko"),
]

def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(s).strip()

def main():
    out = {"fetched_at": datetime.datetime.now().isoformat(timespec="seconds"), "sources": [], "items": [], "blocked": []}
    seen = set()
    for name, url in FEEDS:
        try:
            r = requests.get(url, headers=H, timeout=25)
            root = ET.fromstring(r.content)
            n = 0
            for it in root.iter("item"):
                t = clean(it.findtext("title"))
                link = (it.findtext("link") or "").strip()
                pub = (it.findtext("pubDate") or "").strip()
                src = it.find("{*}source")
                key = t[:60]
                if not t or key in seen:
                    continue
                seen.add(key)
                out["items"].append({"t": t, "u": link, "d": pub, "s": clean(src.text if src is not None else ""), "f": name})
                n += 1
            out["sources"].append({"name": name, "status": r.status_code, "items": n})
        except Exception as e:
            out["blocked"].append({"name": name, "error": type(e).__name__ + ":" + str(e)[:120]})
    for name, url in [
        ("네이버 스포츠 배구", "https://api-gw.sports.naver.com/volleyball/schedule?category=volleyball&year=2026&month=11"),
        ("FIVB", "https://www.fivb.com/en/volleyball/calendar"),
        ("VolleyballWorld VNL", "https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/schedule/"),
    ]:
        try:
            r = requests.get(url, headers=H, timeout=15)
            out["blocked"].append({"name": name, "status": r.status_code, "note": "JS 렌더링/차단 — 스크립트 수집 불가" if r.status_code != 200 else "응답은 오나 데이터 미포함"})
        except Exception as e:
            out["blocked"].append({"name": name, "error": type(e).__name__ + ":" + str(e)[:80]})
    out["items"].sort(key=lambda x: x.get("d", ""), reverse=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("items", len(out["items"]), "sources", out["sources"], "blocked", len(out["blocked"]))

if __name__ == "__main__":
    main()
