#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 data.js 每日自动生成（每日 8:00 由 automation 触发）

v2 升级后改为【合并】模式：
- 保留 site/js/data.js（即本地 site/ 同步过来的「印选 v2 每日热点」全量 curated 事件）不动；
- 仅把 realtime.js 当前按 buzzIndex+stars 取前 30 条作为「实时层」补充追加进 data.js（去重，不覆盖 curated 事件）；
- 更新 SITE_UPDATED 与 meta.js 的 count，使前端感知到更新。

这样每日本地自动化同步的 curated 事件不会被云端实时管线覆盖掉。
"""
import json, datetime, hashlib, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RT_PATH = os.path.join(ROOT, 'realtime.js')
DATA_PATH = os.path.join(ROOT, 'js', 'data.js')

REGION = {"th": "泰国", "my": "马来西亚", "multi": "多市场"}


def star_count(s):
    if isinstance(s, int):
        return max(0, min(5, s))
    return max(0, min(5, str(s or "").count("🔥")))


def mk_desc(e):
    cn = e.get("titleCn") or e.get("titleOrig", "")
    cat = e.get("catCn", "")
    summary = e.get("summary", "")
    src_n = len(e.get("sources", []))
    hot = e.get("hotDays", 1)
    sn = star_count(e.get("stars"))
    buzz = e.get("buzzIndex", 70)
    risk = e.get("risk", "中")
    pt = e.get("printType", "文字款")
    local = e.get("localFlag", False)
    country = e.get("country", "th")
    region = REGION.get(country, "多市场")
    risk_advice = {"低": "风险较低，可放心开发", "中": "风险中等，建议评估", "高": "高风险，谨慎开发"}.get(risk, "建议评估风险")
    local_note = "该热点具有泰马本地媒体来源支撑" if local else "全球多源交叉验证"
    return (
        f"{cn}是近期{region}{cat}热门话题。"
        f"{summary}本条热点汇聚了{src_n}个数据来源交叉验证。"
        f"事件持续{hot}天，当前热度{'★' * sn}级（buzz {buzz}分）。"
        f"建议采用{pt}，{risk_advice}。"
        f"{local_note}，跨境印花溢价潜力较高。"
    )


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


def main():
    if not os.path.exists(RT_PATH):
        print("ERROR: %s 不存在" % RT_PATH, file=sys.stderr)
        sys.exit(1)

    existing = load_existing()
    seen_titles = {e.get("titleCn", "").strip().lower() for e in existing}
    seen_ids = {e.get("id") for e in existing}

    raw = open(RT_PATH, encoding="utf-8").read()
    s, e = raw.index("["), raw.rindex("]")
    rt = json.loads(raw[s:e + 1])

    rt_sorted = sorted(rt, key=lambda x: (x.get("buzzIndex", 0), star_count(x.get("stars"))), reverse=True)
    cand = rt_sorted[:30]

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    added = 0
    for ev in cand:
        title = (ev.get("titleCn") or ev.get("titleOrig") or "").strip()
        if not title:
            continue
        if title.lower() in seen_titles:
            continue
        eid = hashlib.md5(title.encode("utf-8")).hexdigest()[:24]
        if eid in seen_ids:
            continue
        ne = {
            "id": eid,
            "batch": "realtime",
            "fresh": True,
            "country": ev.get("country", "th"),
            "cat": ev.get("cat", "other"),
            "catCn": ev.get("catCn", "其他热搜"),
            "stars": star_count(ev.get("stars")),
            "printType": ev.get("printType", "文字款"),
            "risk": ev.get("risk", "中"),
            "hotDays": ev.get("hotDays", 1),
            "titleCn": ev.get("titleCn", ""),
            "titleOrig": ev.get("titleOrig", ""),
            "summary": ev.get("summary", ""),
            "description": mk_desc(ev),
            "timeRel": ev.get("timeRel", ""),
            "timeAbs": ev.get("timeAbs", now[:10]),
            "tags": ev.get("tags", []),
            "sensitive": ev.get("sensitive", False),
            "sources": ev.get("sources", []),
            "credibilityScore": ev.get("credibilityScore", 70),
            "buzzIndex": ev.get("buzzIndex", 70),
            "timeline": ev.get("timeline", []),
            "timezoneNote": "UTC+8",
            "media": ev.get("media", []),
            "cover": ev.get("cover", ""),
            "coverType": ev.get("coverType", "remote"),
            "hasMedia": bool(ev.get("cover")),
            "imageSource": ev.get("imageSource", ""),
            "primaryUrl": ev.get("primaryUrl", ""),
            "localFlag": ev.get("localFlag", False),
            "sourceBreadth": ev.get("sourceBreadth", {"local": False, "global": True, "social_only": False}),
            "sourceCount": len(ev.get("sources", [])),
        }
        existing.append(ne)
        seen_titles.add(title.lower())
        seen_ids.add(eid)
        added += 1

    lines = ['window.SITE_UPDATED = "%s";' % now, "window.EVENTS = ["]
    for i, ev in enumerate(existing):
        sep = "," if i < len(existing) - 1 else ""
        lines.append("  " + json.dumps(ev, ensure_ascii=False) + sep)
    lines.append("];")
    open(DATA_PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    meta_path = os.path.join(ROOT, "js", "meta.js")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write('window.SITE_META = {"updated": "%s", "count": %d};\n' % (now, len(existing)))
    print("OK: merged +%d realtime -> total %d events ; meta -> %s" % (added, len(existing), meta_path))


if __name__ == "__main__":
    main()
