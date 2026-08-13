#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick v2 — 云端实时榜单爬虫（零 Key · 纯标准库）
每小时由 GitHub Actions 运行：爬取泰/马双市场公开榜单与热搜，
生成 realtime.js（window.EVENTS_REALTIME + 元信息），推到 GitHub Pages。
所有数据源均为免费公开接口，无需任何 API Key / 大模型。
"""
import json
import os
import re
import ssl
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TZ8 = timezone(timedelta(hours=8))

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uff66-\uff9f]")  # 日/韩/中/假名


def now_iso():
    return datetime.now(TZ8).strftime("%Y-%m-%dT%H:%M:%S")


def fetch_text(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "ignore")


def fetch_json(url, timeout=20):
    return json.loads(fetch_text(url, timeout))


def translate(text, to="zh-CN", timeout=6):
    """最好尽力把外文翻成中文（Google 翻译 gtx 端点，无需 Key）。失败回退原文。"""
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
}


def make_event(source, title, *, url="", image="", country="多市场",
               cat="other", cat_cn="其他", rank=None, summary=""):
    title = (title or "").strip()
    if not title:
        return None
    title_cn = translate(title)
    # 星级 / 热度按排名给个观感值
    stars = "🔥🔥🔥" if (rank and rank <= 3) else ("🔥🔥" if (rank and rank <= 10) else "🔥")
    buzz = max(20, 100 - (rank or 20) * 2)
    cred = 86 if source in ("apple", "steam", "mal") else 80
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
        # 顺序无关地提取 <a class="hoverinfo_trigger" ...>名称</a>
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


def collect():
    evs = []
    evs += src_trends24("thailand", "泰国")
    evs += src_trends24("malaysia", "马来西亚")
    evs += src_apple_music("th", "泰国")
    evs += src_apple_music("my", "马来西亚")
    evs += src_steam(12)
    evs += src_mal(20)
    # 同 id 去重（不同源同标题只留一条）
    seen, out = set(), []
    for e in evs:
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
    txt = "window.EVENTS_REALTIME = " + json.dumps(events, ensure_ascii=False, indent=1) + ";\n"
    txt += 'window.REALTIME_UPDATED = "' + now_iso() + '";\n'
    txt += "window.REALTIME_CARRIED = " + ("true" if carried else "false") + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return path


def main():
    print("== 印选实时榜单爬虫 开始", now_iso())
    events = collect()
    print(f"== 抓到事件数: {len(events)}")
    if events:
        p = write_out(events, carried=False)
        print(f"== 已写出(新鲜): {p}")
    else:
        # 沿用版兜底：保留上一版数据，仅推进时间戳
        prev = load_prev(os.path.join(os.path.dirname(os.path.abspath(__file__)), "realtime.js"))
        if prev:
            p = write_out(prev, carried=True)
            print(f"== 全部源失败，沿用上一版({len(prev)}条)，已推进时间戳: {p}")
        else:
            p = write_out([], carried=True)
            print(f"== 全部源失败且无历史，写出空版(沿用): {p}")


if __name__ == "__main__":
    main()
