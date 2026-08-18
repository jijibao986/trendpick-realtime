#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick — 云端实时榜单爬虫 v3（零 Key · 纯标准库）
- 多源采集：Twitter/X 热搜、Apple Music、Steam、AniList 动漫、Google News 新闻
- 跨源聚合：同一热点(实体名包含关系)在多个数据源出现时，合并成一条多源事件并互相借图
- 真实配图：优先官方接口图 → 跨源借图 → 维基词条图 → Commons 兜底
每小时由 GitHub Actions 运行，生成 realtime.js 推到 GitHub Pages。
"""
import json
import os
import re
import ssl
import hashlib
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TZ8 = timezone(timedelta(hours=8))

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uff66-\uff9f]")


def now_iso():
    return datetime.now(TZ8).strftime("%Y-%m-%dT%H:%M:%S")


def fetch_text(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_json(url, timeout=15):
    return json.loads(fetch_text(url, timeout))


def post_json(url, payload, timeout=15):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def translate(text, to="zh-CN", timeout=6):
    """尽力把外文翻成中文（Google 翻译 gtx 端点，无需 Key）。失败回退原文。"""
    if not text:
        return text
    if CJK.search(text):
        return text
    try:
        q = urllib.parse.quote(text[:500])
        u = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={to}&dt=t&q={q}"
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        raw = urllib.request.urlopen(req, timeout=timeout, context=CTX).read().decode("utf-8", "ignore")
        j = json.loads(raw)
        out = "".join(seg[0] for seg in j[0] if seg[0])
        return out.strip() if out.strip() else text
    except Exception:
        return text


def stable_id(source, title):
    h = hashlib.sha1(f"{source}|{title}".encode("utf-8")).hexdigest()
    return "rt-" + h[:12]


SRC_NAME = {
    "trends24": "Twitter/X 热搜榜",
    "apple": "Apple Music 榜单",
    "steam": "Steam 榜单",
    "anilist": "AniList 动漫榜",
    "gnews": "Google 新闻",
    "mal": "MyAnimeList 榜单",
}

CAT_RANK = {"film_tv": 5, "gaming": 4, "music": 3, "celebrity": 5, "concert_show": 4, "meme": 3, "sports": 3, "society": 2, "politics": 2, "ecommerce": 3, "festival": 4, "news": 2, "platform_search": 2, "other": 1}


def make_event(source, title, *, url="", image="", country="多市场",
               cat="other", cat_cn="其他", rank=None, summary="", img_src=""):
    title = (title or "").strip()
    if not title:
        return None
    title_cn = translate(title)
    if rank and rank <= 2:
        _s = 5
    elif rank and rank <= 5:
        _s = 4
    elif rank and rank <= 10:
        _s = 3
    elif rank and rank <= 20:
        _s = 2
    else:
        _s = 1
    stars = "🔥" * _s
    buzz = max(20, 100 - (rank or 20) * 2)
    cred = 88 if source in ("apple", "steam", "anilist", "gnews") else 80
    has_media = bool(image)
    media = [{"url": image, "source": img_src or SRC_NAME.get(source, source), "caption": ""}] if has_media else []
    ev = {
        "id": stable_id(source, title),
        "titleCn": title_cn,
        "titleOrig": title,
        "catCn": cat_cn,
        "cat": cat,
        "country": country,
        "stars": stars,
        "cover": image,
        "coverType": "remote" if has_media else "placeholder",
        "credibilityScore": cred,
        "buzzIndex": buzz,
        "summary": summary or title_cn,
        "tags": [],
        "timeRel": "",
        "timeAbs": "",
        "sources": [
            {"type": source, "name": SRC_NAME.get(source, source), "region": country, "credibility": cred, "url": url or ""}
        ],
        "sourceBreadth": {"local": country != "多市场", "global": country == "多市场", "social_only": source == "trends24"},
        "timeline": [{"date": now_iso()[:10], "desc": "实时榜单收录", "verified": False, "label": "收录"}],
        "printType": "文字款" if cat in ("platform_search", "music", "gaming", "film_tv", "news") else "",
        "risk": "低",
        "hotDays": (7 if buzz >= 90 else 5 if buzz >= 80 else 3 if buzz >= 70 else 2 if buzz >= 50 else 1),
        "imageSource": (img_src or ("官方接口远程图" if has_media else "分类占位图（无自然配图）")),
        "hasMedia": has_media,
        "media": media,
        "fresh": True,
        "batch": "realtime-" + now_iso()[:10],
        "primaryUrl": url or "",
        "_src": source,
    }
    return ev


# ---------- 各数据源 ----------

def src_trends24(country_code, country_cn):
    evs = []
    try:
        html = fetch_text(f"https://trends24.in/{country_code}/")
        for m in re.finditer(r'href="(https?://(?:twitter|x)\.com/[^"]*?search\?q=[^"]+)"[^>]*>([^<]{2,80})</a>', html):
            url = m.group(1)
            name = m.group(2).strip()
            if name.lower() in ("tweet", "twitter", "x"):
                continue
            evs.append(make_event(
                "trends24", name,
                url=url, country=country_cn, cat="platform_search", cat_cn="平台热搜",
                rank=len(evs) + 1,
                summary=f"{country_cn} Twitter/X 今日热搜：{name}",
            ))
            if len(evs) >= 25:
                break
    except Exception as e:
        print(f"[trends24 {country_code}] 失败: {e}")
    return evs


def src_apple_music(country_code, country_cn):
    evs = []
    try:
        d = fetch_json(f"https://rss.applemarketingtools.com/api/v2/{country_code}/music/most-played/25/songs.json")
        for i, it in enumerate(d["feed"]["results"], 1):
            name = it.get("name", "")
            artist = it.get("artistName", "")
            art = (it.get("artworkUrl100") or "").replace("100x100bb", "600x600bb")
            title = f"{name} - {artist}" if artist else name
            evs.append(make_event(
                "apple", title,
                url=it.get("url", ""), image=art, country=country_cn,
                cat="music", cat_cn="音乐榜单", rank=i,
                summary=f"苹果音乐 {country_cn} 热门歌曲第{i}：{name}（{artist}）",
                img_src="Apple Music 专辑图",
            ))
    except Exception as e:
        print(f"[apple {country_code}] 失败: {e}")
    return evs


def src_steam(top=10):
    evs = []
    try:
        s = fetch_json("https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/")
        appids = [g["appid"] for g in s["response"]["ranks"][:top]]
        for i, aid in enumerate(appids, 1):
            try:
                det = fetch_json(f"https://store.steampowered.com/api/appdetails?appids={aid}&cc=us&l=en")
                d = det.get(str(aid), {})
                if not d.get("success"):
                    continue
                data = d["data"]
                name = data.get("name", "")
                hdr = data.get("header_image", "")
                evs.append(make_event(
                    "steam", name,
                    url=f"https://store.steampowered.com/app/{aid}/", image=hdr,
                    country="多市场", cat="gaming", cat_cn="游戏热度", rank=i,
                    summary=f"Steam 最热门游戏第{i}：{name}",
                    img_src="Steam 封面图",
                ))
            except Exception as e:
                print(f"[steam app {aid}] 跳过: {e}")
    except Exception as e:
        print(f"[steam] 失败: {e}")
    return evs


def src_anilist(top=20):
    evs = []
    try:
        q = 'query($p:Int){Page(perPage:$p){media(sort:TRENDING_DESC,type:ANIME){title{romaji english native}coverImage{medium large extraLarge}siteUrl}}}'
        j = post_json("https://graphql.anilist.co", {"query": q, "variables": {"p": top}})
        for i, m in enumerate(j["data"]["Page"]["media"], 1):
            t = m.get("title", {})
            name = (t.get("english") or t.get("romaji") or t.get("native") or "").strip()
            if not name:
                continue
            cov = (m.get("coverImage", {}).get("extraLarge") or m.get("coverImage", {}).get("large")
                   or m.get("coverImage", {}).get("medium") or "")
            evs.append(make_event(
                "anilist", name,
                url=m.get("siteUrl", ""), image=cov, country="多市场",
                cat="film_tv", cat_cn="动漫热度", rank=i,
                summary=f"AniList 人气动漫第{i}：{name}",
                img_src="AniList 封面图",
            ))
    except Exception as e:
        print(f"[anilist] 失败，回退 MyAnimeList: {e}")
        evs += src_mal(top)
    return evs


def src_mal(top=20):
    evs = []
    try:
        html = fetch_text("https://myanimelist.net/topanime.php")
        for i, m in enumerate(re.finditer(r'<a\b[^>]*class="hoverinfo_trigger"[^>]*>(.*?)</a>', html, re.S), 1):
            a_tag = m.group(0)
            hm = re.search(r'href="([^"]*?/anime/\d+[^"]*)"', a_tag)
            if not hm:
                continue
            url = hm.group(1)
            if url.startswith("/"):
                url = "https://myanimelist.net" + url
            name = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if not name:
                continue
            evs.append(make_event(
                "mal", name,
                url=url, country="多市场", cat="film_tv", cat_cn="动漫热度", rank=i,
                summary=f"MyAnimeList 人气动漫第{i}：{name}",
            ))
            if i >= top:
                break
    except Exception as e:
        print(f"[mal] 失败: {e}")
    return evs


def src_google_news(query, country_cn, hl, gl, ceid, limit=1, cat="news", cat_cn="新闻热点"):
    """按关键词查 Google News RSS，返回带图新闻事件（作为独立数据源，也可被聚合借图）。"""
    evs = []
    try:
        q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"
        xml = fetch_text(url, timeout=12)
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        for it in items[:limit]:
            tm = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
            lm = re.search(r"<link>(.*?)</link>", it, re.S)
            im = (re.search(r'<media:content[^>]*url="([^"]+)"', it)
                  or re.search(r'<enclosure[^>]*url="([^"]+)"', it)
                  or re.search(r'<media:thumbnail[^>]*url="([^"]+)"', it))
            if not tm:
                continue
            title = tm.group(1).strip()
            link = lm.group(1).strip() if lm else ""
            img = im.group(1).strip() if im else ""
            if img and "news.google.com/rss" in img:
                img = ""
            if not title:
                continue
            evs.append(make_event(
                "gnews", title,
                url=link, image=img, country=country_cn,
                cat=cat, cat_cn=cat_cn,
                summary=f"{country_cn}{cat_cn}：{title}",
                img_src="Google 新闻图" if img else "",
            ))
    except Exception as e:
        print(f"[gnews {query}] 失败: {e}")
    return evs


# ---------- 多分类 Google News 查询配置 ----------
GNEWS_QUERIES = [
    ("celebrity entertainment gossip", "celebrity", "明星八卦"),
    ("movie film series drama", "film_tv", "影视剧"),
    ("concert festival tour", "concert_show", "演唱会综艺"),
    ("meme viral trending", "meme", "网络热梗"),
    ("sports football match", "sports", "体育"),
    ("society social community", "society", "社会民生"),
    ("politics election government", "politics", "政党选举"),
    ("ecommerce marketplace policy shop", "ecommerce", "电商政策"),
]


def src_holidays():
    """泰马未来节日静态数据（含印花机会）。"""
    holidays = [
        ("母亲节（泰国母亲节）", "泰国", "母亲节（วันแม่）泰国皇后诞辰，康乃馨/母爱主题印花机会"),
        ("圣纪节（回教先知诞辰）", "马来西亚", "圣纪节 Maulid Nabi，回教节日，绿色/新月主题"),
        ("马来西亚国庆日", "马来西亚", "马来西亚独立日，国旗/爱国主题印花爆款"),
        ("水灯节", "泰国", "水灯节 Loy Krathong，水灯/河灯/浪漫主题印花机会"),
        ("国王诞辰（泰国）", "泰国", "国王诞辰，黄色/皇室主题"),
        ("圣诞节", "多市场", "圣诞主题印花全球爆款"),
        ("元旦", "多市场", "新年主题印花"),
        ("春节", "马来西亚", "农历新年，红色/生肖主题印花（马来华人圈）"),
    ]
    evs = []
    for title, country, summary in holidays:
        evs.append(make_event(
            "holiday", title,
            url="", image="", country=country,
            cat="festival", cat_cn="节日",
            summary=summary,
            img_src="",
        ))
    return evs


def wiki_search_img(query, width=600):
    """维基百科搜索相关页面并返回其缩略图（容错拼写，按实体名搜真实图）。"""
    try:
        q = urllib.parse.quote(query)
        api = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
               "&generator=search&gsrsearch=" + q +
               "&gsrlimit=8&prop=pageimages&piprop=thumbnail&pithumbsize=" + str(width))
        d = fetch_json(api)
        for p in d.get("query", {}).get("pages", {}).values():
            th = p.get("thumbnail", {}).get("source")
            if th:
                return th
    except Exception:
        pass
    return None


def commons_image(query, width=600):
    """维基共享资源按关键词搜图（File 空间）。"""
    try:
        q = urllib.parse.quote(query)
        api = (f"https://commons.wikimedia.org/w/api.php?action=query&format=json"
               f"&generator=search&gsrsearch={q}&gsrnamespace=6&gsrlimit=5"
               f"&prop=imageinfo&iiprop=url&iiurlwidth={width}")
        d = fetch_json(api)
        pages = d.get("query", {}).get("pages", {})
        for p in pages.values():
            ii = (p.get("imageinfo") or [{}])[0]
            u = ii.get("thumburl") or ii.get("url")
            if u:
                return u
    except Exception:
        pass
    return None


def openverse_img(query, timeout=12):
    """Openverse 共享图库（零 Key，返回真实照片），作为最后兜底。"""
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.openverse.org/v1/images/?q={q}&page_size=5"
        d = fetch_json(url, timeout)
        for r in d.get("results", []):
            u = r.get("url")
            if u and u.startswith("http"):
                return u
    except Exception:
        pass
    return None


STOPQ = set("ep id mv off ic rl th my cp the and or x with of to a an in on for".split())


def extract_queries(title):
    """从标题提取用于搜图的候选词（按希望程度排序）。"""
    raw = (title or "").strip()
    qs = [raw]
    parts = []
    for tk in re.findall(r"[A-Za-z][A-Za-z0-9]*", raw):
        parts += re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}|\d+", tk)
    lat = [p for p in parts if p.isalpha() and len(p) >= 2]
    if lat:
        qs.append(" ".join(lat))
        meaningful = [p for p in lat if len(p) >= 3 and p.lower() not in STOPQ]
        for p in meaningful:
            qs.append(p)
        if len(meaningful) >= 2:
            qs.append(" ".join(meaningful[:3]))
    seen, out = set(), []
    for q in qs:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out[:4]


def apply_img(e, url, src_name, src_type):
    """给事件贴图，并把图源作为关联来源并入 sources（实现多源）。"""
    e["cover"] = url
    e["coverType"] = "remote"
    e["media"].append({"url": url, "source": src_name, "caption": ""})
    e["imageSource"] = src_name
    e["hasMedia"] = True
    e["sources"].append({
        "type": src_type, "name": src_name, "region": e["country"],
        "credibility": 82, "url": "",
    })


# ---------- 跨源实体聚合 + 借图 ----------

def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\u0e00-\u0e7f\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


STOP = set("live new show top hot best official trailer mv video song music the a an of and remix feat ft version episode ep season watch full hd lyrics concert tour debut comeback win wins".split())


def match_entities(a, b):
    """两标题指向同一实体（包含关系且非纯停用词）时返回 True。"""
    ka, kb = _norm(a), _norm(b)
    if not ka or not kb:
        return False
    if ka == kb:
        return True
    ta, tb = set(ka.split()), set(kb.split())
    if not ta or not tb:
        return False
    shared = ta & tb
    if not shared or shared <= STOP:
        return False
    longer = max(len(ta), len(tb))
    shorter = min(len(ta), len(tb))
    if (ta <= tb or tb <= ta) and longer <= shorter + 1:
        return True
    return False


def _pick_cat(a, b):
    ra, rb = CAT_RANK.get(a["cat"], 1), CAT_RANK.get(b["cat"], 1)
    return (b["cat"], b["catCn"]) if rb > ra else (a["cat"], a["catCn"])


def merge_into(dst, src):
    """把 src 的信息并入 dst（来源、图片、分类、国家、摘要）。"""
    for s in src["sources"]:
        if not any(s["type"] == x["type"] and s["name"] == x["name"] for x in dst["sources"]):
            dst["sources"].append(dict(s))
    for m in src.get("media", []):
        u = m.get("url")
        if u and not any(x.get("url") == u for x in dst["media"]):
            dst["media"].append(dict(m))
    if not dst.get("cover") and src.get("cover"):
        dst["cover"] = src["cover"]
        dst["coverType"] = "remote"
    # 国家归一
    if dst["country"] != "多市场" and src["country"] != "多市场" and dst["country"] != src["country"]:
        dst["country"] = "多市场"
    elif src["country"] == "多市场":
        dst["country"] = "多市场"
    # 分类取更实质
    dst["cat"], dst["catCn"] = _pick_cat(dst, src)
    dst["credibilityScore"] = max(dst["credibilityScore"], src["credibilityScore"])
    if src["summary"] and src["summary"] not in dst["summary"]:
        dst["summary"] = dst["summary"] + " ｜ " + src["summary"]
    if src.get("imageSource") and not dst.get("cover"):
        dst["imageSource"] = src.get("imageSource")
    if src.get("imageSource") and dst.get("cover"):
        dst["imageSource"] = dst.get("imageSource") + " + " + src.get("imageSource")
    sb = dst["sourceBreadth"]
    ss = src["sourceBreadth"]
    sb["local"] = sb["local"] or ss["local"]
    sb["global"] = sb["global"] or ss["global"]
    sb["social_only"] = sb["social_only"] and ss["social_only"]
    dst["hasMedia"] = bool(dst.get("cover") or dst["media"])


def aggregate(events):
    """trends24 热搜词 ↔ 其他源（apple/steam/anilist/gnews）按实体名合并并借图。"""
    trends = [e for e in events if e.get("_src") == "trends24"]
    others = [e for e in events if e.get("_src") != "trends24"]
    result = []
    used = set()
    for t in trends:
        matches = [o for o in others if id(o) not in used and match_entities(t["titleOrig"], o["titleOrig"])]
        if matches:
            primary = matches[0]
            for o in matches[1:]:
                merge_into(primary, o)
                used.add(id(o))
            merge_into(primary, t)  # 把热搜热度并入主体
            used.add(id(primary))
            result.append(primary)
        else:
            result.append(t)
    for o in others:
        if id(o) not in used:
            result.append(o)
    return result


# ── 知名 IP / 游戏 / 艬人 精确短词表（高热度实体，直接用短词搜图避免长标题空耗）──
KNOWN_IPS = [
    # 游戏
    ("Genshin Impact", "原神"), ("Genshin", "原神"),
    ("Black Myth Wukong", "黑神话悟空"), ("Wukong", "黑神话"),
    ("Honkai Star Rail", "崩坏星穹铁道"), ("Honkai", "崩坏"),
    ("PUBG", "绝地求生"), ("Apex Legends", "Apex英雄"),
    ("Dota 2", "Dota2"), ("Counter-Strike 2", "CS2"),
    ("League of Legends", "英雄联盟"), ("Valorant", "瓦罗兰特"),
    ("Minecraft", "我的世界"), ("Roblox", "Roblox"),
    ("Grand Theft Auto V", "GTA5"), ("GTA V", "GTA5"),
    ("EA Sports FC 26", "FIFA26"),
    # 动漫
    ("Jujutsu Kaisen", "咒术回战"), ("Demon Slayer", "鬼灭之刃"),
    ("Attack on Titan", "进击的巨人"), ("One Piece", "海贼王"),
    ("Naruto", "火影忍者"), ("Dragon Ball", "龙珠"),
    ("Spy x Family", "间谍过家家"), ("Chainsaw Man", "电锯人"),
    # K-Pop / 国际艺人
    ("BLACKPINK", "BLACKPINK"), ("BTS", "BTS"),
    ("NewJeans", "NewJeans"), ("IVE", "IVE"),
    ("Taylor Swift", "泰勒斯威夫特"), ("Adele", "阿黛尔"),
    # 泰国 BL / GMMTV
    ("GMMTV", "GMMTV"), ("LINGORM", "LINGORM"),
]

# ── 终极兜底：知名 IP 硬编码备用图（维基/图库全挂时直接用，永不黑块）──
IP_FALLBACK_IMAGES = {
    "Genshin Impact": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5d/Genshin_Impact_logo.svg/960px-Genshin_Impact_logo.svg.png",
    "Genshin":        "https://upload.wikimedia.org/wikipedia/commons/9/9a/Genshin-gazo.jpg",
    "Black Myth Wukong": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e8/Black_Myth_Wukong_cover_art.jpg/800px-Black_Myth_Wukong_cover_art.jpg",
    "Wukong":          "https://upload.wikimedia.org/wikipedia/en/thumb/e/e8/Black_Myth_Wukong_cover_art.jpg/800px-Black_Myth_Wukong_cover_art.jpg",
    "Honkai Star Rail":"https://upload.wikimedia.org/wikipedia/en/thumb/f/fd/Honkai_Star_Rail_logo.png/800px-Honkai_Star_Rail_logo.png",
    "BLACKPINK":       "https://upload.wikimedia.org/wikipedia/en/thumb/3/36/BLACKPINK_COACHELLA_2019.jpg/800px-BLACKPINK_COACHELLA_2019.jpg",
    "BTS":             "https://upload.wikimedia.org/wikipedia/commons/7/75/BTS_for_Dispatch_2017.jpg",
    "Minecraft":        "https://upload.wikimedia.org/wikipedia/en/thumb/7/74/Minecraft_cover_poster.jpg/800px-Minecraft_cover_poster.jpg",
    "Roblox":           "https://upload.wikimedia.org/wikipedia/en/thumb/aad/Roblox_logo_%282022%29.svg/800px-Roblox_logo_%282022%29.svg.png",
    "League of Legends":"https://upload.wikimedia.org/wikipedia/en/thumb/b/b9/League_of_Legends_2019_vector_logo.svg/800px-League_of_Legends_2019_vector_logo.svg.png",
}

def _ip_match(title):
    """检查标题是否匹配知名 IP，返回 (精确搜图词, 中文名) 或 None。"""
    t = title.lower()
    for keyword, cn in KNOWN_IPS:
        if keyword.lower() in t:
            return keyword, cn
    return None


def enrich_images(events, max_requests=300):
    """对无图事件依次尝试：① 知名 IP 精确匹配 → ② 候选词链(维基→Commons→Openverse)。

    优化：
    - 知名 IP 层优先（头部热点零延迟命中）
    - 高命中率类别（游戏/动漫/音乐）优先处理
    - used 只在实际发起网络请求时计数
    - 每事件最多试 3 个候选词 × 3 源 = 9 次
    """
    # 排序：有英文名的高命中率类别优先（游戏>动漫>音乐>其他）
    PRIORITY = {"gaming": 0, "anime": 1, "music": 2}
    events.sort(key=lambda e: (PRIORITY.get(e.get("cat",""), 99),
                                bool(re.search(r"[A-Za-z]{3,}", e.get("titleOrig","")))))
    used = 0
    for e in events:
        if e.get("cover"):
            continue
        # ── 第一层：知名 IP 精确匹配（头部热点直接命中）──
        ip = _ip_match(e["titleOrig"]) or _ip_match(e.get("titleCn") or "")
        if ip:
            kw, cn_name = ip
            w = wiki_search_img(kw); used += 1
            if w:
                apply_img(e, w, f"维基百科({cn_name})", "wiki"); continue
            if used >= max_requests: continue
            c = commons_image(kw); used += 1
            if c:
                apply_img(e, c, f"维基共享({cn_name})", "commons"); continue
            if used >= max_requests: continue
            o = openverse_img(kw); used += 1
            if o:
                apply_img(e, o, f"Openverse({cn_name})", "openverse"); continue
            # ── 终极兜底：硬编码备用图（API 全挂也不黑块）──
            fb = IP_FALLBACK_IMAGES.get(kw)
            if fb:
                apply_img(e, fb, f"备用图({cn_name})", "fallback"); continue
        # ── 第二层：通用候选词链 ──
        tried = 0
        for q in extract_queries(e["titleOrig"]):
            if e.get("cover") or used >= max_requests or tried >= 3:
                break
            tried += 1
            w = wiki_search_img(q); used += 1
            if w:
                apply_img(e, w, "维基百科词条图", "wiki"); break
            if used >= max_requests:
                break
            c = commons_image(q); used += 1
            if c:
                apply_img(e, c, "维基共享资源图", "commons"); break
            if used >= max_requests:
                break
            o = openverse_img(q); used += 1
            if o:
                apply_img(e, o, "Openverse 共享图库", "openverse"); break
    return events


def collect():
    trends_th = src_trends24("thailand", "泰国")
    trends_ml = src_trends24("malaysia", "马来西亚")
    base = (trends_th + trends_ml
            + src_apple_music("th", "泰国")
            + src_apple_music("my", "马来西亚")
            + src_steam(12)
            + src_anilist(20)
            + src_holidays())

    # Google News：基于热搜词查带图新闻（既是数据源，也能给热搜借图）
    gnews_evs = []
    for e in (trends_th[:12] + trends_ml[:12]):
        cc = e["country"]
        hl, gl, ceid = ("th", "TH", "TH:th") if cc == "泰国" else ("ms", "MY", "MY:ms")
        gnews_evs += src_google_news(e["titleOrig"], cc, hl, gl, ceid, limit=1)
        time.sleep(0.15)

    # 多分类 Google News：每分类查泰+马各3条，覆盖明星/影视/综艺/梗/体育/社会/政治/电商
    for query, cat, cat_cn in GNEWS_QUERIES:
        for cc, hl, gl, ceid in [("泰国", "th", "TH", "TH:th"), ("马来西亚", "ms", "MY", "MY:ms")]:
            gnews_evs += src_google_news(query, cc, hl, gl, ceid, limit=3, cat=cat, cat_cn=cat_cn)
            time.sleep(0.15)

    all_evs = base + gnews_evs
    all_evs = aggregate(all_evs)
    all_evs = enrich_images(all_evs)
    # 去重（同 id）
    seen, out = set(), []
    for e in all_evs:
        if e and e["id"] not in seen:
            seen.add(e["id"])
            out.append(e)
    return out


def load_prev(path):
    try:
        txt = open(path, encoding="utf-8").read()
        m = re.search(r"EVENTS_REALTIME\s*=\s*(\[.*?\]);", txt, re.S)
        if m:
            return json.loads(m.group(1))
    except Exception:
        pass
    return None


def write_out(events, carried=False):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "realtime.js")
    clean = [{k: v for k, v in e.items() if k != "_src"} for e in events]
    txt = "window.EVENTS_REALTIME = " + json.dumps(clean, ensure_ascii=False, indent=1) + ";\n"
    txt += 'window.REALTIME_UPDATED = "' + now_iso() + '";\n'
    txt += "window.REALTIME_CARRIED = " + ("true" if carried else "false") + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return path


def main():
    print("== 印选实时榜单爬虫 v3 开始", now_iso())
    events = collect()
    print(f"== 抓到事件数: {len(events)}")
    if events:
        p = write_out(events, carried=False)
        print(f"== 已写出(新鲜): {p}")
    else:
        prev = load_prev(os.path.join(os.path.dirname(os.path.abspath(__file__)), "realtime.js"))
        if prev:
            p = write_out(prev, carried=True)
            print(f"== 全部源失败，沿用上一版({len(prev)}条)，已推进时间戳: {p}")
        else:
            p = write_out([], carried=True)
            print(f"== 全部源失败且无历史，写出空版(沿用): {p}")


if __name__ == "__main__":
    main()
