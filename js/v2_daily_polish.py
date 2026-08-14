# -*- coding: utf-8 -*-
"""打磨：给今日日报兜底事件分配互不相同的真实图，并为可图的补真实主题图。"""
import json, os, urllib.request, urllib.parse, ssl

DATA_JS = os.path.join(os.path.dirname(__file__), "data.js")
IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "img", "real"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

def get(u):
    r = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "application/json"})
    return urllib.request.urlopen(r, timeout=20, context=CTX).read()
def wiki_img(q):
    try:
        d = json.loads(get("https://en.wikipedia.org/api/rest_v1/page/summary/%s" % urllib.parse.quote(q)))
        if "originalimage" in d: return d["originalimage"]["source"]
    except Exception: pass
    try:
        d = json.loads(get("https://en.wikipedia.org/w/api.php?action=query&titles=%s&prop=pageimages&piprop=original&format=json" % urllib.parse.quote(q)))
        for p in d["query"]["pages"].values():
            if "original" in p: return p["original"]["source"]
    except Exception: pass
    return None
def dl(src, dst):
    r = urllib.request.Request(src, headers={"User-Agent": UA})
    data = urllib.request.urlopen(r, timeout=25, context=CTX).read()
    if len(data) < 2000: return False
    open(dst, "wb").write(data); return True

raw = open(DATA_JS, encoding="utf-8").read(); i = raw.index("[")
arr, _ = json.JSONDecoder().raw_decode(raw, i)

fb = [e for e in arr if e.get("fresh") and "同类目示意" in (e.get("imageSource") or "")]
used = set()
for e in fb:
    used.add(e["cover"])
# 同分类候选池封面（磁盘有效）
cat_covers = {}
for e in arr:
    if e.get("cover","").startswith("real/") and os.path.getsize(os.path.join(IMG_DIR, os.path.basename(e["cover"]))) >= 2000:
        cat_covers.setdefault(e.get("catCn"), []).append(e["cover"])

# 1) 英仙座流星雨：NASA 自由图
for e in fb:
    if e["titleCn"].startswith("英仙座"):
        src = "https://upload.wikimedia.org/wikipedia/commons/2/24/Perseid_meteor.jpg"
        dst = os.path.join(IMG_DIR, os.path.basename(e["cover"]))
        try:
            if dl(src, dst):
                e["imageSource"] = "Wikipedia / Commons（NASA 自由版权）"
                e["media"][0]["source"] = e["imageSource"]; print("Perseid OK")
            else: print("Perseid small")
        except Exception as ex: print("Perseid fail", ex)

# 2) Stray Kids：尝试真实图
for e in fb:
    if e["titleCn"].startswith("Stray Kids"):
        src = wiki_img("Stray Kids")
        if src:
            dst = os.path.join(IMG_DIR, os.path.basename(e["cover"]))
            try:
                if dl(src, dst):
                    e["imageSource"] = "Wikipedia / Commons（自由版权）"
                    e["media"][0]["source"] = e["imageSource"]; print("Stray Kids OK", src[:50])
                else: print("Stray Kids small")
            except Exception as ex: print("Stray Kids fail", ex)
        else: print("Stray Kids no wiki")

# 3) 剩余兜底分配互不相同的同分类真实图
for e in fb:
    if "同类目示意" not in (e.get("imageSource") or ""):
        continue  # 已补真实图
    cands = [c for c in cat_covers.get(e["catCn"], []) if c not in used]
    if cands:
        newc = cands[0]; used.add(newc)
        e["cover"] = newc
        e["media"][0]["thumb"] = newc
        print("reassign", e["titleCn"], "->", newc)

out = "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
open(DATA_JS, "w", encoding="utf-8").write(out)

# 校验去重 + 门禁
from collections import Counter
cov = Counter(e["cover"] for e in arr if e.get("fresh"))
dups = {k:v for k,v in cov.items() if v>1}
b=0
for e in arr:
    c=e.get("cover","")
    if c.startswith("real/"):
        p=os.path.join(IMG_DIR,os.path.basename(c))
        if not os.path.exists(p) or os.path.getsize(p)<2000: b+=1
print("fresh duplicate covers:", dups)
print("GATE broken/missing:", b, "| total:", len(arr))
