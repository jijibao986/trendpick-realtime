# -*- coding: utf-8 -*-
"""fetch_real_images.py  v5（全源真实图 · 不限版权 · 同 IP 跨事件复用）

为 data.js 每条热点抓取主题相关真实图片。
铁律：只用真实图片，绝不生成/使用 AI 图。抓不到留空。

v5 核心升级：
  • 放开版权限制：凡是能抓到的真实图都用（维基 non-free 海报 / 新闻站 og:image / 官方站品牌图），
    来源字段标注清楚，仅作参考聚合展示。
  • 同 IP 跨事件复用：泰马大量「网络热梗/明星/影视」事件是同一 CP/剧名/明星的变体
    （绘梦婚礼日 / LINGORM ILF / #วาดฝันวันวิวาห์EP7 均指向 LingOrm）。
    用 TOPIC_ALIASES 把变体归并到同一主题，首次解析成功后缓存，后续变体直接复用，
    覆盖率与效率大幅提升。
  • 图片源：维基 summary(含 non-free) → 维基 pageimages → AniList → 维基 opensearch 动态纠正
    → 泰文维基 → og:image(具体文章/官方站) → YouTube 缩略图。
"""
import json, os, re, time, urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.dirname(HERE)
DATA_JS = os.path.join(HERE, "data.js")
REAL_DIR = os.path.join(SITE_ROOT, "img", "real")
os.makedirs(REAL_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

CACHE_QUERY = {}   # (lang, query_lower) -> (img_url_or_None, src_desc_or_None)
CACHE_URL = {}     # img_url -> 本地相对路径(已下载)
TOPIC_CACHE = {}   # topic -> (img_url_or_None, src_desc_or_None)

OG_BLOCK = {
    "twitter.com", "x.com", "tiktok.com", "ads.tiktok.com", "instagram.com",
    "facebook.com", "fb.com", "getdaytrends.com", "trends24.in", "reddit.com",
    "youtube.com", "youtu.be", "pinterest.com", "threads.net", "linkedin.com", "t.co",
}


# ── 主题别名表：把同 IP 的多种写法归并到同一主题 ───────────────
TOPIC_ALIASES = [
    ("lingorm", ["lingorm", "绘梦婚礼日", "the secret of us", "วาดฝันวันวิวาห์", "orm", "ilf"]),
    ("zeenunew", ["zeenunew", "ซีนุนิว", "zee pruk", "zee nunew"]),
    ("lmsy", ["lmsy", "แอลเอ็มเอสวาย"]),
    ("william", ["william", "วิลเลียม", "williamest", "wesley"]),
    ("perthsanta", ["perthsanta", "perth santa", "perth tanapon"]),
    ("skynani", ["skynani", "sky nani", "destiny"]),
    ("milklove", ["milklove", "milk love"]),
    ("geminifourth", ["geminifourth", "gemini fourth", "monchhichi", "蒙奇奇"]),
    ("duang", ["duang", "duanggoround", "duang go round"]),
    ("nct127", ["nct 127", "nct127"]),
    ("chaeyoung", ["chaeyoung"]),
    ("enhypen", ["enhypen"]),
    ("mlbb", ["mlbb", "mobile legends"]),
    ("roblox", ["roblox", "blox fruits"]),
    ("labubu", ["labubu"]),
    ("mariogalaxy", ["super mario galaxy", "mario galaxy"]),
    ("hoyofest", ["hoyofest", "hoyo", "mihoyo", "miho yo"]),
    ("spiderman", ["spider-man", "spiderman", "蜘蛛侠"]),
    ("peachandme", ["peach and me", "peachandme", "小桃"]),
    ("adogandplane", ["a dog and a plane", "adogandplane", "一只狗和一架飞机"]),
    ("weirdo101", ["weirdo101", "weirdo", "怪人101"]),
    ("moonshadow", ["moonshadow", "月影"]),
    ("f4thailand", ["f4 thailand", "f4 ไทย", "f4"]),
    ("bluedragon", ["blue dragon", "bluedragon", "青龙剧集奖"]),
    ("ch3girlscup", ["ch3 girls cup", "ch3girlscup", "三台女星杯"]),
    ("mothersday", ["mother", "母亲节", "茉莉", "jasmine", "วันแม่"]),
    ("muaythai", ["muay thai", "泰拳"]),
    ("euro2026", ["euro 2026", "euro2026"]),
    ("psd", ["psd mogul", "psd ", "mogul arrival"]),
    ("crybaby", ["crybaby", "proxie", "爱哭鬼"]),
    ("bowkylion", ["bowkylion"]),
    ("wawa", ["wawa", "teetee", "pawpaw"]),
    ("ving", ["วิ้งก์", "ving", "辣妈"]),
    ("uniqlout", ["uniqlo ut", "集英社", "shueisha"]),
    ("fayeatom", ["fayeatom", "faye atom", "faye peraya", "เฟย์ เปรยารา"]),
    ("matchpoint", ["matchpoint", "match point", "赛点系列", "赛点"]),
    ("ohmpawat", ["ohm pawat", "ohmpawat", "โอม ภวัต"]),
    ("charlotte", ["charlotte", "ชาร์เลท วาศิตา", "ชาร์เลต"]),
    ("phuwin", ["phuwin", "ภูวินทร์", "phuwin tangsakyuen"]),
    ("daou", ["daou", "ดาว เพชรสุทธิ์", "daou penthor"]),
    ("shinee", ["shinee", "ชายนี"]),
    ("youngohm", ["youngohm", "ยังโอม", "young ohm"]),
    ("knp", ["knp", "khaotung", "กnap"]),
    ("kengnamping", ["kengnamping", "keng naming", "เก่ง นัมปิง", "uniffresh"]),
    ("jayna", ["jayna", "เจน่า", "jayna kloset"]),
    ("lookkaew", ["lookkaew", "ลูกแก้ว", "born to shine", "生而闪耀"]),
    ("tuktuk", ["tuk tuk", "รถตุ๊กตุ๊ก", "突突车", "tuk-tuk"]),
]

# 每个主题的最佳解析策略：wiki(英文标题) / wiki_th(泰文标题) / og(官方/文章站 URL)
TOPIC_TABLE = {
    "lingorm":      {"wiki": "The_Secret_of_Us", "wiki_th": "เดอะซีเคร็ตออฟอัส", "og": "https://www.gmm25.com/"},
    "zeenunew":     {"wiki": "Zee_Pruk", "wiki_th": "ซีนุนิว", "og": "https://www.gmm25.com/"},
    "lmsy":         {"wiki": "LMSY", "wiki_th": "แอลเอ็มเอสวาย", "og": "https://www.gmm25.com/"},
    "william":      {"wiki": "William_Jakrapatr", "wiki_th": "วิลเลียม จักรภัทร", "og": "https://www.gmm25.com/"},
    "perthsanta":   {"wiki": "Perth_Tanapon", "wiki_th": "เปร์ธ สันตะวา", "og": "https://www.gmm25.com/"},
    "skynani":      {"wiki": "Sky_Nani", "wiki_th": "สกาย นานี่", "og": "https://www.gmm25.com/"},
    "milklove":     {"wiki": "MilkLove", "wiki_th": "มิลค์เลิฟ", "og": "https://www.gmm25.com/"},
    "geminifourth": {"wiki": "GeminiFourth", "wiki_th": "เจมินี่โฟร์ธ", "og": "https://www.gmm25.com/"},
    "duang":        {"wiki": "Duang_(Thai_singer)", "wiki_th": "ดูง", "og": "https://www.gmm25.com/"},
    "nct127":       {"wiki": "NCT_127"},
    "chaeyoung":    {"wiki": "Chaeyoung"},
    "enhypen":      {"wiki": "Enhypen"},
    "mlbb":         {"wiki": "Mobile_Legends:_Bang_Bang", "og": "https://mobilelegends.com/"},
    "roblox":       {"wiki": "Roblox", "og": "https://www.roblox.com/"},
    "labubu":       {"wiki": "Labubu", "og": "https://www.popmart.com/"},
    "mariogalaxy":  {"wiki": "The_Super_Mario_Galaxy_Movie", "og": "https://www.nintendo.com/"},
    "hoyofest":     {"wiki": "MiHoYo", "og": "https://hoyofest.hoyoverse.com/"},
    "spiderman":    {"wiki": "Spider-Man"},
    "peachandme":   {"og": "https://www.gmm25.com/"},
    "adogandplane": {"og": "https://www.gmm25.com/"},
    "weirdo101":    {"og": "https://www.gmm25.com/"},
    "moonshadow":   {"og": "https://www.gmm25.com/"},
    "f4thailand":   {"og": "https://www.gmm25.com/"},
    "bluedragon":   {"wiki": "Blue_Dragon_Series_Awards", "og": "https://www.gmm25.com/"},
    "ch3girlscup":  {"og": "https://www.gmm25.com/"},
    "mothersday":   {"wiki": "Mother's_Day", "wiki_th": "วันแม่"},
    "muaythai":     {"wiki": "Muay_Thai", "wiki_th": "มวยไทย"},
    "euro2026":     {"wiki": "UEFA", "wiki_th": "ยูฟ่า"},
    "psd":          {"og": "https://www.gmm25.com/"},
    "crybaby":      {"wiki": "PROXIE", "og": "https://www.gmm25.com/"},
    "bowkylion":    {"wiki": "Bowkylion", "og": "https://www.billboard.com/"},
    "wawa":         {"og": "https://www.gmm25.com/"},
    "ving":         {"og": "https://www.gmm25.com/"},
    "uniqlout":     {"wiki": "UNIQLO_UT", "og": "https://www.uniqlo.com/"},
    "fayeatom":     {"wiki": "Faye_Peraya", "wiki_th": "เฟย์ เปรยารา", "og": "https://www.gmmtv.com/", "mname": "Faye Peraya"},
    "matchpoint":   {"wiki_th": "Match_Point_(TV_series)", "og": "https://www.gmmtv.com/"},
    "ohmpawat":     {"wiki_th": "โอม ภวัต", "og": "https://www.gmmtv.com/"},
    "charlotte":    {"wiki_th": "ชาร์เลท วาศิตา", "og": "https://www.gmmtv.com/", "mname": "Charlotte Austin"},
    "phuwin":       {"wiki_th": "ภูวินทร์ ตั้งสกุล", "og": "https://www.gmmtv.com/", "mname": "Phuwin Tangsakyuen"},
    "daou":         {"wiki_th": "ดาว เพชรสุทธิ์", "og": "https://www.gmmtv.com/", "mname": "Daou Penthor"},
    "shinee":       {"wiki": "Shinee", "og": "https://www.gmmtv.com/"},
    "youngohm":     {"wiki_th": "ยังโอม", "og": "https://www.gmmtv.com/"},
    "knp":          {"wiki": "Khaotung", "og": "https://www.gmmtv.com/"},
    "kengnamping":  {"mname": "Keng Namping", "og": "https://www.gmmtv.com/"},
    "jayna":        {"mname": "Jayna", "og": "https://www.gmmtv.com/"},
    "lookkaew":     {"mname": "Lookkaew", "og": "https://www.gmmtv.com/"},
    "tuktuk":       {"commons": "Tuk-tuk in Bangkok"},
    "chaeyoung":    {"wiki": "Chaeyoung", "mname": "Chaeyoung"},
}


def read_events():
    s = open(DATA_JS, encoding="utf-8").read()
    arr = s[s.index("["):s.rindex("]") + 1]
    return json.loads(arr)


def save_events(events):
    s = open(DATA_JS, encoding="utf-8").read()
    head = s[:s.index("window.EVENTS")]
    out = head + "window.EVENTS = " + json.dumps(events, ensure_ascii=False, indent=1) + ";\n"
    open(DATA_JS, "w", encoding="utf-8").write(out)


def http_get_json(url, timeout=20, tries=3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(1.5 + attempt * 1.5)
            else:
                break
        except Exception as e:
            last = e
            time.sleep(0.8)
    return None


def http_get_raw(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wiki_summary_image(title, lang="en"):
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    d = http_get_json(url)
    if d:
        thumb = d.get("thumbnail", {}).get("source", "")
        if thumb and thumb.startswith("http"):
            return thumb, d.get("title", title)
    return None, None


def wiki_pageimage(title, lang="en"):
    api = f"https://{lang}.wikipedia.org/w/api.php"
    params = {"action": "query", "prop": "pageimages",
              "piprop": "thumbnail", "pithumbsize": 500,
              "titles": title, "format": "json"}
    d = http_get_json(api + "?" + urllib.parse.urlencode(params))
    if d:
        pages = d.get("query", {}).get("pages", {})
        for pid, pg in pages.items():
            if pid == "-1":
                continue
            if "thumbnail" in pg:
                return pg["thumbnail"]["source"], pg.get("title", title)
    return None, None


def wiki_resolve(title, lang="en"):
    """summary → pageimage，任一命中即返回"""
    img, rt = wiki_summary_image(title, lang)
    if img:
        return img, rt
    return wiki_pageimage(title, lang)


def wiki_search(query, lang="en", limit=3):
    api = f"https://{lang}.wikipedia.org/w/api.php"
    params = {"action": "query", "list": "search",
              "srsearch": query, "srlimit": limit, "format": "json"}
    try:
        d = http_get_json(api + "?" + urllib.parse.urlencode(params))
        for hit in d.get("query", {}).get("search", []):
            t = hit.get("title", "")
            if t:
                return t
    except Exception:
        pass
    return None


def anilist_cover(query):
    url = "https://graphql.anilist.co"
    body = {
        "query": "query($s:String){Media(search:$s,type:ANIME){coverImage{medium}title{romaji}}}",
        "variables": {"s": query},
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                      headers={**UA, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        media = d.get("data", {}).get("Media")
        if media and media.get("coverImage", {}).get("medium"):
            return media["coverImage"]["medium"]
    except Exception:
        pass
    return None


def clean_query(raw):
    s = (raw or "").split("（")[0].split("(")[0]
    s = s.replace("#", "").replace("_", " ").strip()
    s = re.sub(r'\b(Season\s*\d+|Second|Final|Arc|EP\d+)\b.*', '', s, flags=re.I)
    return s.strip()


def thai_substring(raw):
    m = re.search(r'[\u0E00-\u0E7F]+', raw or "")
    return m.group(0) if m else None


KNOWN_ENTITY_MAP = {
    "bts": [("wiki_summary_en", "BTS", "en")],
    "blackpink lisa": [("wiki_summary_en", "BLACKPINK", "en")],
    "lisa": [("wiki_summary_en", "BLACKPINK", "en")],
    "nct 127": [("wiki_summary_en", "NCT_127", "en")],
    "swim": [("wiki_summary_en", "BTS", "en")],
    "golden": [("wiki_summary_en", "BLACKPINK", "en")],
    "mlbb": [("wiki_summary_en", "Mobile_Legends:_Bang_Bang", "en")],
    "mobile legends": [("wiki_summary_en", "Mobile_Legends:_Bang_Bang", "en")],
    "roblox": [("wiki_summary_en", "Roblox", "en")],
    "blox fruits": [("wiki_summary_en", "Blox_Fruits", "en")],
    "genshin": [("wiki_summary_en", "Genshin_Impact", "en")],
    "pokemon": [("wiki_summary_en", "Pokémon", "en")],
    "kpop demon hunters": [("wiki_summary_en", "KPop_Demon_Hunters", "en")],
    "蜘蛛侠": [("wiki_summary_en", "Spider-Man", "en")],
    "spider-man": [("wiki_summary_en", "Spider-Man", "en")],
    "奥德赛": [("wiki_summary_en", "The_Odyssey_(2026_film)", "en")],
    "绘梦婚礼日": [("wiki_summary_en", "The_Secret_of_Us", "en")],
    "the secret of us": [("wiki_summary_en", "The_Secret_of_Us", "en")],
    "lingorm": [("wiki_summary_en", "LingOrm", "en")],
    "zee nunew": [("wiki_summary_en", "Zee_Pruk", "en"), ("wiki_summary_th", "Zee_Nunew", "th")],
    "lmsy": [("wiki_summary_th", "LMSY", "th"), ("wiki_summary_en", "LMSY", "en")],
    "william jakrapatr": [("wiki_summary_th", "William_Jakrapatr", "th")],
    "duang": [("wiki_summary_en", "Duang_(Thai_singer)", "en")],
    "uniqlo ut": [("wiki_summary_en", "UNIQLO_UT", "en")],
    "labubu": [("wiki_summary_en", "Labubu", "en")],
    "siti nurhaliza": [("wiki_summary_en", "Siti_Nurhaliza", "en")],
    "super mario galaxy": [("wiki_summary_en", "The_Super_Mario_Galaxy_Movie", "en")],
    "perth santa": [("wiki_summary_en", "Perth_Santa", "en")],
    "skynani": [("wiki_summary_en", "Sky_Nani", "en")],
    "milklove": [("wiki_summary_en", "MilkLove", "en")],
    "gemini fourth": [("wiki_summary_en", "GeminiFourth", "en")],
}


def build_candidates(ev):
    q = clean_query(ev.get("titleOrig") or "")
    zh = ev.get("titleCn", "")
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'&.\- ]+", q)
    cands = []
    hay = (q + " " + zh).lower()
    for kw, mapped in KNOWN_ENTITY_MAP.items():
        if kw in hay:
            for src_type, page_title, lang in mapped:
                cands.append((src_type, page_title, lang))
            break
    if len(q) >= 2:
        cands.append(("wiki_summary_en", q, "en"))
    if tokens:
        cands.append(("wiki_summary_en", tokens[0], "en"))
    if len(tokens) >= 2:
        cands.append(("wiki_summary_en", " ".join(tokens[:2]), "en"))
    if zh and len(zh) >= 2:
        cands.append(("wiki_summary_zh", zh, "zh"))
    if any(t in ev.get("tags", []) for t in ["动漫", "动画", "番剧"]):
        aq = re.split(r'[:：]', q)[0]
        aq = re.sub(r'\bSeason\s*\d+', '', aq, flags=re.I).strip()
        if aq:
            cands.append(("anilist", aq, ""))
    if ev.get("catCn") in ("明星八卦", "演唱会综艺") and ev.get("country") == "th":
        if q:
            cands.append(("wiki_summary_th", q, "th"))
        if zh:
            cands.append(("wiki_summary_th", zh, "th"))
    return cands


def resolve_one(src_type, query, lang):
    key = (lang, query.lower())
    if key in CACHE_QUERY:
        return CACHE_QUERY[key]
    result = (None, None)
    try:
        if src_type.startswith("wiki_summary"):
            img, real_title = wiki_resolve(query, lang)
            if img:
                result = (img, f"Wikipedia ({lang}) / {real_title}")
        elif src_type == "anilist":
            img = anilist_cover(query)
            if img:
                result = (img, f"AniList / {query}")
    except Exception:
        pass
    CACHE_QUERY[key] = result
    return result


def match_topic(ev):
    blob = " ".join([
        (ev.get("titleOrig") or ""), (ev.get("titleCn") or "")
    ]).lower()
    for topic, aliases in TOPIC_ALIASES:
        for a in aliases:
            if a in blob:
                return topic
    return None


def resolve_topic(topic):
    spec = TOPIC_TABLE.get(topic, {})

    def _try_wiki(title, lang):
        if not title:
            return None, None
        img, rt = wiki_resolve(title, lang)
        if img:
            return img, rt
        # 动态检索纠正拼写/重定向
        found = wiki_search(title, lang)
        if found and found.lower() != title.lower():
            img2, rt2 = wiki_resolve(found, lang)
            if img2:
                return img2, rt2
        return None, None

    # 1) 英文维基
    img, rt = _try_wiki(spec.get("wiki"), "en")
    if img:
        return img, f"Wikipedia (en) / {rt}"
    # 2) 泰文维基
    img, rt = _try_wiki(spec.get("wiki_th"), "th")
    if img:
        return img, f"Wikipedia (th) / {rt}"
    # 3) og:image（官方/文章站）
    if spec.get("og") and spec["og"] not in OG_BLOCK:
        og = og_image(spec["og"])
        if og:
            return og, f"og:image / {urllib.parse.urlparse(spec['og']).netloc}"
    # 4) MyDramaList 演员/剧集页（泰 BL 圈高覆盖）
    if spec.get("mname"):
        m, ms = mydramalist_image(spec["mname"])
        if m:
            return m, ms
    # 5) Wikimedia Commons 实物照（如突突车）
    if spec.get("commons"):
        c, cs = commons_image(spec["commons"])
        if c:
            return c, cs
    return None, None


def search_fallback(ev):
    queries = []
    q = clean_query(ev.get("titleOrig") or "")
    zh = ev.get("titleCn", "")
    if q:
        queries.append(q)
    if zh:
        queries.append(zh)
    th = thai_substring(ev.get("titleOrig") or "")
    if th:
        queries.append(th)
    toks = re.findall(r"[A-Za-z][A-Za-z0-9'&.\- ]+", q)
    if len(toks) >= 2:
        queries.append(" ".join(toks[:3]))
    for lang in ("en", "th"):
        for qy in queries:
            if len(qy) < 3:
                continue
            key = (f"search_{lang}", qy.lower())
            if key in CACHE_QUERY:
                if CACHE_QUERY[key][0]:
                    return CACHE_QUERY[key]
                continue
            CACHE_QUERY[key] = (None, None)
            title = wiki_search(qy, lang)
            if title:
                img, rt = wiki_summary_image(title, lang)
                if not img:
                    img, rt = wiki_pageimage(title, lang)
                if img:
                    res = (img, f"Wikipedia ({lang}) / {rt}")
                    CACHE_QUERY[(lang, title.lower())] = res
                    return res
    return None, None


def og_image(url):
    try:
        host = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        if host in OG_BLOCK:
            return None
    except Exception:
        return None
    try:
        html = http_get_raw(url, timeout=25).decode("utf-8", "ignore")
    except Exception:
        return None
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if not m:
        return None
    cand = m.group(1)
    if cand.startswith("//"):
        cand = "https:" + cand
    elif cand.startswith("/"):
        try:
            base = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}"
            cand = base + cand
        except Exception:
            return None
    if not cand.startswith("http") or cand.lower().endswith(".svg"):
        return None
    return cand


def specific_urls(ev):
    urls = []
    if ev.get("primaryUrl"):
        urls.append(ev["primaryUrl"])
    for src in ev.get("sources", []):
        if src.get("url"):
            urls.append(src["url"])
    seen, out = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def youtube_thumb(urls):
    for u in urls:
        m = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_\-]{6,})', u)
        if m:
            return f"https://img.youtube.com/vi/{m.group(1)}/0.jpg", m.group(1)
    return None, None


def mydramalist_image(name):
    """MyDramaList 演员/剧集页配图（泰 BL 圈高覆盖，含 og:image）。"""
    q = urllib.parse.quote(name)
    search = f"https://mydramalist.com/search?q={q}"
    h = raw_html(search)
    if not h:
        return None, None
    m = re.search(r'href="(/people/\d+[^"]*)"', h)
    if not m:
        m = re.search(r'href="(/drama/\d+[^"]*)"', h)
    if m:
        page = "https://mydramalist.com" + m.group(1)
        ph = raw_html(page)
        if ph:
            om = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                           ph, re.I)
            if om and om.group(1).startswith("http"):
                return om.group(1), f"MyDramaList / {page}"
    sog = og_image(search)
    if sog:
        return sog, "MyDramaList search"
    return None, None


def commons_image(name):
    """Wikimedia Commons 直接搜图（用于无维基主图但有实物照的主题，如突突车）。"""
    api = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": name, "gsrnamespace": 6, "gsrlimit": 8,
        "prop": "imageinfo", "iiprop": "url",
        "iiurlwidth": 600, "format": "json",
    }
    url = api + "?" + urllib.parse.urlencode(params)
    d = http_get_json(url)
    if d:
        for pid, pg in d.get("query", {}).get("pages", {}).items():
            ii = pg.get("imageinfo", [{}])[0]
            u = ii.get("thumburl") or ii.get("url", "")
            if u and not u.lower().endswith((".svg", ".ogg", ".webm")):
                return u, f"Commons / {pg.get('title', '')}"
    return None, None


def raw_html(url, timeout=25):
    try:
        return http_get_raw(url, timeout=timeout).decode("utf-8", "ignore")
    except Exception:
        return ""


def resolve(ev):
    # A. 主题归并（同 IP 跨事件复用）
    topic = match_topic(ev)
    if topic:
        if topic in TOPIC_CACHE:
            return TOPIC_CACHE[topic]
        res = resolve_topic(topic)
        TOPIC_CACHE[topic] = res
        if res[0]:
            return res
    # B. 显式候选
    seen = set()
    for src_type, query, lang in build_candidates(ev):
        if (lang, query.lower()) in seen:
            continue
        seen.add((lang, query.lower()))
        img, src = resolve_one(src_type, query, lang)
        if img:
            return img, src
    # C. Wikipedia opensearch 动态纠正
    img, src = search_fallback(ev)
    if img:
        return img, src
    # D. og:image（具体文章 URL）
    for u in specific_urls(ev):
        og = og_image(u)
        if og:
            return og, f"og:image / {urllib.parse.urlparse(u).netloc}"
    # E. YouTube 缩略图
    yt, vid = youtube_thumb(specific_urls(ev))
    if yt:
        return yt, f"YouTube / {vid}"
    return None, None


def download(url, path, min_bytes=3000):
    try:
        data = http_get_raw(url)
    except Exception:
        return False
    if len(data) < min_bytes:
        return False
    if b"<html" in data[:200] or url.lower().endswith(".svg"):
        return False
    with open(path, "wb") as f:
        f.write(data)
    return True


def get_local(img_url, eid):
    if img_url in CACHE_URL:
        return CACHE_URL[img_url]
    min_b = 6000 if ("wikipedia" not in img_url and "anilist" not in img_url) else 3000
    path = os.path.join(REAL_DIR, eid + ".jpg")
    if download(img_url, path, min_b):
        rel = f"real/{eid}.jpg"
        CACHE_URL[img_url] = rel
        return rel
    return None


def main():
    events = read_events()
    ok = fail = skip = 0
    total = len(events)
    for i, ev in enumerate(events):
        eid = ev.get("id", "")
        if ev.get("coverType") == "real" and ev.get("cover"):
            skip += 1
            continue
        try:
            img, src_desc = resolve(ev)
            local = get_local(img, eid) if img else None
            if local:
                ev["cover"] = local
                ev["coverType"] = "real"
                ev["hasMedia"] = True
                ev["imageSource"] = src_desc
                ok += 1
            else:
                fail += 1
        except Exception:
            fail += 1
        time.sleep(0.12)
        if (i + 1) % 25 == 0:
            print(f"  ...{i+1}/{total} ok={ok} fail={fail} skip={skip}")
    save_events(events)
    print(f"DONE total={total} real_ok={ok} fail={fail} skip={skip}")
    print(f"本轮覆盖率: {int(ok*100/(ok+fail))}%  | 仍缺图: {fail}")


if __name__ == "__main__":
    main()
