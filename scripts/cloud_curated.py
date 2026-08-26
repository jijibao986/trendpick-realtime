#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印选 TrendPick — 纯云端研究爬虫（零 Key / 零第三方库）

每天由 GitHub Actions `daily-curated.yml` 调用，从免费公开源抓取泰马双市场热点，
产出 SCHEMA_v2 结构事件 JSON，供后续 merge -> 配图 -> 门禁 -> 发布 使用。

设计原则：
- 纯标准库（urllib / json / re），与 scrape_realtime.py 同范式，Ubuntu Runner 直接跑。
- 每个数据源独立 try/except，单源失败不影响其他源。
- 翻译用免 Key 谷歌翻译接口（translate.googleapis.com?client=gtx）。
- 若全部源失败 -> 写空数组 + cloud_status.carried=true（沿用版兜底）。
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.parse, random, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRESH_DIR = os.path.join(ROOT, "fresh")
os.makedirs(FRESH_DIR, exist_ok=True)

TODAY = datetime.date.today().strftime("%Y-%m-%d")
BATCH = "cloud-" + TODAY
NOW = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CAT_MAP = {
    "明星八卦": "celebrity", "演唱会综艺": "concert_show", "音乐热歌": "celebrity",
    "影视剧": "film_tv", "动漫": "film_tv", "游戏电竞": "gaming", "网络热梗": "meme",
    "社会民生": "society", "体育": "sports", "政治": "politics", "电商政策": "ecommerce",
    "平台热搜": "platform_search", "其他热搜": "other", "节日": "society",
}
ENUM = (set(CAT_MAP.values()) |
        {"celebrity", "concert_show", "film_tv", "gaming", "meme",
         "other", "society", "sports", "politics", "ecommerce", "platform_search"})

REGION_CN = {"th": "泰国", "my": "马来西亚", "multi": "多市场"}

events = []
seen_titles = set()


# ----------------------------- 网络 / 工具 -----------------------------
def fetch_text(url, timeout=15, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA,
                              "Accept-Language": "th-TH,my-MY,en;q=0.8,zh-CN;q=0.7"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            for enc in ("utf-8", "utf-8-sig", "tis-620", "cp1252"):
                try:
                    return data.decode(enc)
                except Exception:
                    continue
            return data.decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.2)
    return ""


def fetch_json(url, timeout=15):
    txt = fetch_text(url, timeout=timeout)
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        return None


def translate(text, to="zh-CN"):
    if not text or re.search(r"[一-鿿]", text):
        return text  # 已含中文 -> 原样
    try:
        q = urllib.parse.quote(text)
        url = ("https://translate.googleapis.com/translate_a/single?client=gtx"
               "&sl=auto&tl=%s&dt=t&q=%s" % (to, q))
        txt = fetch_text(url, timeout=10)
        if not txt:
            return text
        data = json.loads(txt)
        parts = [seg[0] for seg in data[0] if seg[0]]
        return "".join(parts) or text
    except Exception:
        return text


def stable_id(prefix, title):
    return hashlib.md5((prefix + "|" + title).encode("utf-8")).hexdigest()[:24]


def clean_query(s):
    s = re.sub(r"#", "", s or "")
    s = re.sub(r"[（(][^)）]*[)）]", "", s)
    s = re.sub(r"[^A-Za-z0-9 \-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:60]


def strip_tags(html_frag):
    return re.sub(r"<[^>]+>", "", html_frag or "").strip()


# ----------------------------- 事件构造 -----------------------------
def add_event(title_orig, *, cat_cn, cat, country, src_name, src_type,
              url, credibility, region, rank=None, summary="", keywords=None,
              image_query=None):
    title = (title_orig or "").strip()
    if not title:
        return
    key = title.lower()
    if key in seen_titles:
        return
    seen_titles.add(key)

    tc = translate(title)
    if rank is not None:
        try:
            rk = int(rank)
        except Exception:
            rk = 20
        buzz = max(20, 100 - rk * 2)
        stars = max(1, min(5, 5 - rk // 4))
    else:
        buzz = random.randint(58, 82)
        stars = random.randint(2, 4)

    if cat not in ENUM:
        cat = CAT_MAP.get(cat_cn, "other")

    cred_label = "高" if credibility >= 85 else ("中" if credibility >= 75 else "低")
    iq = image_query or clean_query(title)
    kw = keywords or [iq]

    ev = {
        "id": stable_id("cloud", title),
        "batch": BATCH,
        "fresh": True,
        "country": country,
        "cat": cat,
        "catCn": cat_cn,
        "stars": stars,
        "printType": "文字+图案",
        "risk": "低风险",
        "hotDays": random.randint(7, 30),
        "titleCn": tc,
        "titleOrig": title,
        "summary": summary or (
            "%s 是近期%s%s热点，相关话题在社媒与榜单持续升温，"
            "适合作为印花T恤题材开发，建议结合视觉梗点做文字+图案款。" % (
                tc, REGION_CN.get(country, "多市场"), cat_cn)),
        "tags": kw[:6],
        "credibilityScore": credibility,
        "buzzIndex": buzz,
        "sources": [{
            "name": src_name, "type": src_type, "url": url,
            "credibility": cred_label, "region": region,
            "mention": int(rank) if rank else 0,
        }],
        "sourceBreadth": {
            "local": 1 if region in ("th", "my") else 0,
            "global": 1,
            "social_only": 1 if src_type == "social" else 0,
        },
        "timeline": [{"date": TODAY, "label": "当日热点", "desc": "入选印选每日云端精选"}],
        "primaryUrl": url,
        "imageQuery": iq,
        "keywords": kw,
        "cover": "",
        "coverType": "",
        "hasMedia": False,
        "media": [],
    }
    events.append(ev)


# ----------------------------- 数据源 -----------------------------
def scrape_trends24(country_code, country, limit=12):
    url = "https://trends24.in/%s/" % country_code
    html = fetch_text(url)
    if not html:
        return 0
    cands = []
    # trends24 把热搜放在 <a href="...trends24...">词</a> 或 <td>词</td>
    for m in re.finditer(r'<a[^>]*href="[^"]*trends24[^"]*"[^>]*>([^<]+)</a>', html):
        cands.append(m.group(1).strip())
    if not cands:
        for m in re.finditer(r'<td[^>]*>([^<]{2,60})</td>', html):
            t = strip_tags(m.group(1)).strip()
            if t and "trend" not in t.lower():
                cands.append(t)
    cnt = 0
    for t in cands:
        t = t.strip()
        if not t or len(t) > 60 or t.lower().startswith("http"):
            continue
        add_event(t, cat_cn="网络热梗", cat="meme", country=country,
                  src_name="trends24 %s" % country_code, src_type="social",
                  url=url, credibility=72, region=country, rank=cnt + 1)
        cnt += 1
        if cnt >= limit:
            break
    return cnt


def scrape_getdaytrends(country_code, country, limit=8):
    url = "https://getdaytrends.com/%s/" % country_code
    html = fetch_text(url)
    if not html:
        return 0
    cands = re.findall(r'<a[^>]*href="[^"]*getdaytrends[^"]*"[^>]*>([^<]+)</a>', html)
    if not cands:
        cands = re.findall(r'<td[^>]*>([^<]{2,60})</td>', html)
    cnt = 0
    for t in cands:
        t = strip_tags(t).strip()
        if not t or len(t) > 60 or t.lower().startswith("http"):
            continue
        add_event(t, cat_cn="平台热搜", cat="platform_search", country=country,
                  src_name="GetDayTrends %s" % country_code, src_type="social",
                  url=url, credibility=72, region=country, rank=cnt + 1)
        cnt += 1
        if cnt >= limit:
            break
    return cnt


def scrape_apple_music(region, country, limit=8):
    url = ("https://rss.applemarketingtools.com/api/v2/%s/music/most-played/10/songs.json"
           % region)
    data = fetch_json(url)
    if not data:
        return 0
    entries = (data.get("feed") or {}).get("entry") or []
    cnt = 0
    for e in entries[:limit]:
        try:
            name = e["im:name"]["label"]
            artist = e["im:artist"]["label"]
            title = "%s - %s" % (name, artist)
        except Exception:
            continue
        add_event(title, cat_cn="音乐热歌", cat="celebrity", country=country,
                  src_name="Apple Music %s Top Songs" % region, src_type="chart",
                  url=url, credibility=88, region=country, rank=cnt + 1,
                  keywords=[name, artist])
        cnt += 1
    return cnt


def scrape_jikan(limit=8):
    url = "https://api.jikan.moe/v4/top/anime?filter=bypopularity&limit=%d" % limit
    data = fetch_json(url)
    if not data:
        return 0
    cnt = 0
    for a in (data.get("data") or [])[:limit]:
        title = a.get("title") or a.get("title_english") or ""
        if not title:
            continue
        add_event(title, cat_cn="动漫", cat="film_tv", country="multi",
                  src_name="MyAnimeList (Jikan) Top", src_type="chart",
                  url=a.get("url", "https://myanimelist.net/topanime.php"),
                  credibility=88, region="global",
                  keywords=[title], image_query=title)
        cnt += 1
    return cnt


def scrape_steam(limit=8):
    url = "https://store.steampowered.com/charts/topselling/global"
    html = fetch_text(url)
    if not html:
        return 0
    names = re.findall(r'class="tab_item_name"[^>]*>([^<]+)</div>', html)
    if not names:
        names = re.findall(r'<span class="title">([^<]+)</span>', html)
    cnt = 0
    for n in names[:limit]:
        n = strip_tags(n).strip()
        if not n:
            continue
        add_event(n, cat_cn="游戏电竞", cat="gaming", country="multi",
                  src_name="Steam 全球热销榜", src_type="chart",
                  url=url, credibility=88, region="global",
                  keywords=[n], image_query=n)
        cnt += 1
    return cnt


def scrape_gnews(query, hl, gl, ceid, cat_cn, cat, country, region, limit=6):
    url = ("https://news.google.com/rss/search?q=%s&hl=%s&gl=%s&ceid=%s"
           % (urllib.parse.quote(query), hl, gl, ceid))
    xml = fetch_text(url)
    if not xml:
        return 0
    items = re.findall(r"<item>(.*?)</item>", xml, re.S)
    cnt = 0
    for it in items[:limit]:
        m = re.search(r"<title>(.*?)</title>", it, re.S)
        if not m:
            continue
        title = strip_tags(m.group(1)).strip()
        # Google News 标题常带 " - 媒体名"
        title = re.split(r"\s+-\s+", title)[0].strip()
        if not title or len(title) > 80:
            continue
        add_event(title, cat_cn=cat_cn, cat=cat, country=country,
                  src_name="Google News (%s)" % query, src_type="news",
                  url=url, credibility=80, region=region,
                  keywords=[title])
        cnt += 1
    return cnt


def scrape_holidays():
    # 泰马近期固定节日（静态数据，提供印花机会与紧急度）
    hol = [
        ("Merdeka 马来西亚独立日（独立日）", "my", "society", 8, "红",
         "马来西亚国庆，国旗/虎纹/独立宣言主题印花强需求"),
        ("Malaysia Day 马来西亚日（马来西亚日）", "my", "society", 9, "红",
         "9/16 马来西亚日，民族融合主题印花"),
        ("Mid-Autumn Festival 中秋节（中秋节）", "multi", "society", 9, "黄",
         "月饼/玉兔/灯笼图案款，跨文化通用"),
        ("Deepavali 屠妖节（排灯节）", "my", "society", 10, "黄",
         "印度裔节日，油灯/孔雀/曼海蒂图案高溢价"),
        ("Songkran 宋干节（泰国新年泼水节）", "th", "society", 4, "绿",
         "年度最强印花季，水花/大象/传统纹样"),
        ("Loy Krathong 水灯节（水灯节）", "th", "society", 11, "黄",
         "河灯/孔雀/泰式金箔图案"),
    ]
    cnt = 0
    for name, country, cat, month, urgency, note in hol:
        add_event(name, cat_cn="节日", cat="society", country=country,
                  src_name="公共假期日历", src_type="other",
                  url="https://www.timeanddate.com/holidays/",
                  credibility=80, region=country,
                  summary="%s（紧急度%s）。%s。" % (name, urgency, note),
                  keywords=[name.split()[0]])
        cnt += 1
    return cnt


# ----------------------------- 主流程 -----------------------------
def main():
    stats = {}
    try:
        stats["trends24_th"] = scrape_trends24("thailand", "th")
    except Exception:
        stats["trends24_th"] = 0
    try:
        stats["trends24_my"] = scrape_trends24("malaysia", "my")
    except Exception:
        stats["trends24_my"] = 0
    try:
        stats["getday_th"] = scrape_getdaytrends("thailand", "th")
    except Exception:
        stats["getday_th"] = 0
    try:
        stats["getday_my"] = scrape_getdaytrends("malaysia", "my")
    except Exception:
        stats["getday_my"] = 0
    try:
        stats["apple_th"] = scrape_apple_music("th", "th")
    except Exception:
        stats["apple_th"] = 0
    try:
        stats["apple_my"] = scrape_apple_music("my", "my")
    except Exception:
        stats["apple_my"] = 0
    try:
        stats["jikan"] = scrape_jikan()
    except Exception:
        stats["jikan"] = 0
    try:
        stats["steam"] = scrape_steam()
    except Exception:
        stats["steam"] = 0

    gnews_jobs = [
        ("celebrity Thailand BL K-pop", "th", "TH", "TH:th", "明星八卦", "celebrity", "th", "th"),
        ("movie series drama Thailand", "th", "TH", "TH:th", "影视剧", "film_tv", "th", "th"),
        ("game esports Mobile Legends Thailand", "th", "TH", "TH:th", "游戏电竞", "gaming", "th", "th"),
        ("Malaysia entertainment selebriti", "ms", "MY", "MY:ms", "明星八卦", "celebrity", "my", "my"),
        ("Malaysia filem drama", "ms", "MY", "MY:ms", "影视剧", "film_tv", "my", "my"),
        ("ecommerce Shopee Lazada policy Malaysia", "ms", "MY", "MY:ms", "电商政策", "ecommerce", "my", "my"),
        ("Thailand viral meme trend", "th", "TH", "TH:th", "网络热梗", "meme", "th", "th"),
        ("Malaysia football match", "ms", "MY", "MY:ms", "体育", "sports", "my", "my"),
        ("Thailand politics election", "th", "TH", "TH:th", "政治", "politics", "th", "th"),
    ]
    for q, hl, gl, ceid, cat_cn, cat, country, region in gnews_jobs:
        try:
            k = "gnews_%s" % cat
            stats[k] = stats.get(k, 0) + scrape_gnews(
                q, hl, gl, ceid, cat_cn, cat, country, region)
        except Exception:
            pass

    try:
        stats["holidays"] = scrape_holidays()
    except Exception:
        stats["holidays"] = 0

    carried = len(events) == 0
    out_json = os.path.join(FRESH_DIR, "cloud_events_%s.json" % TODAY)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=1)
    status = {"date": TODAY, "count": len(events), "carried": carried,
              "stats": stats, "generated_at": NOW}
    with open(os.path.join(FRESH_DIR, "cloud_status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)

    print("cloud_curated done: events=%d carried=%s" % (len(events), carried))
    print("stats:", json.dumps(stats, ensure_ascii=False))
    # 即使全失败也以 0 退出，让 workflow 走沿用版兜底
    sys.exit(0)


if __name__ == "__main__":
    main()
