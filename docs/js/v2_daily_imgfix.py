# -*- coding: utf-8 -*-
"""为今日日报中 8 条同类目兜底事件，尝试补抓自由版权主题真实图。"""
import json, os, urllib.request, urllib.parse, ssl

DATA_JS = os.path.join(os.path.dirname(__file__), "data.js")
IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "img", "real"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

# titleCn -> wikipedia 查询词
QUERY = {
    "英仙座流星雨星空 Tee": "Perseid",
    "中秋灯笼满月 Tee": "Mid-Autumn Festival",
    "屠妖节迪亚灯 Tee": "Deepavali",
    "足球球迷 Tee": "Association football",
    "KATSEYE《Animal》野性系列": "Katseye",
    "宽松 Graphic Tee 基底": "T-shirt",
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    return urllib.request.urlopen(req, timeout=20, context=CTX).read()

def wiki_img(q):
    # 1) REST summary
    try:
        d = json.loads(get("https://en.wikipedia.org/api/rest_v1/page/summary/%s" % urllib.parse.quote(q)))
        if "originalimage" in d and d["originalimage"].get("source"):
            return d["originalimage"]["source"]
    except Exception: pass
    # 2) pageimages
    try:
        u = "https://en.wikipedia.org/w/api.php?action=query&titles=%s&prop=pageimages&piprop=original&format=json" % urllib.parse.quote(q)
        d = json.loads(get(u))
        pages = d["query"]["pages"]
        for p in pages.values():
            if "original" in p: return p["original"]["source"]
    except Exception: pass
    return None

def download(src, dst):
    req = urllib.request.Request(src, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=25, context=CTX).read()
    if len(data) < 2000: return False
    with open(dst, "wb") as f: f.write(data)
    return True

raw = open(DATA_JS, encoding="utf-8").read()
i = raw.index("[")
arr, _ = json.JSONDecoder().raw_decode(raw, i)

fixed = 0
for e in arr:
    if not e.get("fresh"): continue
    if "同类目示意" not in (e.get("imageSource") or ""): continue
    q = QUERY.get(e["titleCn"])
    if not q: continue
    src = wiki_img(q)
    if not src:
        print("  no wiki img for", e["titleCn"]); continue
    dst = os.path.join(IMG_DIR, os.path.basename(e["cover"]))
    try:
        if download(src, dst):
            e["imageSource"] = "Wikipedia / Commons（自由版权）"
            e["media"][0]["source"] = e["imageSource"]
            fixed += 1
            print("  OK", e["titleCn"], "->", src[:60])
        else:
            print("  too small", e["titleCn"])
    except Exception as ex:
        print("  fail", e["titleCn"], ex)

out = "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
open(DATA_JS, "w", encoding="utf-8").write(out)
print("fixed:", fixed, "| total:", len(arr))

# 门禁复核
b=0
for e in arr:
    c=e.get("cover","")
    if c.startswith("real/"):
        p=os.path.join(IMG_DIR,os.path.basename(c))
        if not os.path.exists(p) or os.path.getsize(p)<2000: b+=1
print("GATE broken/missing:", b)
