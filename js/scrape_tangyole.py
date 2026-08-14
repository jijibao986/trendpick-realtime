# -*- coding: utf-8 -*-
"""采集 news.tangyole.com (TrendTee 泰马热点选品) —— 可每日复用的稳定版。
输出: <workspace>/.workbuddy/memory/_tmp_YYYYMMDD/events.json
用法:
  python scrape_tangyole.py                 # 抓当天
  python scrape_tangyole.py --date 20260807
  python scrape_tangyole.py --out /path/to/events.json
"""
import re, json, os, sys, time, argparse
import urllib.request
from collections import Counter

BASE = "https://news.tangyole.com"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .../automation-claw-.../
CATS = ["celebrity", "concert_show", "film_tv", "gaming", "meme", "other", "politics", "society", "sports"]
CAT_CN = {
    "celebrity": "明星八卦", "concert_show": "演唱会/演出", "film_tv": "影视剧",
    "gaming": "游戏电竞", "meme": "网络热梗", "other": "其他热搜",
    "politics": "政党选举", "society": "社会民生", "sports": "体育",
}

def fetch(url, tries=3):
    last = ""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = str(e)
            sys.stderr.write("  retry %d %s: %s\n" % (i + 1, url, e))
            time.sleep(1.5)
    sys.stderr.write("  FAILED %s: %s\n" % (url, last))
    return ""

def clean(s):
    if s is None:
        return ""
    s = re.sub(r"<!--.*?-->", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&quot;", '"'), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&#x27;", "'"), ("&nbsp;", " "), ("&#39;", "'")):
        s = s.replace(a, b)
    return s.strip()

CARD_RE = re.compile(r'<a class="block rounded-xl border.*?href="(/(?:th|my)/event/[^"]+)"(.*?)</a>', re.S)

def parse(html, country, cat):
    out = []
    for m in CARD_RE.finditer(html):
        url, body = m.group(1), m.group(2)
        d = {"country": country, "cat": cat, "cat_cn": CAT_CN.get(cat, cat), "url": BASE + url}
        st = re.search(r'title="印花指数 (\d+) 星"', body)
        d["stars"] = int(st.group(1)) if st else 0
        tags = [clean(t) for t in re.findall(r'<span class="rounded bg-[^"]*"[^>]*>(.*?)</span>', body)]
        d["tags"] = [t for t in tags if t]
        d["print_type"] = next((t for t in d["tags"] if t in ("文字款", "图案款", "文字+图案")), "")
        d["cat_label"] = next((t for t in d["tags"] if t not in ("文字款", "图案款", "文字+图案")), "")
        tm = re.search(r'<span class="text-neutral-400" title="([^"]+)">([^<]+)</span>', body)
        d["time_abs"], d["time_rel"] = (tm.group(1), clean(tm.group(2))) if tm else ("", "")
        hot = re.search(r'还热\s*(?:<!--\s*-->)?\s*(\d+)\s*(?:<!--\s*-->)?\s*天', body)
        d["hot_days"] = int(hot.group(1)) if hot else None
        if "bg-red-500" in body and "高风险" in body:
            d["risk"] = "高风险"
        elif "bg-amber-500" in body and "中风险" in body:
            d["risk"] = "中风险"
        elif "bg-emerald-500" in body and "低风险" in body:
            d["risk"] = "低风险"
        else:
            d["risk"] = "未标注"
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", body, re.S)
        d["title_cn"] = clean(h3.group(1)) if h3 else ""
        p1 = re.search(r'<p class="mt-0\.5 line-clamp-1[^"]*"[^>]*>(.*?)</p>', body, re.S)
        d["title_orig"] = clean(p1.group(1)) if p1 else ""
        p2 = re.search(r'<p class="mt-2 line-clamp-2[^"]*"[^>]*>(.*?)</p>', body, re.S)
        d["summary"] = clean(p2.group(1)) if p2 else ""
        src = re.search(r'(\d+)\s*家媒体', clean(body))
        srcs = re.findall(r'家媒体\s*·?\s*([^<]{2,120})', clean(body))
        d["source_count"] = int(src.group(1)) if src else None
        d["sources"] = clean(srcs[0]) if srcs else ""
        out.append(d)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="抓取日期 YYYYMMDD（默认今天）")
    ap.add_argument("--out", help="events.json 输出路径（默认 <workspace>/.workbuddy/memory/_tmp_YYYYMMDD/events.json）")
    args = ap.parse_args()

    if args.date:
        ymd = args.date
    else:
        ymd = time.strftime("%Y%m%d")
    if args.out:
        out_path = args.out
    else:
        tmp_dir = os.path.join(ROOT, ".workbuddy", "memory", "_tmp_" + ymd)
        os.makedirs(tmp_dir, exist_ok=True)
        out_path = os.path.join(tmp_dir, "events.json")

    all_items, seen = [], set()
    def grab(url, country, cat):
        html = fetch(url)
        if not html:
            return 0
        n = 0
        for it in parse(html, country, cat):
            if it["url"] in seen:
                continue
            seen.add(it["url"]); all_items.append(it); n += 1
        sys.stderr.write("  %s -> +%d (total %d)\n" % (url, n, len(all_items)))
        return n

    for country in ("th", "my"):
        for cat in CATS:
            grab("%s/%s?cat=%s" % (BASE, country, cat), country, cat)
            time.sleep(0.4)
            grab("%s/%s?cat=%s&days=1" % (BASE, country, cat), country, cat)
            time.sleep(0.4)
        for q in ("?days=1", "?days=3", "?stars=4", "?stars=3", "?risk=low", ""):
            grab("%s/%s%s" % (BASE, country, q), country, "mixed")
            time.sleep(0.4)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=1)

    print("TOTAL", len(all_items))
    print("OUT", out_path)
    print("country", Counter(i["country"] for i in all_items))
    print("cat", Counter(i["cat_label"] for i in all_items))
    print("stars", Counter(i["stars"] for i in all_items))
    print("risk", Counter(i["risk"] for i in all_items))

if __name__ == "__main__":
    main()
