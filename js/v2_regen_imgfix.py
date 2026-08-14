# -*- coding: utf-8 -*-
"""对今日 fresh 事件中 wikiTitle 有值但被兜底的真实图，再用 维基+Commons 补抓，提升主题真实图占比。"""
import json, os, urllib.request, ssl, urllib.parse, time
from io import BytesIO
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
DATA_JS = os.path.join(HERE, "data.js")
REAL = os.path.join(PROJECT, "site", "img", "real")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

MAP = {
 "TEN新单登顶泰国榜":"TEN (entertainer)","JENNIE新单空降前五":"Jennie (singer)",
 "FreenBecky CP粉圈刷屏":"FreenBecky","母亲节茉莉浅蓝T恤":"Mother's Day (Thailand)",
 "水灯节11/25临近备货":"Loy Krathong","Vans×Carnival冬阴功Tee":"Vans",
 "IDOLiSH7影院直播热映":"Idolish7","《影之恶魔》登网飞泰前十":"Daemons of the Shadow Realm",
 "吉伊卡哇电影联名UT热卖":"Chiikawa","KATSEYE纪录片今日上映":"Katseye",
 "原神7.0至冬国今日上线":"Genshin Impact","ROBLOX 2026引擎大更新":"Roblox",
 "优衣库马里奥赛车UT8月":"Mario Kart","优衣库YOASOBI联名UT热卖":"Yoasobi",
 "西蒂30周年传奇演唱会":"Siti_Nurhaliza","苏利亚《Vishwanath》8月上映":"Suriya",
 "《Jana Nayagan》泰米尔爆款":"Kollywood","国庆日Jalur Gemilang":"Flag_of_Malaysia",
 "蜡染街头风回潮":"Batik","现代Kebaya回潮":"Kebaya","海贼王Elbaph篇热播":"One_Piece",
 "Stray Kids RUN IT巡演":"Stray_Kids","Neelofa清真时尚霸榜":"Neelofa",
 "2026世界杯西班牙夺冠":"2026_FIFA_World_Cup","马哈蒂尔死讯谣言":"Mahathir_Mohamad",
 "BLACKPINK巡演跳过大马":"Blackpink","好莱坞《奥德赛》在映":"The_Odyssey_2026_film",
 "马区X热搜泰腐CP霸榜":"LingOrm","MPL大马S18开赛":"Mobile_Legends:_Bang_Bang",
 "Shopee国旗T恤热搜":"Flag_of_Malaysia","TikTok蜡染街头热":"Batik",
}

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        return urllib.request.urlopen(req, timeout=25, context=CTX).read()
    except Exception:
        return None

def wiki_img(title):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
    for _ in range(3):
        try:
            d = json.loads(fetch(url))
            if "originalimage" in d: return d["originalimage"]["source"]
            if "thumbnail" in d: return d["thumbnail"]["source"]
        except Exception:
            time.sleep(1.0)
    return None

def commons_img(title):
    q = urllib.parse.quote(title)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={q}&gsrnamespace=6&gsrlimit=6&prop=imageinfo&iiprop=url&format=json"
    try:
        d = json.loads(fetch(url))
        for p in d.get("query", {}).get("pages", {}).values():
            if "imageinfo" in p:
                src = p["imageinfo"][0]["url"]
                if src.lower().endswith(".svg"): continue
                return src
    except Exception:
        time.sleep(1)
    return None

def save_jpg(url, path):
    data = fetch(url)
    if not data or len(data) < 2000: return False
    try:
        im = Image.open(BytesIO(data)).convert("RGB"); im.save(path, "JPEG", quality=88)
    except Exception:
        return False
    return os.path.getsize(path) >= 2000

def main():
    raw = open(DATA_JS, encoding="utf-8").read()
    arr, _ = json.JSONDecoder().raw_decode(raw, raw.index("["))
    fixed = 0
    for e in arr:
        if not e.get("fresh"): continue
        if "维基" in (e.get("imageSource") or ""): continue
        wt = MAP.get(e.get("titleCn", ""))
        if not wt: continue
        dest = os.path.join(REAL, os.path.basename(e["cover"]))
        for src_fn in (wiki_img(wt), commons_img(wt)):
            if src_fn and save_jpg(src_fn, dest):
                e["imageSource"] = "维基媒体：" + wt if "wikipedia" in src_fn else "维基共享：" + wt
                fixed += 1
                break
    txt = "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
    open(DATA_JS, "w", encoding="utf-8").write(txt)
    # 复核
    reread = open(DATA_JS, encoding="utf-8").read()
    chk, _ = json.JSONDecoder().raw_decode(reread, reread.index("["))
    assert len(chk) == len(arr)
    wiki_now = sum(1 for e in chk if e.get("fresh") and ("维基" in (e.get("imageSource") or "")))
    fallback = sum(1 for e in chk if e.get("fresh") and ("兜底" in (e.get("imageSource") or "")))
    print(f"补抓替换: {fixed} 条 | fresh 维基类真实图: {wiki_now} | fresh 兜底: {fallback}")
    b64 = sum(1 for e in chk if str(e.get("cover","")).startswith("data:image"))
    broken = sum(1 for e in chk if str(e.get("cover","")).startswith("real/") and (not os.path.exists(os.path.join(REAL,os.path.basename(e["cover"]))) or os.path.getsize(os.path.join(REAL,os.path.basename(e["cover"])))<2000))
    print(f"GATE: base64={b64} broken/missing={broken} TOTAL={len(chk)}")

if __name__ == "__main__":
    main()
