#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick v3 — 云端实时榜单爬虫（零 Key · 纯标准库 · 多源 + 自动补图）
每 30 分钟由 GitHub Actions 运行：爬取泰/马双市场 + 全球公开榜单与热搜，
覆盖 平台热搜 / 音乐 / 游戏 / 动漫 / 影视 / 明星 / 热梗 / 世界热点 / 时尚 等类目，
自动为缺图事件联网检索真实配图（Wikimedia Commons 等），生成 realtime.js 推到 Pages。
所有数据源均为免费公开接口，无需任何 API Key / 大模型。
"""
import json
import os
import re
import ssl
import time
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UA_BOT = "TrendPickBot/3.0 (github.com/jijibao986/trendpick-realtime)"
TZ8 = timezone(timedelta(hours=8))

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uff66-\uff9f]")  # 日/韩/中/假名


def now_iso():
    return datetime.now(TZ8).strftime("%Y-%m-%dT%H:%M:%S")


def fetch_text(url, timeout=20, headers=None):
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_json(url, timeout=20, headers=None):
    return json.loads(fetch_text(url, timeout, headers))


def translate(text, to="zh-CN", timeout=6):
    """尽力把外文翻成中文（Google 翻译 gtx 端点，无需 Key）。失败回退原文。"""
    if not text:
        return text
    if CJK.search(text):
        return text  # 已含中日韩文字，直接保留
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
    "mal": "MyAnimeList 榜单",
    "googlenews": "Google News 热讯",
    "anilist": "AniList 榜单",
    "wiki": "维基精选",
}

CRED = {
    "trends24": 80, "apple": 86, "steam": 86, "mal": 86,
    "googlenews": 84, "anilist": 86, "wiki": 90,
}


def make_event(source, title, *, url="", image="", country="多市场",
               cat="other", cat_cn="其他", rank=None, summary=""):
    title = (title or "").strip()
    if not title:
        return None
    title_cn = translate(title)
    stars = "🔥🔥🔥" if (rank and rank <= 3) else ("🔥🔥" if (rank and rank <= 10) else "🔥")
    buzz = max(20, 100 - (rank or 20) * 2)
    cred = CRED.get(source, 80)
    has_media = bool(image)
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
        "printType": "文字款" if cat in ("platform_search", "music", "gaming", "film_tv") else "",
        "risk": "低",
        "hotDays": 1,
        "imageSource": ("官方接口远程图" if has_media else "分类占位图（无自然配图）"),
        "hasMedia": has_media,
        "media": [{"thumb": image}] if has_media else [],
        "fresh": True,
        "batch": "realtime-" + now_iso()[:10],
        "primaryUrl": url or "",
    }
    return ev


# ---------- 原有数据源 ----------

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
                ))
            except Exception as e:
                print(f"[steam app {aid}] 跳过: {e}")
    except Exception as e:
        print(f"[steam] 失败: {e}")
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


# ---------- 新增数据源 ----------

def src_google_news(query, country_cn, cat, cat_cn, hl="en-US", gl="US", ceid="US:en", limit=10):
    evs = []
    try:
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + f"&hl={hl}&gl={gl}&ceid={ceid}"
        xml = fetch_text(url, timeout=20)
        items = re.findall(r"<item>(.*?)</item>", xml, re.S)
        for it in items[:limit]:
            tm = re.search(r"<title>(.*?)</title>", it, re.S)
            lm = re.search(r"<link>(.*?)</link>", it, re.S)
            dm = re.search(r"<description>(.*?)</description>", it, re.S)
            if not tm:
                continue
            title = re.sub(r"<[^>]+>", "", tm.group(1)).strip()
            if not title:
                continue
            link = lm.group(1).strip() if lm else ""
            desc = re.sub(r"<[^>]+>", "", dm.group(1)).strip() if dm else ""
            img = ""
            if dm:
                im = re.search(r'<img[^>]+src="(https://[^"]+)"', dm.group(1))
                if im:
                    img = im.group(1)
            if not img:
                mm = re.search(r'<media:thumbnail[^>]+url="([^"]+)"', it)
                if mm:
                    img = mm.group(1)
            if not img:
                mc = re.search(r'<media:content[^>]+url="([^"]+)"', it)
                if mc:
                    img = mc.group(1)
            evs.append(make_event(
                "googlenews", title,
                url=link, image=img, country=country_cn, cat=cat, cat_cn=cat_cn,
                rank=len(evs) + 1, summary=desc[:200],
            ))
    except Exception as e:
        print(f"[googlenews {query}] 失败: {e}")
    return evs


def src_anilist(media_type, cat, cat_cn, limit=15):
    """AniList GraphQL（免费、无需 Key），动漫/漫画带封面图。"""
    evs = []
    try:
        body = json.dumps({
            "query": ("query($type:MediaType,$n:Int){Page(perPage:$n){media("
                      "sort:POPULARITY_DESC,type:$type){title{romaji english native} "
                      "coverImage{large} siteUrl}}}"),
            "variables": {"type": media_type, "n": limit}
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://graphql.anilist.co", data=body,
            headers={"User-Agent": UA, "Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req, timeout=20, context=CTX).read().decode("utf-8", "ignore"))
        for i, m in enumerate(d["data"]["Page"]["media"], 1):
            t = m.get("title") or {}
            name = t.get("english") or t.get("romaji") or t.get("native") or ""
            if not name:
                continue
            img = (m.get("coverImage") or {}).get("large") or ""
            label = "动漫" if media_type == "ANIME" else "漫画"
            evs.append(make_event(
                "anilist", name,
                url=m.get("siteUrl") or "", image=img, country="多市场",
                cat=cat, cat_cn=cat_cn, rank=i,
                summary=f"AniList 人气{label}第{i}：{name}",
            ))
    except Exception as e:
        print(f"[anilist {media_type}] 失败: {e}")
    return evs


def src_wikipedia():
    evs = []
    try:
        d = datetime.now(TZ8)
        url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{d.year}/{d.month:02d}/{d.day:02d}"
        data = fetch_json(url, timeout=20)
        img_obj = (data.get("image") or {}).get("image") or {}
        img = img_obj.get("source") or ""
        title = (data.get("image") or {}).get("title") or "维基每日精选图"
        if img:
            evs.append(make_event(
                "wiki", title,
                url="https://en.wikipedia.org/wiki/Special:FeedItem", image=img,
                country="多市场", cat="world", cat_cn="世界热点",
                rank=1, summary=f"维基百科每日精选：{title}",
            ))
    except Exception as e:
        print(f"[wiki] 失败: {e}")
    return evs


# ---------- 自动补图（联网检索） ----------

def commons_image(query, width=600):
    """按关键词在 Wikimedia Commons 检索一张真实图片 URL。失败返回空（带 1 次重试）。"""
    for _ in range(2):
        try:
            q = urllib.parse.quote(query[:200])
            url = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                   f"&gsrsearch={q}&gsrnamespace=6&gsrlimit=6&prop=imageinfo&iiprop=url|mime&iiurlwidth={width}&format=json")
            d = fetch_json(url, timeout=15)
            pages = (d.get("query") or {}).get("pages") or {}
            for pid, p in pages.items():
                ii = (p.get("imageinfo") or [{}])[0]
                if ii.get("mime", "").startswith("image"):
                    return ii.get("thumburl") or ii.get("url") or ""
            return ""
        except Exception:
            time.sleep(1.0)
    return ""


# 分类兜底检索词（精确标题搜不到时，按类目搜一张相关的真实网络图）
CAT_QUERY = {
    "platform_search": "social media trend",
    "music": "music concert",
    "gaming": "video game",
    "film_tv": "movie film",
    "celebrity": "celebrity star",
    "meme": "internet meme",
    "world": "breaking news",
    "fashion": "fashion style",
    "other": "trend",
}


def enrich_images(events, cap=140):
    """为缺图事件联网补图：Wikimedia Commons 两层级检索
    （精确原标题 → 类目关键词兜底），带缓存 + 调用上限 + 礼貌延迟。"""
    cache = {}
    calls = 0
    filled = 0
    for e in events:
        if e.get("cover"):
            continue
        key = (e.get("titleOrig") or e.get("titleCn") or "")[:120]
        cat = e.get("cat", "other")
        for q in [key, CAT_QUERY.get(cat, "trend")]:
            if not q:
                continue
            if q in cache:
                img = cache[q]
            else:
                if calls >= cap:
                    img = ""
                else:
                    img = commons_image(q)
                    calls += 1
                    cache[q] = img
                    time.sleep(0.15)
            if img:
                e["cover"] = img
                e["coverType"] = "remote"
                e["hasMedia"] = True
                e["media"] = [{"thumb": img}]
                e["imageSource"] = "Wikimedia Commons 检索图"
                filled += 1
                break
    print(f"== 自动补图：检索 {calls} 次，成功补齐 {filled} 张")
    return events


# ---------- 汇总 ----------

def collect():
    evs = []

    # 平台热搜
    evs += src_trends24("thailand", "泰国")
    evs += src_trends24("malaysia", "马来西亚")
    evs += src_google_news("trending Thailand", "泰国", "platform_search", "平台热搜", hl="th", gl="TH", ceid="TH:th", limit=12)
    evs += src_google_news("trending Malaysia", "马来西亚", "platform_search", "平台热搜", hl="ms", gl="MY", ceid="MY:ms", limit=12)

    # 音乐榜单
    evs += src_apple_music("th", "泰国")
    evs += src_apple_music("my", "马来西亚")
    evs += src_google_news("Kpop new song release", "多市场", "music", "音乐榜单", limit=10)
    evs += src_google_news("Spotify top global", "多市场", "music", "音乐榜单", limit=10)

    # 游戏热度
    evs += src_steam(12)
    evs += src_google_news("video game release", "多市场", "gaming", "游戏热度", limit=12)
    evs += src_google_news("Steam top game", "多市场", "gaming", "游戏热度", limit=8)

    # 动漫 / 漫画
    evs += src_anilist("ANIME", "film_tv", "动漫热度", 18)
    evs += src_anilist("MANGA", "film_tv", "动漫热度", 10)
    evs += src_mal(20)
    evs += src_google_news("anime trending", "多市场", "film_tv", "动漫热度", limit=8)

    # 影视剧
    evs += src_google_news("Netflix new series", "多市场", "film_tv", "影视剧", limit=12)
    evs += src_google_news("box office weekend", "多市场", "film_tv", "影视剧", limit=8)
    evs += src_google_news("หนัง ใหม่", "泰国", "film_tv", "影视剧", limit=8)

    # 明星八卦
    evs += src_google_news("Kpop comeback", "多市场", "celebrity", "明星八卦", limit=12)
    evs += src_google_news("ดารา ไทย", "泰国", "celebrity", "明星八卦", limit=10)
    evs += src_google_news("artis Malaysia", "马来西亚", "celebrity", "明星八卦", limit=10)

    # 网络热梗
    evs += src_google_news("viral meme internet", "多市场", "meme", "网络热梗", limit=12)
    evs += src_google_news("ไวรัล", "泰国", "meme", "网络热梗", limit=8)
    evs += src_google_news("trending meme Malaysia", "马来西亚", "meme", "网络热梗", limit=8)

    # 世界热点
    evs += src_google_news("world news", "多市场", "world", "世界热点", hl="en-US", gl="US", ceid="US:en", limit=12)
    evs += src_google_news("breaking news", "多市场", "world", "世界热点", hl="en-US", gl="US", ceid="US:en", limit=8)

    # 时尚趋势
    evs += src_google_news("fashion trend 2026", "多市场", "fashion", "时尚趋势", limit=10)
    evs += src_google_news("แฟชั่น", "泰国", "fashion", "时尚趋势", limit=8)

    # 维基精选图
    evs += src_wikipedia()

    # 同 id 去重（不同源同标题只留一条，保留先到者）
    seen, out = set(), []
    for e in evs:
        if e and e["id"] not in seen:
            seen.add(e["id"])
            out.append(e)

    # 自动补图
    enrich_images(out, cap=90)
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
    txt = "window.EVENTS_REALTIME = " + json.dumps(events, ensure_ascii=False, indent=1) + ";\n"
    txt += 'window.REALTIME_UPDATED = "' + now_iso() + '";\n'
    txt += "window.REALTIME_CARRIED = " + ("true" if carried else "false") + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return path


def main():
    print("== 印选实时榜单爬虫 v3 开始", now_iso())
    events = collect()
    with_img = sum(1 for e in events if e.get("cover"))
    print(f"== 抓到事件数: {len(events)}，其中含图: {with_img}")
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
