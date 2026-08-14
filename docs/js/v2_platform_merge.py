# -*- coding: utf-8 -*-
"""印选 TrendPick v2 — 补充「电商政策」+「平台热搜」两类事件（源自每日热点日报 ⑥⑬）。
真实配图走 Wikipedia REST summary（自由版权照片），图片完整性门禁：0 base64 / 0 损坏 / 0 缺失。"""
import json, os, uuid, urllib.request, urllib.parse, ssl
from PIL import Image
from io import BytesIO

DATA_JS = "data.js"
IMG_DIR = os.path.abspath("../img/real")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def load():
    raw = open(DATA_JS, encoding="utf-8").read()
    i = raw.index("[")
    arr, _ = json.JSONDecoder().raw_decode(raw, i)
    return arr

def save(arr):
    out = "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(out)

import time

def wiki_img(title):
    """返回 Wikipedia 条目主图的 JPG/PNG 直链（自由版权优先）。"""
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.loads(urllib.request.urlopen(req, timeout=20, context=CTX).read())
            if "originalimage" in d: return d["originalimage"]["source"]
            if "thumbnail" in d: return d["thumbnail"]["source"]
            return None
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                time.sleep(8 * (attempt + 1)); continue
            break
        except Exception as ex:
            print("  wiki_img fail", title, ex); break
    return None

def download(url, path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=30, context=CTX).read()
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                time.sleep(8 * (attempt + 1)); continue
            return False
        except Exception:
            return False
        if len(data) < 2000:
            return False
        try:
            im = Image.open(BytesIO(data)).convert("RGB")
            im.save(path, "JPEG", quality=88)
        except Exception:
            return False
        return os.path.getsize(path) >= 2000
    return False

def get_image(wiki_title, fallback_title, path):
    for t in (wiki_title, fallback_title):
        time.sleep(1.5)
        u = wiki_img(t)
        if u:
            if download(u, path):
                return t
            time.sleep(3)
    # ultimate fallback: a guaranteed free Commons photo
    for fb in [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Shopping_cart_in_supermarket.jpg/640px-Shopping_cart_in_supermarket.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Amazon_delivery_packages.jpg/640px-Amazon_delivery_packages.jpg",
    ]:
        time.sleep(2)
        if download(fb, path):
            return "fallback-commons"
    return None

def new_id():
    return uuid.uuid4().hex[:24]

# ---- 事件定义 ----
# 电商政策（⑥）：9 条
POLICY = [
  dict(titleCn="TikTok Shop 新商减免（泰马新菲新免佣至9/30）", country="all", wiki="E-commerce", fb="Online shopping",
       impact="利好", stars=5, buzz=92, cred=95, risk="低",
       summary="TikTok Shop 在泰国/马来/新加坡/菲律宾/越南推出新商减免：免佣金（马来120天/菲90天/新90天/泰30天）、免交易手续费、免基础设施费，窗口 2026-07-01 至 09-30。新店冷启成本大降，是入场最佳窗口。",
       tl=[("2026-07-01","新商减免启动"),("2026-09-30","免佣窗口截止")],
       src=[("TikTok Shop Seller Center","https://seller-us.tiktok.com/")]),
  dict(titleCn="TikTok Shop 泰国二手品类资质升级（仅企业卖家）", country="th", wiki="Recycling", fb="Second-hand goods",
       impact="收紧", stars=4, buzz=80, cred=90, risk="低",
       summary="二手奢侈品/手机数码/服饰鞋包翻新类目资质升级，2026-07-31 起仅允许企业卖家经营。个人卖家退出二手赛道，需以企业资质入场。",
       tl=[("2026-07-31","二手品类仅限企业卖家")],
       src=[("TikTok Shop Seller Center","https://seller-us.tiktok.com/")]),
  dict(titleCn="Shopee 马来平台支持费 RM0.50/单", country="my", wiki="Online shopping", fb="Retail",
       impact="微增成本", stars=4, buzz=78, cred=90, risk="低",
       summary="马来西亚本地店每单收 RM0.50「平台支持费」（含 8% 税），新店自 2026-08-01 起豁免。每单微增约 0.5 马币成本，需计入定价。",
       tl=[("2026-08-01","新店豁免，老店起征")],
       src=[("Shopee Seller Education Hub","https://seller.shopee.com/")]),
  dict(titleCn="Shopee 马来本地佣金上调（时尚最高15%）", country="my", wiki="Shopping mall", fb="Retail",
       impact="成本上升", stars=5, buzz=88, cred=92, risk="低",
       summary="本地 Marketplace 佣金上调：电子 7.5–14%、时尚 11.5–13.5%、快消最高 15%，2026-08-14 起生效。时尚类卖家成本上升明显，须重算定价。",
       tl=[("2026-08-14","新佣金表生效")],
       src=[("Shopee Seller Education Hub","https://seller.shopee.com/")]),
  dict(titleCn="Lazada 泰国跨境佣金 +4.5% / Premium 7%→8%", country="th", wiki="Import", fb="International trade",
       impact="成本上升", stars=5, buzz=85, cred=90, risk="低",
       summary="泰国跨境佣金统一 +4.5%；Premium 店铺由 7% 升至 8%，2026-08-01 起。非 Premium 卖家涨幅更大，建议评估 Premium 包对冲。",
       tl=[("2026-08-01","佣金上调生效")],
       src=[("Lazada Seller Center","https://sellercenter.lazada.com/")]),
  dict(titleCn="Lazada 跨境技术支持费 +4.3%（马新泰越菲）", country="all", wiki="Logistics", fb="Supply chain",
       impact="成本上升", stars=5, buzz=86, cred=91, risk="低",
       summary="马来/新/泰/越/菲新增「技术支持费」：跨境订单按比例代扣（马来实扣约 4.32%），2026-08-17 起。全跨境单普遍 +约 4.3% 成本。",
       tl=[("2026-08-17","技术支持费起征")],
       src=[("Lazada Seller Center","https://sellercenter.lazada.com/")]),
  dict(titleCn="印尼单一商品出口管制 9/1（棕榈油等）", country="all", wiki="Palm oil", fb="Indonesia",
       impact="供应链", stars=4, buzz=82, cred=88, risk="低",
       summary="印尼政府将单一商品出口管制（棕榈油等）由 Danantara 统管，2026-09-01 全效。做印尼货源的卖家须提前备货，原料采购合规趋严。",
       tl=[("2026-09-01","出口管制全效")],
       src=[("印尼贸易部 Kemendag","https://www.kemendag.go.id/")]),
  dict(titleCn="Shopee SLS-N 日达分区轮流关停", country="all", wiki="Package delivery", fb="Warehouse",
       impact="物流变动", stars=4, buzz=79, cred=87, risk="低",
       summary="菲/泰/越下半年 SLS-N 日达按城市分区轮流关停。绑定 N 日达的店铺将自动切换物流渠道，需关注履约时效变化。",
       tl=[("2026 下半年","分区轮流关停")],
       src=[("Shopee Seller Education Hub","https://seller.shopee.com/")]),
  dict(titleCn="TikTok Shop「一商卖全球·经营组」上线", country="all", wiki="International trade", fb="Globalization",
       impact="利好", stars=4, buzz=84, cred=93, risk="低",
       summary="「一商卖全球·经营组」已上线：多店好评继承、消息聚合，多国店铺可统一运营。利于泰马卖家用一套团队管多市场。",
       tl=[("已上线","多店统一运营")],
       src=[("TikTok Shop Seller Center","https://seller-us.tiktok.com/")]),
]

# 平台热搜（⑬）：6 平台，每条汇总该平台 🔥 关键词
HOTSEARCH = [
  dict(titleCn="Shopee 泰国热搜 T恤关键词 TOP", country="th", wiki="Shopping", fb="E-commerce",
       stars=4, buzz=88, cred=90, risk="低",
       summary="Shopee TH 站内热搜 T恤关键词（🔥高）：宽松 Oversized、情侣 Couple、动漫 Anime、母亲节 Mother's Day、图形 Graphic、K-pop/Stray Kids、足球 Football。宽松/情侣/动漫为常年霸榜长销词。",
       src=[("Shopee TH","https://shopee.co.th/")]),
  dict(titleCn="Shopee 马来热搜 T恤关键词 TOP", country="my", wiki="Retail", fb="Shopping mall",
       stars=4, buzz=88, cred=90, risk="低",
       summary="Shopee MY 站内热搜 T恤关键词（🔥高）：Baju Oversized、Baju Couple、Baju Anime、Baju Merdeka（8/31 国庆季）、Graphic Tee、Baju Deepavali（10 月季）、Streetwear。",
       src=[("Shopee MY","https://shopee.com.my/")]),
  dict(titleCn="Lazada 泰国热搜 T恤关键词 TOP", country="th", wiki="E-commerce", fb="Online shopping",
       stars=4, buzz=86, cred=89, risk="低",
       summary="Lazada TH 站内热搜 T恤关键词（🔥高）：Oversized、Couple、Anime、母亲节、Graphic、K-pop、重磅 Heavyweight、Y2K、Slogan。与 Shopee TH 高度重叠。",
       src=[("Lazada TH","https://www.lazada.co.th/")]),
  dict(titleCn="Lazada 马来热搜 T恤关键词 TOP", country="my", wiki="Warehouse", fb="Mail order",
       stars=4, buzz=86, cred=89, risk="低",
       summary="Lazada MY 站内热搜 T恤关键词（🔥高）：Baju Oversized、Baju Couple、Baju Anime、Baju Merdeka、Graphic、Baju Deepavali、Streetwear、Cute Cartoon。",
       src=[("Lazada MY","https://www.lazada.com.my/")]),
  dict(titleCn="TikTok Shop 泰国热搜 T恤关键词 TOP", country="th", wiki="Social media", fb="Live streaming",
       stars=5, buzz=90, cred=88, risk="低",
       summary="TikTok Shop TH 热搜 T恤关键词（🔥高）：Oversized、Couple、动漫 Anime、母亲节、Graphic、K-pop/Stray Kids、Vintage、Y2K、Slogan。短视频带货转化高。",
       src=[("TikTok Shop TH","https://seller-us.tiktok.com/")]),
  dict(titleCn="TikTok Shop 马来热搜 T恤关键词 TOP", country="my", wiki="Live streaming", fb="Social media",
       stars=5, buzz=90, cred=88, risk="低",
       summary="TikTok Shop MY 热搜 T恤关键词（🔥高）：Baju Oversized、Baju Couple、Baju Anime、Baju Merdeka、Graphic、Baju Viral（网红同款）、Baju Custom Name、Cute Cartoon。",
       src=[("TikTok Shop MY","https://seller-my.tiktok.com/")]),
]

def build_event(d, catCn):
    eid = new_id()
    path = os.path.join(IMG_DIR, eid + ".jpg")
    used = get_image(d["wiki"], d["fb"], path)
    print(f"  [{catCn}] {d['titleCn'][:30]} -> img {'OK' if used else 'FAIL'} ({used})")
    return {
        "id": eid,
        "catCn": catCn,
        "catEn": "E-Commerce Policy" if catCn == "电商政策" else "Platform Hot Search",
        "titleCn": d["titleCn"],
        "titleTh": "",
        "titleEn": "",
        "country": d.get("country", "all"),
        "summaryCn": d["summary"],
        "printType": "平台情报" if catCn == "电商政策" else "热搜趋势",
        "risk": d.get("risk", "低"),
        "stars": d.get("stars", 4),
        "buzzIndex": d.get("buzz", 85),
        "credibilityScore": d.get("cred", 90),
        "hotDays": d.get("tl", [("持续", "持续关注")])[0][0] if d.get("tl") else "持续",
        "cover": "real/" + eid + ".jpg",
        "coverType": "real",
        "imageSource": ("Wikipedia: " + used) if used else "同类目示意",
        "hasMedia": False,
        "media": [],
        "sources": [{"name": n, "url": u} for n, u in d.get("src", [])],
        "sourceBreadth": len(d.get("src", [])),
        "timeline": [{"date": a, "text": b} for a, b in d.get("tl", [])],
        "tags": ["电商政策", "跨境", "平台"] if catCn == "电商政策" else ["平台热搜", "T恤关键词", "跨境"],
        "localFlag": False,
        "sensitive": False,
        "fresh": True,
        "batch": "daily-2026-08-12",
        "impact": d.get("impact", ""),
    }

if __name__ == "__main__":
    arr = load()
    print("before:", len(arr))
    added = 0
    for d in POLICY:
        arr.append(build_event(d, "电商政策")); added += 1
    for d in HOTSEARCH:
        arr.append(build_event(d, "平台热搜")); added += 1
    save(arr)
    # 写盘后磁盘复核
    raw = open(DATA_JS, encoding="utf-8").read()
    arr2, _ = json.JSONDecoder().raw_decode(raw, raw.index("["))
    broken = 0
    for e in arr2:
        cc = e.get("cover", "")
        if cc.startswith("real/"):
            p = os.path.join("../img/real", os.path.basename(cc))
            if not os.path.exists(p) or os.path.getsize(p) < 2000:
                broken += 1
    b64 = sum(1 for e in arr2 if str(e.get("cover", "")).startswith("data:image"))
    print("after:", len(arr2), "| added:", added, "| base64:", b64, "| broken/missing:", broken)
    cats = {}
    for e in arr2:
        cats[e["catCn"]] = cats.get(e["catCn"], 0) + 1
    print("categories:", cats)
