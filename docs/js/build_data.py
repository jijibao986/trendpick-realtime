# -*- coding: utf-8 -*-
"""把 TrendTee 抓取结果 events.json 转为前端数据集 data.js。
用法:
  python build_data.py                       # 自动找今天/最近一次抓取
  python build_data.py --src /path/events.json --out /path/data.js
"""
import json, re, os, sys, argparse, glob, time
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .../automation-claw-.../
MEM = os.path.join(ROOT, ".workbuddy", "memory")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "data.js")

# sensitive categories to flag (royalty / politics / religion) — per red-line policy
SENSITIVE_CATS = {"政党选举"}  # politics
SENSITIVE_KW = ["王室", "国王", "王后", "公主", "王子", "太后", "พระราช", "ในหลวง",
                "清真", "佛", "寺", "僧", "伊斯兰教", "基督", "มัสยิด", "วัด", "พระสงฆ์",
                "苏丹", "最高元首", "杨", "陛下"]

def is_sensitive(e):
    if e.get("cat_cn") in SENSITIVE_CATS:
        return True
    blob = (e.get("title_cn", "") + " " + e.get("title_orig", "") + " " + e.get("summary", ""))
    for kw in SENSITIVE_KW:
        if kw in blob:
            return True
    return False

def find_latest_src():
    # 今天优先，否则最近的 _tmp_YYYYMMDD
    ymd = time.strftime("%Y%m%d")
    cand = os.path.join(MEM, "_tmp_" + ymd, "events.json")
    if os.path.exists(cand):
        return cand
    dirs = sorted(glob.glob(os.path.join(MEM, "_tmp_*")), reverse=True)
    for d in dirs:
        p = os.path.join(d, "events.json")
        if os.path.exists(p):
            return p
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="events.json 路径（默认今天/最近一次抓取）")
    ap.add_argument("--out", help="data.js 输出路径（默认 site/js/data.js）")
    args = ap.parse_args()

    src = args.src or find_latest_src()
    out = args.out or DEFAULT_OUT
    if not src or not os.path.exists(src):
        sys.stderr.write("ERROR: 找不到 events.json，请先运行 scrape_tangyole.py\n")
        sys.exit(2)
    ev = json.load(open(src, encoding="utf-8"))

    seen = {}
    for e in ev:
        u = e.get("url")
        if not u:
            continue
        if u not in seen or (e.get("stars") or 0) > (seen[u].get("stars") or 0):
            seen[u] = e

    out_list = []
    for e in seen.values():
        uid = e["url"].rstrip("/").split("/")[-1]
        rec = {
            "id": uid,
            "country": "th" if e.get("country") == "th" or "/th/" in e.get("url", "") else "my",
            "cat": e.get("cat"),
            "catCn": e.get("cat_cn") or e.get("cat_label"),
            "stars": e.get("stars") or 1,
            "printType": e.get("print_type") or "图案款",
            "risk": e.get("risk") or "未标注",
            "hotDays": e.get("hot_days") or 0,
            "titleCn": e.get("title_cn") or "",
            "titleOrig": e.get("title_orig") or "",
            "summary": e.get("summary") or "",
            "timeRel": e.get("time_rel") or "",
            "timeAbs": e.get("time_abs") or "",
            "sourceCount": e.get("source_count") or 0,
            "sources": e.get("sources") or "",
            "tags": e.get("tags") or [],
            "sensitive": is_sensitive(e),
        }
        out_list.append(rec)

    out_list.sort(key=lambda x: (-x["stars"], -x["hotDays"]))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("// Auto-generated from TrendTee scrape. User-owned dataset. Source: %s\n" % src)
        f.write("window.EVENTS = ")
        f.write(json.dumps(out_list, ensure_ascii=False))
        f.write(";\n")

    print("SRC", src)
    print("unique events:", len(out_list))
    print("th:", sum(1 for x in out_list if x["country"] == "th"),
          "my:", sum(1 for x in out_list if x["country"] == "my"))
    print("sensitive:", sum(1 for x in out_list if x["sensitive"]))
    print("written:", out)

if __name__ == "__main__":
    main()
