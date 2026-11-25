#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/manifest.json 검증기.
- 모든 청크의 존재·바이트·sha256 을 manifest 와 대조한다.
- --fix: .json 정본을 기준으로 .js 래퍼와 manifest 의 sha256/bytes/updated_at 을 다시 쓴다.
사용: python3 tools/verify_manifest.py [--fix]
"""
import json, os, sys, hashlib, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
MAN = os.path.join(DATA, "manifest.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    fix = "--fix" in sys.argv
    man = json.load(open(MAN, encoding="utf-8"))
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    bad, fixed = [], []
    for c in man.get("chunks", []):
        jp = os.path.join(DATA, c["id"] + ".json")
        jsp = os.path.join(DATA, c["id"] + ".js")
        if not os.path.exists(jp):
            bad.append((c["id"], "missing json"))
            continue
        size = os.path.getsize(jp)
        h = sha(jp)
        issues = []
        if c.get("bytes") != size:
            issues.append("bytes %s→%s" % (c.get("bytes"), size))
        if c.get("sha256") != h:
            issues.append("sha256")
        body = open(jp, encoding="utf-8").read()
        js = "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % body
        if not os.path.exists(jsp) or open(jsp, encoding="utf-8").read() != js:
            issues.append("js wrapper")
        if issues:
            bad.append((c["id"], ", ".join(issues)))
        if fix:
            open(jsp, "w", encoding="utf-8").write(js)
            changed = c.get("sha256") != h or c.get("bytes") != size
            c["bytes"] = size
            c["sha256"] = h
            if changed or not c.get("updated_at"):
                c["updated_at"] = now
            fixed.append(c["id"])
    if fix:
        man["updated_at"] = max([c.get("updated_at") or "" for c in man.get("chunks", [])] or [now])
        man["checked_at"] = now
        json.dump(man, open(MAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        js = "window.KOVO_RECEIVE&&window.KOVO_RECEIVE(%s);" % json.dumps(man, ensure_ascii=False, separators=(",", ":"))
        open(os.path.join(DATA, "manifest.js"), "w", encoding="utf-8").write(js)
    print("chunks", len(man.get("chunks", [])), "issues", len(bad), "fixed", len(fixed))
    for b in bad:
        print("  -", b[0], b[1])
    print("OK" if not bad else "NEEDS FIX")
    return 0 if (not bad or fix) else 1


if __name__ == "__main__":
    sys.exit(main())
