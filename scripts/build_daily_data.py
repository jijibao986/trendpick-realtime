#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 data.js 每日自动生成（每日 8:00 由 automation 触发）
从 realtime.js 当前事件按 buzzIndex+stars 取前 30 条，写入 js/data.js。
每事件含 description 模板字段（含来源数/热度/印花建议/风险/跨境溢价）。
"""
import json, datetime, hashlib, os, sys

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


def main():
    if not os.path.exists(RT_PATH):
        print("ERROR: %s 不存在" % RT_PATH, file=sys.stderr)
        sys.exit(1)
    raw = open(RT_PATH, encoding="utf-8").read()
    s, e = raw.index("["), raw.rindex("]")
    rt = json.loads(raw[s:e + 1])

    rt_sorted = sorted(rt, key=lambda x: (x.get("buzzIndex", 0), star_count(x.get("stars"))), reverse=True)
    cand = rt_sorted[:30]

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = ['window.SITE_UPDATED = "%s";' % now, "window.EVENTS = ["]
    for i, ev in enumerate(cand):
        title = (ev.get("titleCn") or ev.get("titleOrig") or "").strip()
        if not title:
            continue
        eid = hashlib.md5(title.encode("utf-8")).hexdigest()[:24]
        ne = {
            "id": eid,
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
        sep = "," if i < len(cand) - 1 else ""
        lines.append("  " + json.dumps(ne, ensure_ascii=False) + sep)
    lines.append("];")
    open(DATA_PATH, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("OK: %d events -> %s" % (len(cand), DATA_PATH))


if __name__ == "__main__":
    main()