#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현역 등록 로스터 정합성 수정 — repo 청크(core.json / season.json) 패치.

정본: KOVO 공식 API /teams/{tc}/players?seasonCode=023 (남녀부 14개 구단 288명, REGISTER)
로직: build_kovo.sync_current_roster() 한 곳에서만 구현한다(빌드와 동일 코드).
  · 선수 기록(player-records)에 섞여 오는 코칭스태프 행(등번호 100 이상) 제거
  · 코칭스태프 전용 인물은 선수 DB에서 제외
  · 등록 선수 소속·목록 기준을 로스터로 고정(개인 기록 0인 등록 선수도 노출)
사용: python3 tools/fix_roster.py [--apply]
"""
import json, os, re, sys, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)
from build_kovo import sync_current_roster  # noqa: E402

REPO_DATA = os.path.join(BASE, "repo", "data")
LIVE = os.path.join(BASE, "data", "roster023_live.json")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def main():
    apply = "--apply" in sys.argv
    core = load(os.path.join(REPO_DATA, "core.json"))
    season = load(os.path.join(REPO_DATA, "season.json"))
    live = load(LIVE)

    # ── 공식 로스터(정본) 확인 ───────────────────────────────────────
    off_team_of, off_by_team = {}, {}
    for tc, arr in live.items():
        codes = [str(p["playerCode"]) for p in arr if p.get("playerCode")]
        off_by_team[tc] = codes
        for pc in codes:
            off_team_of[pc] = tc
    official = set(off_team_of)
    print("공식 등록", len(official), "명 · 구단", len(off_by_team))
    assert set(core["roster"]) == official, "repo roster 가 공식 API 와 불일치"
    for g, mp in core["rosterTeams"].items():
        for tc, arr in mp.items():
            assert sorted(arr) == sorted(off_by_team[tc]), ("rosterTeams 불일치", tc)

    # ── 동일 로직 적용 (core+season 병합 뷰) ─────────────────────────
    data = dict(core)
    data["players"] = season["players"]
    data["v"] = "2.2.0"
    stats = sync_current_roster(data)
    print("적용 결과", stats)

    # ── 검증: 등록 선수 소속·존재 ────────────────────────────────────
    P = {str(p["p"]): p for p in data["players"]}
    bad = [(pc, P.get(pc, {}).get("t"), tc) for pc, tc in off_team_of.items()
           if P.get(pc, {}).get("t") != tc]
    missing = official - set(P)
    print("소속 불일치", len(bad), bad[:5], "· 누락", len(missing), sorted(missing)[:5])
    assert not bad and not missing
    banned = {"0001556": "전병선", "0001476": "송희채"}
    for pc, nm in banned.items():
        p = P.get(pc)
        print("  ", nm, pc, "→", ("등록" if pc in official else "미등록"), p and p["st"],
              "seasons 최신:", p and (p["seasons"][0] if p["seasons"] else None))

    if not apply:
        print("[DRY RUN] --apply 로 저장")
        return

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    core_out = {k: v for k, v in data.items() if k != "players"}
    for cid, body in (("core", core_out), ("season", {"players": data["players"]})):
        jp = os.path.join(REPO_DATA, cid + ".json")
        js = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        open(jp, "w", encoding="utf-8").write(js)
        open(os.path.join(REPO_DATA, cid + ".js"), "w", encoding="utf-8").write(
            "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % js)
        print("saved", jp, os.path.getsize(jp))

    man = load(os.path.join(REPO_DATA, "manifest.json"))
    for c in man.get("chunks", []):
        if c["id"] in ("core", "season"):
            jp = os.path.join(REPO_DATA, c["id"] + ".json")
            b = open(jp, "rb").read()
            c["sha256"] = hashlib.sha256(b).hexdigest()
            c["bytes"] = len(b)
            c["updated_at"] = now
    man["updated_at"] = now
    man["checked_at"] = now
    man["app_version"] = "2.2.0"
    man["player_count"] = len(data["players"])
    man["roster_count"] = len(official)
    json.dump(man, open(os.path.join(REPO_DATA, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("manifest updated_at", man["updated_at"])


if __name__ == "__main__":
    main()
