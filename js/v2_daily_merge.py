# -*- coding: utf-8 -*-
"""
印选 TrendPick v2 — 每日任务(热点日报)补充进站点数据
把 2026-08-12 热点日报 ⑨T恤设计推荐 22 条转成 v2 事件，
复用印选图库(site/img/real/)里已抓好的同主题真实配图，
追加进 data.js（标记 batch / fresh），并跑图片完整性门禁。
"""
import json, os, random, glob

DATA_JS = os.path.join(os.path.dirname(__file__), "data.js")
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "img", "real")
IMG_DIR = os.path.abspath(IMG_DIR)

# ---------- 1. 载入现有池 (257 条) ----------
raw = open(DATA_JS, encoding="utf-8").read()
i = raw.index("[")
arr, _ = json.JSONDecoder().raw_decode(raw, i)
print("pool loaded:", len(arr))

def norm(e):
    return (e.get("titleCn", "") + " " + e.get("titleOrig", "") + " " + " ".join(e.get("tags", []))).lower()

pool = arr
pool_norm = [norm(e) for e in pool]

def find_cover(kws):
    """在池里按关键词找同主题事件，返回其 cover（必须磁盘存在且>=2KB）。"""
    for kw in kws:
        k = kw.lower()
        for e, n in zip(pool, pool_norm):
            if k in n:
                c = e.get("cover", "")
                if c.startswith("real/") and os.path.getsize(os.path.join(IMG_DIR, os.path.basename(c))) >= 2000:
                    return e
    return None

def cat_rep_cover(catCn):
    """同类目任意一张有效真实配图兜底。"""
    for e in pool:
        if e.get("catCn") == catCn:
            c = e.get("cover", "")
            if c.startswith("real/") and os.path.getsize(os.path.join(IMG_DIR, os.path.basename(c))) >= 2000:
                return e
    return None

CAT_EN = {
    "明星八卦": "celebrity", "演唱会综艺": "concert_show", "影视剧": "film_tv",
    "游戏电竞": "gaming", "网络热梗": "meme", "其他热搜": "other",
    "社会民生": "society", "体育": "sports", "政党选举": "politics",
}

# ---------- 2. 今日 22 条 T恤设计推荐(来自日报⑨) ----------
# (titleCn, titleOrig, priority, catCn, country, stars, printType, hotDays, kws, tags, summary)
DAILY = [
 ("母亲节蓝茉莉感恩 Tee", "Mother's Day Jasmine（母亲节蓝茉莉）", 98, "社会民生", "th", 4, "文字+图案", 1,
  ["母亲","Mother","茉莉","蓝茉莉","วันแม่","Queen Mother","诗丽吉"],
  ["母亲节","蓝茉莉","泰国","感恩","蓝"],
  "蓝色茉莉花+「แม่」(妈妈)+感恩文案，今日母亲节节点零风险立即上架。"),
 ("SkyNani 顶流 CP 巡演 Tee", "SkyNani Fancon（Sky×Nani 粉丝演唱会）", 96, "明星八卦", "th", 4, "图案款", 30,
  ["SkyNani","Sky","Nani","Arrest"],
  ["SkyNani","CP","巡演","泰腐","演唱会"],
  "双男主剪影+演唱会日期，王牌 CP 演唱会即时转化。"),
 ("PondPhuwin 王牌 CP 通用底衫", "PondPhuwin（Pond×Phuwin）", 95, "明星八卦", "th", 4, "文字+图案", 365,
  ["PondPhuwin","Pond","Phuwin"],
  ["PondPhuwin","CP","顶流","常青"],
  "名字花字+应援色，常驻顶流全年长销底衫。"),
 ("马来国庆 Merdeka 国旗 Tee", "Merdeka Jalur Gemilang（独立日国旗）", 94, "社会民生", "my", 4, "图案款", 19,
  ["Merdeka","国庆","Jalur","独立日","独立"],
  ["Merdeka","国庆","马来","国旗","爱国"],
  "国旗色+「Merdeka」字样，8/31 临近提前打版。"),
 ("KengNamping #bibro 兄弟对衫", "KengNamping bibro（Keng×Namping 兄弟梗）", 92, "明星八卦", "th", 4, "文字款", 11,
  ["bibro","KengNamping","Keng","Namping","BiBi","兄弟"],
  ["bibro","KengNamping","兄弟","CP","2026爆红"],
  "「BIBI×BIBRO」对衫，2026 爆红新晋 CP 台北见面会 8/23。"),
 ("泰语万能梗「ปัง Pang」潮流字 Tee", "Pang Slay（ปัง 绝了）", 91, "网络热梗", "th", 3, "文字款", 180,
  ["ปัง","Pang","pang","绝了"],
  ["泰语","梗","Pang","潮流字","低成本"],
  "「ปัง」大字+星星特效，低成本高传播常青梗。"),
 ("蜘蛛侠 Brand New Day 漫画格纹 Tee", "Spider-Man: Brand New Day（蜘蛛侠：全新一天）", 90, "影视剧", "th", 3, "图案款", 60,
  ["Spider","蜘蛛侠","Marvel","漫威","Spider-Man"],
  ["蜘蛛侠","漫威","电影","漫画格纹"],
  "蛛网+电影感，全球 $484M+ 热映。"),
 ("KATSEYE《Animal》野性系列", "Animal Wild（KATSEYE 野性）", 89, "明星八卦", "th", 3, "图案款", 90,
  ["KATSEYE","Animal","猫眼"],
  ["KATSEYE","K-pop","野性","霓虹"],
  "动物纹+霓虹，Hot 100 #24。"),
 ("泰 BL 电竞《Be My Player Two》手柄 Tee", "Be My Player Two（我的玩家二号）", 88, "影视剧", "th", 3, "图案款", 30,
  ["Player Two","PlayerTwo","Be My Player","玩家二号"],
  ["Be My Player Two","电竞","BL","WeTV","手柄"],
  "手柄+战队 LOGO，WeTV 泰国榜 #1。"),
 ("马来 Love Algorithm 跨境 CP Tee", "Love Algorithm MY（恋爱演算法）", 87, "明星八卦", "my", 3, "图案款", 30,
  ["Love Algorithm","LoveAlgorithm","Jack Goh","Zhen Ning","恋爱演算法"],
  ["Love Algorithm","马来","CP","跨境","独家"],
  "Jack Goh×Zhen Ning，马来 2026 代表 BL 跨境独家。"),
 ("中秋灯笼满月 Tee", "Mid-Autumn Lantern（中秋灯笼）", 86, "社会民生", "th", 3, "图案款", 44,
  ["中秋","Mid-Autumn","MidAutumn","灯笼","月饼","Mooncake","满月"],
  ["中秋","灯笼","满月","华人","玉兔"],
  "月饼+灯笼+玉兔，9/25 华人圈提前打版。"),
 ("FreenBecky GL 玫瑰双人 Tee", "FreenBecky（Freen×Becky）", 85, "明星八卦", "th", 3, "图案款", 365,
  ["FreenBecky","Freen","Becky","GL"],
  ["FreenBecky","GL","玫瑰","双女主"],
  "双女主+玫瑰，GL 全球顶流常青。"),
 ("蜡染 Batik 文化图腾 Tee", "Batik Malaysia（巴迪蜡染）", 84, "其他热搜", "my", 3, "图案款", 365,
  ["Batik","蜡染","巴迪"],
  ["Batik","蜡染","马来","文化","长青"],
  "KLFW 2026 年度主题，东西马传统图腾。"),
 ("Stray Kids《This & That》应援 Tee", "Stray Kids（ stray kids 应援）", 83, "明星八卦", "th", 3, "图案款", 120,
  ["Stray Kids","StrayKids","SKZ"],
  ["Stray Kids","K-pop","应援","眼睛标"],
  "眼睛标+歌词，YouTube 全球 #1。"),
 ("英仙座流星雨星空 Tee", "Perseid Meteor（英仙座流星雨）", 82, "其他热搜", "th", 3, "图案款", 2,
  ["英仙","Perseid","流星","Meteor","流星雨"],
  ["流星雨","星空","天文","季节"],
  "星空+流星，8/13 极大仅 1 天窗口紧迫。"),
 ("日漫《Frieren》花束剪影 Tee", "Frieren（葬送的芙莉莲）", 81, "影视剧", "th", 3, "图案款", 120,
  ["Frieren","芙莉莲","葬送"],
  ["Frieren","日漫","MAL","花束"],
  "芙莉莲+勇者辛美尔剪影，MAL 全球 #1。"),
 ("原神 5.8 夏日度假村 Tee", "Genshin Summer（原神 5.8 绘夏度假村）", 80, "游戏电竞", "th", 3, "图案款", 55,
  ["Genshin","原神","绘夏","Sunspray"],
  ["原神","Genshin","游戏","夏日"],
  "伊涅芙+海浪，全平台夏日活动。"),
 ("泰语「วอดส์ What's?」极简梗 Tee", "Wods（วอดส์ 装傻）", 79, "网络热梗", "th", 3, "文字款", 180,
  ["วอดส์","Wods","What"],
  ["泰语","梗","Wods","极简"],
  "大字疑问+问号，全网鬼畜常青梗。"),
 ("Lisa 辣酷豹纹 Tee", "Lisa BLACKPINK（莉萨）", 78, "明星八卦", "th", 3, "图案款", 365,
  ["Lisa","BLACKPINK","莉萨"],
  ["Lisa","BLACKPINK","豹纹","辣酷"],
  "豹纹+个人 logo，东南亚破圈。"),
 ("屠妖节迪亚灯 Tee", "Deepavali Diya（屠妖节油灯）", 77, "社会民生", "my", 3, "图案款", 69,
  ["Deepavali","屠妖","Diya","迪亚"],
  ["Deepavali","屠妖节","印度","油灯"],
  "油灯 diya+rangoli，10/20 季前打版。"),
 ("宽松 Graphic Tee 基底", "Oversized Graphic（宽松图形基底）", 76, "其他热搜", "th", 2, "图案款", 365,
  ["Oversized","宽松","Graphic"],
  ["Oversized","宽松","长销","无IP"],
  "无 IP 长销基底，泰马全平台热搜重叠。"),
 ("足球球迷 Tee", "Real Madrid / Musiala（皇马/穆西亚拉）", 75, "体育", "th", 2, "图案款", 90,
  ["Real Madrid","Musiala","足球","Football","皇马"],
  ["足球","球迷","皇马","穆西亚拉"],
  "俱乐部/球星，泰马足球热。"),
]

# ---------- 3. 生成新事件 ----------
used_ids = {e.get("id") for e in pool}
def new_id():
    while True:
        h = "%024x" % random.getrandbits(96)
        if h not in used_ids:
            used_ids.add(h); return h

matched = 0; fallback = 0
fresh_events = []
for (titleCn, titleOrig, prio, catCn, country, stars, pt, hotDays, kws, tags, summary) in DAILY:
    rep = find_cover(kws)
    if rep:
        matched += 1
        cover = rep["cover"]
        imageSource = rep.get("imageSource", "") or "印选图库"
        cred = rep.get("credibilityScore") or max(60, min(96, prio - 3))
        buzz = rep.get("buzzIndex") or max(70, min(98, prio))
        srcs = rep.get("sources") if isinstance(rep.get("sources"), list) else []
        sb = rep.get("sourceBreadth") or {"local": 1, "global": 0, "social_only": 0}
    else:
        rep = cat_rep_cover(catCn)
        fallback += 1
        cover = rep["cover"] if rep else ""
        imageSource = "印选图库（同类目示意）"
        cred = max(60, min(96, prio - 3))
        buzz = max(70, min(98, prio))
        srcs = []
        sb = {"local": 1, "global": 0, "social_only": 0}

    # 兜底来源
    if not srcs:
        srcs = [{"name": "泰马热点日报 2026-08-12", "type": "news", "url": "",
                 "credibility": "高", "region": country, "mention": 0}]

    eid = new_id()
    ev = {
        "id": eid,
        "country": country,
        "cat": CAT_EN.get(catCn, "other"),
        "catCn": catCn,
        "stars": stars,
        "printType": pt,
        "risk": "低风险",
        "hotDays": hotDays,
        "titleCn": titleCn,
        "titleOrig": titleOrig,
        "summary": summary,
        "tags": tags,
        "sensitive": False,
        "sources": srcs,
        "credibilityScore": cred,
        "buzzIndex": buzz,
        "timeline": [{
            "date": "2026-08-12",
            "label": "入选今日热点日报 T恤设计推荐",
            "desc": f"优先级 {prio}/100，关联日报板块⑨",
            "verified": False,
        }],
        "timeAbs": "2026-08-12",
        "timeRel": "今日热点日报入选",
        "timezoneNote": "UTC+8",
        "media": [{"type": "poster", "url": "", "thumb": cover,
                   "caption": titleCn, "source": imageSource}],
        "cover": cover,
        "hasMedia": True,
        "imageSource": imageSource,
        "primaryUrl": "",
        "sourceBreadth": sb,
        "coverType": "real",
        "batch": "daily-2026-08-12",
        "fresh": True,
        "priority": prio,
        "relatedBoard": 9,
    }
    fresh_events.append(ev)

arr.extend(fresh_events)
print(f"new events: {len(fresh_events)} | image matched from pool: {matched} | fallback: {fallback}")
print("total now:", len(arr))

# ---------- 4. 写盘 ----------
out = "window.EVENTS = " + json.dumps(arr, ensure_ascii=False, indent=1) + ";\n"
with open(DATA_JS, "w", encoding="utf-8") as f:
    f.write(out)
print("written:", os.path.getsize(DATA_JS), "bytes")

# ---------- 5. 图片门禁校验（从磁盘复核） ----------
broken = 0; missing = 0; base64 = 0; real = 0
for e in arr:
    c = e.get("cover", "")
    if c.startswith("data:image"):
        base64 += 1
    elif c.startswith("real/"):
        real += 1
        p = os.path.join(IMG_DIR, os.path.basename(c))
        if not os.path.exists(p) or os.path.getsize(p) < 2000:
            broken += 1
            print("  BROKEN:", e.get("titleCn"), c)
    else:
        missing += 1
print(f"GATE -> base64:{base64} | real:{real} | broken/missing:{broken+missing}")
