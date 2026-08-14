# -*- coding: utf-8 -*-
"""v2_fix_fields.py — 把 fresh 事件字段对齐到 app.js 实际读取的 v2 契约。
问题：daily/平台合并时用了 summaryCn(模板读 summary)、sourceBreadth=数字、sources 缺 type/region/credibility、hotDays 为字符串。
结果卡片标题在、但描述/来源/热度全空白，看起来像“空分类”。
本脚本补齐这些字段，使卡片信息完整。
"""
import json, os, re
from datetime import date

DATA_JS = os.path.join(os.path.dirname(__file__), "data.js")
TODAY = date(2026, 8, 12)

def load():
    raw = open(DATA_JS, encoding="utf-8").read()
    i = raw.index("[")
    arr, _ = json.JSONDecoder().raw_decode(raw, i)
    return arr

def save(arr):
    raw = open(DATA_JS, encoding="utf-8").read()
    pre = raw[:raw.index("window.EVENTS")]
    out = pre + "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
    tmp = DATA_JS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, DATA_JS)

def parse_date(s):
    if not isinstance(s, str):
        return None
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    return None

def norm_hotdays(e):
    hd = e.get("hotDays")
    if isinstance(hd, int) and 0 < hd <= 400:
        return hd
    # try future date from timeline
    best = None
    for n in (e.get("timeline") or []):
        d = parse_date(n.get("date", ""))
        if d and d >= TODAY:
            best = d if (best is None or d > best) else best
    if best:
        return max(1, (best - TODAY).days)
    d = parse_date(hd)
    if d:
        return max(1, (d - TODAY).days) if d >= TODAY else 30
    # "持续" / 其他
    return 30

def norm_sources(e):
    srcs = e.get("sources") or []
    country = e.get("country")
    region_default = country if country in ("th", "my") else "global"
    out = []
    for s in srcs:
        if not isinstance(s, dict):
            continue
        name = s.get("name", "来源")
        # type
        t = s.get("type")
        if not t:
            low = name.lower()
            if any(k in low for k in ["shop", "seller", "center", "official", "lazada", "shopee", "tiktok"]):
                t = "official"
            elif any(k in low for k in ["twitter", "tiktok", "x.com", "ig", "insta", "facebook", "reddit"]):
                t = "social"
            else:
                t = "news"
        # region
        r = s.get("region")
        if not r:
            r = region_default
        # credibility
        c = s.get("credibility")
        if not c:
            c = "高" if t == "official" else "中"
        out.append({"name": name, "url": s.get("url", ""), "type": t, "region": r, "credibility": c})
    if not out:
        out = [{"name": "公开报道", "url": "", "type": "news", "region": "global", "credibility": "中"}]
    return out

def norm_source_breadth(e, srcs):
    sb = e.get("sourceBreadth")
    if isinstance(sb, dict) and "local" in sb:
        return sb
    local = sum(1 for s in srcs if s.get("region") == "local")
    global_c = sum(1 for s in srcs if s.get("region") == "global")
    social_only = sum(1 for s in srcs if s.get("type") == "social" and s.get("region") == "global")
    if local == global_c == social_only == 0:
        global_c = len(srcs)
    return {"local": local, "global": global_c, "social_only": social_only}

def build_summary(e):
    sc = e.get("summaryCn") or e.get("summary")
    if sc and str(sc).strip():
        return str(sc).strip()
    # generate from available fields
    title = e.get("titleCn", "")
    tags = "、".join(e.get("tags", []) or [])
    pt = e.get("printType", "")
    stars = e.get("stars", 0)
    country = "🇹🇭泰国" if e.get("country") == "th" else "🇲🇾马来" if e.get("country") == "my" else "多市场"
    base = f"{title}：基于{country}市场热度，印花指数★{stars}，建议以「{pt}」形式开发。"
    if tags:
        base += f" 关联标签：{tags}。"
    return base

def norm_timeline(e):
    tl = e.get("timeline") or []
    if tl:
        return tl
    return [{
        "date": "2026-08-12",
        "label": "入选今日热点日报",
        "desc": (e.get("summaryCn") or e.get("titleCn") or "")[:40],
        "verified": False,
    }]

def main():
    arr = load()
    n = 0
    for e in arr:
        if not e.get("fresh"):
            continue
        n += 1
        # summary
        e["summary"] = build_summary(e)
        # titleOrig
        e["titleOrig"] = e.get("titleEn") or e.get("titleTh") or e.get("titleCn") or ""
        # sources + breadth
        srcs = norm_sources(e)
        e["sources"] = srcs
        e["sourceBreadth"] = norm_source_breadth(e, srcs)
        # hotDays
        e["hotDays"] = norm_hotdays(e)
        # timeline
        e["timeline"] = norm_timeline(e)
        # schema parity (harmless extras app.js may read)
        e["cat"] = e.get("catCn")
        e["description"] = e["summary"]
        e["timeAbs"] = "2026-08-12"
        e["timeRel"] = "今日"
        # drop legacy summaryCn to avoid confusion (keep summary as canonical)
        if "summaryCn" in e:
            del e["summaryCn"]
    # unblock the 2 old sensitive events per user request (no blocking at all)
    unblocked = 0
    for e in arr:
        if e.get("sensitive"):
            e["sensitive"] = False
            unblocked += 1
    save(arr)
    print(f"normalized fresh events: {n}")
    print(f"unblocked sensitive events: {unblocked}")
    # gate + field check
    b64 = sum(1 for e in arr if str(e.get("cover", "")).startswith("data:image"))
    broken = 0
    for e in arr:
        cov = e.get("cover", "")
        if cov.startswith("real/"):
            p = os.path.join(os.path.dirname(DATA_JS), "..", "img", "real", os.path.basename(cov))
            if not os.path.exists(p) or os.path.getsize(p) < 2000:
                broken += 1
    missing_summary = sum(1 for e in arr if not str(e.get("summary", "")).strip())
    bad_sb = sum(1 for e in arr if not (isinstance(e.get("sourceBreadth"), dict) and "local" in e.get("sourceBreadth")))
    bad_src = sum(1 for e in arr for s in e.get("sources", []) if "type" not in s or "region" not in s or "credibility" not in s)
    print(f"TOTAL: {len(arr)} | base64: {b64} | broken covers: {broken}")
    print(f"missing summary: {missing_summary} | bad sourceBreadth: {bad_sb} | sources missing subfields: {bad_src}")

if __name__ == "__main__":
    main()
