#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick — 合并云端研究事件到 data.js

- 读 fresh/cloud_events_YYYY-MM-DD.json（cloud_curated.py 产出）
- 按 titleCn(lower) 与 id 去重，跳过 data.js 已有事件
- 追加进 data.js，更新 window.SITE_UPDATED
- 空数组时（研究全失败）不追加，但仍推进 SITE_UPDATED（沿用版兜底）

载入/写出范式与 scripts/build_daily_data.py 保持一致，避免破坏 data.js 格式。
"""
import json, os, re, sys, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRESH_DIR = os.path.join(ROOT, "fresh")
DATA_PATH = os.path.join(ROOT, "js", "data.js")

CAT_MAP = {
    "明星八卦": "celebrity", "演唱会综艺": "concert_show", "音乐热歌": "celebrity",
    "影视剧": "film_tv", "动漫": "film_tv", "游戏电竞": "gaming", "网络热梗": "meme",
    "社会民生": "society", "体育": "sports", "政治": "politics", "电商政策": "ecommerce",
    "平台热搜": "platform_search", "其他热搜": "other", "节日": "society",
}
ENUM = (set(CAT_MAP.values()) |
        {"celebrity", "concert_show", "film_tv", "gaming", "meme",
         "other", "society", "sports", "politics", "ecommerce", "platform_search"})


def load_existing():
    if not os.path.exists(DATA_PATH):
        return []
    raw = open(DATA_PATH, encoding="utf-8").read()
    m = re.search(r'window\.EVENTS\s*=\s*(\[.*\]);', raw, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []


def latest_cloud_json():
    files = glob.glob(os.path.join(FRESH_DIR, "cloud_events_*.json"))
    if not files:
        return None
    # 取文件名日期最大者
    files.sort(reverse=True)
    return files[0]


def main():
    existing = load_existing()
    seen_titles = {e.get("titleCn", "").strip().lower() for e in existing}
    seen_ids = {e.get("id") for e in existing}

    path = latest_cloud_json()
    if not path:
        print("WARN: 未找到 cloud_events_*.json，沿用既有数据")
        cloud = []
    else:
        try:
            cloud = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            print("WARN: 读取 %s 失败: %s" % (path, e))
            cloud = []

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    added = 0
    for ev in cloud:
        # 规范化 cat
        cat = ev.get("cat")
        if cat not in ENUM:
            cat = CAT_MAP.get(ev.get("catCn"), "other")
        ev["cat"] = cat
        title = (ev.get("titleCn") or ev.get("titleOrig") or "").strip()
        if not title:
            continue
        if title.lower() in seen_titles:
            continue
        eid = ev.get("id") or hashlib_md5(title)
        if eid in seen_ids:
            continue
        # 确保必要字段
        ev["id"] = eid
        ev.setdefault("batch", "cloud-" + now[:10])
        ev.setdefault("fresh", True)
        ev.setdefault("cover", "")
        ev.setdefault("coverType", "")
        ev.setdefault("hasMedia", False)
        ev.setdefault("media", [])
        existing.append(ev)
        seen_titles.add(title.lower())
        seen_ids.add(eid)
        added += 1

    lines = ['window.SITE_UPDATED = "%s";' % now, "window.EVENTS = ["]
    for i, ev in enumerate(existing):
        sep = "," if i < len(existing) - 1 else ""
        lines.append("  " + json.dumps(ev, ensure_ascii=False) + sep)
    lines.append("];")
    open(DATA_PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    print("OK: cloud merged +%d -> total %d events (carried=%s)"
          % (added, len(existing), len(cloud) == 0))
    sys.exit(0)


def hashlib_md5(s):
    import hashlib
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:24]


if __name__ == "__main__":
    main()
