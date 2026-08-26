#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick — 发布前门禁校验

检查项：
- 事件总数 > 0
- meta.count == len(EVENTS)
- 每条 cover 要么 real/{id}.jpg（且物理文件存在 >=2000 字节），要么 http(s):// 远程，
  不允许 data:image / 空串
- window.SITE_UPDATED 存在且为本日

任一项失败以非零退出，让 workflow 标红告警（但默认仍推送，避免每日断更）。
"""
import json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "js", "data.js")
META_PATH = os.path.join(ROOT, "js", "meta.js")
REAL_DIR = os.path.join(ROOT, "img", "real")

errs = []


def load_events():
    raw = open(DATA_PATH, encoding="utf-8").read()
    m = re.search(r'window\.EVENTS\s*=\s*(\[.*\]);', raw, re.S)
    return json.loads(m.group(1))


def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    raw = open(DATA_PATH, encoding="utf-8").read()
    m = re.search(r'window\.EVENTS\s*=\s*(\[.*\]);', raw, re.S)
    if not m:
        errs.append("无法解析 window.EVENTS")
        return 1
    events = json.loads(m.group(1))
    if len(events) == 0:
        errs.append("事件总数为 0")
        return 1

    # meta.count 一致性
    if os.path.exists(META_PATH):
        mt = open(META_PATH, encoding="utf-8").read()
        mm = re.search(r'SITE_META\s*=\s*(\{[^}]*\})', mt)
        if mm:
            meta = json.loads(mm.group(1))
            if meta.get("count") != len(events):
                errs.append("meta.count(%s) != len(EVENTS)(%s)"
                            % (meta.get("count"), len(events)))

    # SITE_UPDATED
    su = re.search(r'window\.SITE_UPDATED\s*=\s*"([^"]*)"', raw)
    if not su:
        errs.append("缺少 window.SITE_UPDATED")
    elif not su.group(1).startswith(today):
        errs.append("SITE_UPDATED(%s) 非本日(%s)" % (su.group(1), today))

    # cover 门禁
    base64_n = none_n = broken_n = 0
    for e in events:
        cov = e.get("cover", "")
        if cov.startswith("data:image"):
            base64_n += 1
        elif not cov:
            none_n += 1
        elif cov.startswith("http://") or cov.startswith("https://"):
            pass  # 远程图，放行
        elif cov.startswith("real/"):
            p = os.path.join(REAL_DIR, cov[len("real/"):])
            if not (os.path.exists(p) and os.path.getsize(p) >= 2000):
                broken_n += 1
        else:
            none_n += 1
    if base64_n:
        errs.append("存在 %d 张 base64 占位图" % base64_n)
    if none_n:
        errs.append("存在 %d 张空封面" % none_n)
    if broken_n:
        errs.append("存在 %d 张损坏/缺失封面" % broken_n)

    if errs:
        print("VALIDATE FAILED:")
        for x in errs:
            print("  -", x)
        return 1
    print("VALIDATE OK: events=%d 门禁全通过（0 base64 / 0 none / 0 broken）" % len(events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
