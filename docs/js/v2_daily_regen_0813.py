# -*- coding: utf-8 -*-
"""8/13 增量重建：基底=当前 data.js(308) + 今日候选(泰31+马36) -> 写回 data.js，batch=daily-2026-08-13。"""
import json, os, shutil, urllib.request, ssl, urllib.parse, secrets, time
from collections import defaultdict
from io import BytesIO
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
DATA_JS = os.path.join(HERE, "data.js")
REAL = os.path.join(PROJECT, "site", "img", "real")
os.makedirs(REAL, exist_ok=True)

BATCH = "daily-2026-08-13"
TODAY = "2026-08-13"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

CAT_MAP = {
    "明星八卦": "celebrity", "演唱会综艺": "concert_show", "影视剧": "film_tv",
    "游戏电竞": "gaming", "网络热梗": "meme", "其他热搜": "other",
    "社会民生": "society", "体育": "sports", "电商政策": "ecommerce", "平台热搜": "platform_search",
}
RISK_MAP = {"明星八卦": "中", "影视剧": "中", "政治人物相关": "高", "社会民生": "低", "网络热梗": "低",
            "电商政策": "低", "平台热搜": "低", "游戏电竞": "低", "演唱会综艺": "中", "其他热搜": "低", "体育": "低"}
HOT_MAP = {"电商政策": 30, "平台热搜": 15, "社会民生": 90, "体育": 60}

def wiki_img(title):
    if not title:
        return None
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.loads(urllib.request.urlopen(req, timeout=20, context=CTX).read())
            if "originalimage" in d: return d["originalimage"]["source"]
            if "thumbnail" in d: return d["thumbnail"]["source"]
        except Exception:
            time.sleep(1.2)
    return None

def save_jpg(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=30, context=CTX).read()
        if len(data) < 2000: return False
        try:
            im = Image.open(BytesIO(data)).convert("RGB"); im.save(path, "JPEG", quality=88)
        except Exception:
            return False
        return os.path.getsize(path) >= 2000
    except Exception:
        return False

def build_cat_pool(base):
    pool = defaultdict(list)
    for e in base:
        c = e.get("cover", "")
        if c.startswith("real/"):
            fn = os.path.basename(c)
            p = os.path.join(REAL, fn)
            if os.path.exists(p) and os.path.getsize(p) >= 2000:
                pool[e.get("catCn", "其他热搜")].append(fn)
    return pool

def fresh_id():
    return secrets.token_hex(12)

def make_event(cand, cat_pool):
    eid = fresh_id()
    catCn = cand["catCn"]; country = cand["country"]
    buzz = cand.get("buzzSignal", "稳定热门")
    stars = {"viral": 5, "上升中": 4, "稳定热门": 4, "新发布": 4}.get(buzz, 4)
    buzz_idx = {"viral": 92, "上升中": 80, "稳定热门": 74, "新发布": 82}.get(buzz, 74)
    cred = "高" if any(k in cand.get("sourceUrl", "") for k in ["wikipedia", "official", "majorcineplex", "uniqlo", "roblox", "store.steampowered", "bernama"]) else "中"
    cred_score = 90 if cred == "高" else 78
    risk = RISK_MAP.get(catCn, "低")
    wiki = cand.get("wikiTitle", "")
    cover = f"real/{eid}.jpg"; dest = os.path.join(REAL, os.path.basename(cover)); img_src = ""
    got = False
    if wiki:
        u = wiki_img(wiki)
        if u and save_jpg(u, dest):
            img_src = f"维基媒体：{wiki}"; got = True
    if not got:
        pool = cat_pool.get(catCn, [])
        if pool:
            src = secrets.choice(pool)
            shutil.copy(os.path.join(REAL, src), dest)
            img_src = "同类目真实图示意"; got = True
    if not got:
        any_real = [f for f in os.listdir(REAL) if f.endswith(".jpg") and os.path.getsize(os.path.join(REAL, f)) >= 2000]
        if any_real:
            shutil.copy(os.path.join(REAL, secrets.choice(any_real)), dest)
            img_src = "通用真实图示意"
    src_url = cand.get("sourceUrl", "")
    return {
        "id": eid, "titleCn": cand["titleCn"], "titleOrig": cand.get("titleOrig", ""),
        "catCn": catCn, "cat": CAT_MAP.get(catCn, "other"), "country": country,
        "stars": stars, "cover": cover, "coverType": "real",
        "credibilityScore": cred_score, "buzzIndex": buzz_idx,
        "summary": cand.get("summary", ""),
        "sources": [{"type": "官方" if cred == "高" else "媒体/榜单", "region": "泰国" if country == "th" else "马来西亚",
                     "credibility": cred, "url": src_url}],
        "sourceBreadth": {"local": True, "global": country == "my" or "world" in cand.get("titleCn", ""), "social_only": False},
        "timeline": [{"date": TODAY, "desc": "入选今日(8/13)印选热点日报"}],
        "printType": ("人物印花" if catCn in ("明星八卦", "影视剧", "演唱会综艺") else
                      "文字梗/标语" if catCn in ("网络热梗", "其他热搜") else
                      "主题插画" if catCn in ("社会民生", "游戏电竞") else
                      "信息图/清单" if catCn in ("电商政策", "平台热搜") else "图案印花"),
        "risk": risk, "hotDays": HOT_MAP.get(catCn, 18 if buzz in ("新发布", "viral") else 45),
        "imageSource": img_src, "hasMedia": True,
        "media": [{"thumb": cover, "caption": cand["titleCn"]}],
        "fresh": True, "batch": BATCH, "primaryUrl": src_url,
    }

def main():
    # 基底 = 当前 data.js（累积历史）
    raw = open(DATA_JS, encoding="utf-8").read()
    base, _ = json.JSONDecoder().raw_decode(raw, raw.index("["))
    cat_pool = build_cat_pool(base)
    existing = {e.get("titleCn") for e in base}
    # 候选
    cands = []
    for f in ["candidates_th_0813.json", "candidates_my_0813.json"]:
        cands += json.load(open(os.path.join(HERE, f), encoding="utf-8"))
    added, skipped = [], 0
    for c in cands:
        if c["titleCn"] in existing:
            skipped += 1; continue
        existing.add(c["titleCn"])
        added.append(make_event(c, cat_pool))
    out = base + added
    for e in out:
        if e.get("catCn") in CAT_MAP:
            e["cat"] = CAT_MAP[e["catCn"]]
    txt = "window.SITE_UPDATED = \"" + TODAY + "T09:00:00\";
window.EVENTS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n"
    open(DATA_JS, "w", encoding="utf-8").write(txt)
    # 磁盘复核
    reread = open(DATA_JS, encoding="utf-8").read()
    chk, _ = json.JSONDecoder().raw_decode(reread, reread.index("["))
    assert len(chk) == len(out), f"disk mismatch {len(chk)} != {len(out)}"
    b64 = sum(1 for e in chk if str(e.get("cover", "")).startswith("data:image"))
    broken = 0
    for e in chk:
        cc = e.get("cover", "")
        if cc.startswith("real/"):
            p = os.path.join(REAL, os.path.basename(cc))
            if not os.path.exists(p) or os.path.getsize(p) < 2000:
                broken += 1
    fresh = sum(1 for e in chk if e.get("batch") == BATCH)
    real_wiki = sum(1 for e in added if "维基" in (e.get("imageSource") or ""))
    print(f"BASE={len(base)} + ADDED={len(added)} (skipped dup={skipped}) = TOTAL={len(chk)}")
    print(f"GATE: base64={b64} | broken/missing={broken} | fresh(8/13)={fresh}")
    print(f"added imageSource: wiki={real_wiki} | fallback={len(added)-real_wiki}")

if __name__ == "__main__":
    main()
