#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick — 写 js/meta.js（前端轻量轮询检测更新用）

格式（单行合法 JSON，前端用正则 { ... } 解析）：
  window.SITE_META = {"updated": "...", "count": N, "carried": bool};

carried 取自 fresh/cloud_status.json：研究全失败当天为 true（沿用版）。
"""
import json, os, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "js", "data.js")
META_PATH = os.path.join(ROOT, "js", "meta.js")
STATUS_PATH = os.path.join(ROOT, "fresh", "cloud_status.json")


def load_count():
    if not os.path.exists(DATA_PATH):
        return 0
    raw = open(DATA_PATH, encoding="utf-8").read()
    m = re.search(r'window\.EVENTS\s*=\s*(\[.*\]);', raw, re.S)
    if not m:
        return 0
    try:
        return len(json.loads(m.group(1)))
    except Exception:
        return 0


def main():
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    count = load_count()
    carried = False
    if os.path.exists(STATUS_PATH):
        try:
            st = json.load(open(STATUS_PATH, encoding="utf-8"))
            carried = bool(st.get("carried"))
        except Exception:
            pass
    with open(META_PATH, "w", encoding="utf-8") as f:
        f.write('window.SITE_META = {"updated": "%s", "count": %d, "carried": %s};\n'
                % (now, count, "true" if carried else "false"))
    print("OK: meta.js -> updated=%s count=%d carried=%s" % (now, count, carried))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
