# -*- coding: utf-8 -*-
"""全量重建印选 TrendPick v2 站点数据：基底257 + 今日(2026-08-12) fresh 批次。
按印选 TrendPick v2 每日热点站点自动化执行：研究->转v2事件->真实配图->门禁。
"""
import json, os, re, shutil, urllib.request, ssl, urllib.parse, secrets, time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
DATA_JS = os.path.join(HERE, "data.js")
BASE = os.path.join(PROJECT, "_backups", "data.js.bak_20260812_before_daily_merge")
REAL = os.path.join(PROJECT, "site", "img", "real")
os.makedirs(REAL, exist_ok=True)

BATCH = "daily-2026-08-12"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

CAT_MAP = {
    "明星八卦": "celebrity", "演唱会综艺": "concert_show", "影视剧": "film_tv",
    "游戏电竞": "gaming", "网络热梗": "meme", "其他热搜": "other",
    "社会民生": "society", "体育": "sports", "电商政策": "ecommerce", "平台热搜": "platform_search",
}
RISK_MAP = {"明星八卦": "中", "影视剧": "中", "政治人物相关": "高", "社会民生": "低", "网络热梗": "低",
            "电商政策": "低", "平台热搜": "低", "游戏电竞": "低", "演唱会综艺": "中", "其他热搜": "低", "体育": "低"}

def wiki_img(title):
    if not title:
        return None
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            d = json.loads(urllib.request.urlopen(req, timeout=20, context=CTX).read())
            if "originalimage" in d: return d["originalimage"]["source"]
            if "thumbnail" in d: return d["thumbnail"]["source"]
        except Exception:
            time.sleep(1.2)
    return None

def save_jpg(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=30, context=CTX).read()
        if len(data) < 2000: return False
        from io import BytesIO
        from PIL import Image
        try:
            im = Image.open(BytesIO(data)).convert("RGB"); im.save(path, "JPEG", quality=88)
        except Exception:
            return False
        return os.path.getsize(path) >= 2000
    except Exception:
        return False

# 同类目兜底图池（来自基底257已有的真实图）
def build_cat_pool(base):
    pool = defaultdict(list)
    for e in base:
        c = e.get("cover", "")
        if c.startswith("real/"):
            fn = os.path.basename(c)
            p = os.path.join(REAL, fn)
            if os.path.exists(p) and os.path.getsize(p) >= 2000:
                pool[e.get("catCn", "其他热搜")].append(fn)
    return pool

def fresh_id():
    return secrets.token_hex(12)

def make_event(cand, cat_pool):
    eid = fresh_id()
    catCn = cand["catCn"]; country = cand["country"]
    buzz = cand.get("buzzSignal", "稳定热门")
    stars = {"viral": 5, "上升中": 4, "稳定热门": 4, "新发布": 4}.get(buzz, 4)
    buzz_idx = {"viral": 92, "上升中": 80, "稳定热门": 74, "新发布": 82}.get(buzz, 74)
    cred = "高" if any(k in cand.get("sourceUrl", "") for k in ["wikipedia", "official", "majorcineplex", "uniqlo", "roblox", "store.steampowered"]) else "中"
    cred_score = 90 if cred == "高" else 78
    risk = RISK_MAP.get(catCn, "低")
    # 配图
    wiki = cand.get("wikiTitle", "")
    cover = f"real/{eid}.jpg"; dest = os.path.join(REAL, os.path.basename(cover)); img_src = ""
    got = False
    if wiki:
        u = wiki_img(wiki)
        if u and save_jpg(u, dest):
            img_src = f"维基媒体：{wiki}"; got = True
    if not got:
        pool = cat_pool.get(catCn, [])
        if pool:
            src = secrets.choice(pool)
            shutil.copy(os.path.join(REAL, src), dest)
            img_src = "同类目真实图示意"; got = True
    if not got:  # 终极兜底
        any_real = [f for f in os.listdir(REAL) if f.endswith(".jpg") and os.path.getsize(os.path.join(REAL, f)) >= 2000]
        if any_real:
            shutil.copy(os.path.join(REAL, secrets.choice(any_real)), dest)
            img_src = "通用真实图示意"
    src_url = cand.get("sourceUrl", "")
    return {
        "id": eid, "titleCn": cand["titleCn"], "titleOrig": cand.get("titleOrig", ""),
        "catCn": catCn, "cat": CAT_MAP.get(catCn, "other"), "country": country,
        "stars": stars, "cover": cover, "coverType": "real",
        "credibilityScore": cred_score, "buzzIndex": buzz_idx,
        "summary": cand.get("summary", ""),
        "sources": [{"type": "官方" if cred == "高" else "媒体/榜单", "region": "泰国" if country == "th" else "马来西亚",
                     "credibility": cred, "url": src_url}],
        "sourceBreadth": {"local": True, "global": country == "my" or "world" in cand.get("titleCn", ""), "social_only": False},
        "timeline": [{"date": "2026-08-12", "desc": "入选今日(8/12)印选热点日报"}],
        "printType": ("人物印花" if catCn in ("明星八卦", "影视剧", "演唱会综艺") else
                      "文字梗/标语" if catCn in ("网络热梗", "其他热搜") else
                      "主题插画" if catCn in ("社会民生", "游戏电竞") else
                      "信息图/清单" if catCn in ("电商政策", "平台热搜") else "图案印花"),
        "risk": risk, "hotDays": (18 if buzz in ("新发布", "viral") else 45),
        "imageSource": img_src, "hasMedia": True,
        "media": [{"thumb": cover, "caption": cand["titleCn"]}],
        "fresh": True, "batch": BATCH, "primaryUrl": src_url,
    }

# ---- 精选候选（来自联网研究 TH 41 + MY 24，去重映射）----
CANDIDATES = [
 # TH
 {"catCn":"演唱会综艺","country":"th","titleCn":"PerthSanta曼谷演唱会登热搜","titleOrig":"#PerthSantaConcertD2","summary":"泰国顶流CP Perth×Santa曼谷演唱会第二天引爆X热搜，粉丝大量晒图与饭拍，周边应援T恤需求强，是粉丝印花T恤黄金热点。","sourceUrl":"https://xtrends.iamrohit.in/thailand","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"明星八卦","country":"th","titleCn":"FreenBecky CP粉圈刷屏","titleOrig":"#FreenBecky","summary":"泰国国民女女CP FreenBecky长期霸榜X泰国趋势，演唱会周边独家发售T恤受捧，CP名印花、双人合照图是稳定高转化题材。","sourceUrl":"https://www.trends24.in/thailand/","buzzSignal":"稳定热门","wikiTitle":"FreenBecky"},
 {"catCn":"演唱会综艺","country":"th","titleCn":"LingOrm粉丝见面会巡演","titleOrig":"#LingOrmThailandFMTour","summary":"Ling×Orm泰国粉丝见面会巡演登上X趋势，现场应援与同款穿搭带动粉丝印花T恤热销，情侣/闺蜜款设计适配度高。","sourceUrl":"https://xtrends.iamrohit.in/thailand","buzzSignal":"上升中","wikiTitle":""},
 {"catCn":"其他热搜","country":"th","titleCn":"TEN新单登顶泰国榜","titleOrig":"If You Don't Mean It - TEN","summary":"NCT/SM solo歌手TEN新单《If You Don't Mean It》空降Billboard泰国歌曲榜冠军，粉丝应援印花与歌词梗T恤适合速推。","sourceUrl":"https://www.billboard.com/charts/thailand-songs-hotw/","buzzSignal":"新发布","wikiTitle":"TEN (entertainer)"},
 {"catCn":"其他热搜","country":"th","titleCn":"PROXIE《Crybaby》居前三","titleOrig":"Crybaby (Boy's Don't Cry) - PROXIE","summary":"泰国女团PROXIE《Crybaby》稳居Billboard泰国榜前三，团名与歌词男孩不哭成青年情绪梗，贴合Gen-Z印花T恤表达。","sourceUrl":"https://www.billboard.com/charts/thailand-songs-hotw/","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"明星八卦","country":"th","titleCn":"JENNIE新单空降前五","titleOrig":"Less Than A Lover - JENNIE","summary":"BLACKPINK JENNIE新单《Less Than A Lover》空降Billboard泰国榜第5，全球粉群叠加泰国本地热度，黑白极简明星印花T恤适销。","sourceUrl":"https://www.billboard.com/charts/thailand-songs-hotw/","buzzSignal":"新发布","wikiTitle":"Jennie (singer)"},
 {"catCn":"网络热梗","country":"th","titleCn":"泰国哭包挑战爆火","titleOrig":"#ขี้แงChallenge","summary":"X泰国长热榜#ขี้แงChallenge(哭包挑战)走红，配合PROXIE《Crybaby》形成情绪二创，可爱委屈表情包印花T恤易病毒传播。","sourceUrl":"https://getdaytrends.com/thailand/top/longest/day/","buzzSignal":"viral","wikiTitle":""},
 {"catCn":"影视剧","country":"th","titleCn":"《给阿嬷的情书》催泪","titleOrig":"จดหมายรักถึงอาม่า / Letter to Grandma","summary":"华语片《给阿嬷的情书》8/6登陆泰国327家院线，首日票房前3、TikTok二创破1.2亿播放，祖孙温情主题适合亲情T恤。","sourceUrl":"https://www.sohu.com/a/1059613618_122066679","buzzSignal":"viral","wikiTitle":""},
 {"catCn":"其他热搜","country":"th","titleCn":"Vans×Carnival冬阴功Tee","titleOrig":"Vans x Carnival City Tee 'Born to Burn'","summary":"Vans联手泰国潮牌Carnival推以冬阴功为灵感的City Tee“Born to Burn”，将国民美食图形化，是本土文化街头印花T恤范例。","sourceUrl":"https://www.thaioutdoorgroup.com/vans-and-carnival-officially-launch-the-city-tee-born-to-burn-at-exclusive-media-event","buzzSignal":"稳定热门","wikiTitle":"Vans"},
 {"catCn":"网络热梗","country":"th","titleCn":"Pip式舞蹈挑战走红","titleOrig":"#เต้นแบบปิ๊ป","summary":"X泰国长热榜#เต้นแบบปิ๊ป(Pip式舞蹈)带动短视频模仿，魔性舞步配卡通人物或文字梗，适合做趣味动态印花T恤。","sourceUrl":"https://getdaytrends.com/thailand/top/longest/day/","buzzSignal":"viral","wikiTitle":""},
 {"catCn":"社会民生","country":"th","titleCn":"母亲节茉莉浅蓝T恤","titleOrig":"Mother's Day Jasmine & Light Blue","summary":"8/12泰国母亲节举国庆祝，茉莉花环与周五浅蓝为标志色，母亲节主题T恤(浅蓝+茉莉+泰文แม่)是应季高需单品。","sourceUrl":"https://www.rawai.com/phuket-marks-national-mothers-day-with-public-holiday-and-library-activities","buzzSignal":"稳定热门","wikiTitle":"Mother's Day (Thailand)"},
 {"catCn":"社会民生","country":"th","titleCn":"水灯节11/25临近备货","titleOrig":"Loy Krathong 2026 (25 Nov)","summary":"泰国水灯节2026年11月25日，全国放水灯祈福，香蕉叶灯船、莲花与烛光图形可提前规划秋冬T恤，错峰上新颖抢先机。","sourceUrl":"https://www.highlightstravel.com/thailand/loy-krathong-festival","buzzSignal":"上升中","wikiTitle":"Loy Krathong"},
 {"catCn":"平台热搜","country":"th","titleCn":"Shopee泰女装凉鞋T恤热搜","titleOrig":"รองเท้าแตะผู้หญิง / เสื้อ","summary":"Shopee泰国周报热搜词领跑为女式凉鞋、衬衫、捏捏乐、女士时尚衬衫、肩包等，服饰类目T恤长居热搜，选品参考强。","sourceUrl":"https://www.dny123.com/tag-Shopee-3.htm","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"平台热搜","country":"th","titleCn":"Lazada泰母亲季+雨季选品","titleOrig":"Lazada TH Mother's Day & Rainy Season","summary":"Lazada泰国Q3围绕母亲节季末促销与家电节点布局，雨季防水降温品类上升，平台趋势报告指疗愈消费与正品需求暴涨210%。","sourceUrl":"http://chwang.com/baike/lazada","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"平台热搜","country":"th","titleCn":"TikTok泰印花T恤热卖","titleOrig":"TikTok Shop TH Graphic Tee / Elephant Pants","summary":"TikTok泰国服饰以高弹印花T恤、泰式象裤为主力，直播演示舒适度转化高，图案T恤适合短视频带货。","sourceUrl":"https://www.accio.com/business/thailand-garment","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"电商政策","country":"th","titleCn":"TikTok Shop泰强推TISI与AHR","titleOrig":"TikTok Shop Thailand TISI & AHR Policy","summary":"TikTok Shop泰国7月起严查12小时回复率(<85%扣分)、6/30起强制TISI认证，并启用0-1000 AHR健康分，合规卖家务须留意。","sourceUrl":"https://www.tukemarketing.com/news/3835-tiktok-shop-thailand-adjusts-rules-again-starting-july-6-reply-rates-below-85-will-result-in-point-deductions","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"电商政策","country":"th","titleCn":"Lazada泰8/1佣金涨4.5%","titleOrig":"Lazada Thailand Cross-border Commission +4.5%","summary":"Lazada泰国站自2026/8/1起跨境基础佣金统一上调4.5%(Premium Package仅+1%)，卖家需重算T恤定价与毛利，影响选品策略。","sourceUrl":"https://www.ouzhou123.com/news/7751","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"影视剧","country":"th","titleCn":"IDOLiSH7影院直播热映","titleOrig":"IDOLiSH7 VISIBLIVE TOUR 4WARD JOURNEY","summary":"偶像动画《IDOLiSH7》影院直播巡演8/22登陆泰国Major Cineplex(220分钟)，二次元男团粉丝周边与角色印花T恤需求旺盛。","sourceUrl":"https://www.majorcineplex.com/","buzzSignal":"新发布","wikiTitle":"Idolish7"},
 {"catCn":"影视剧","country":"th","titleCn":"《影之恶魔》登网飞泰前十","titleOrig":"Daemons of the Shadow Realm","summary":"奇幻动画《Daemons of the Shadow Realm》稳居Netflix泰国剧集榜前十，暗黑奇幻美术风适配哥特/神秘感印花T恤设计。","sourceUrl":"https://www.netflix.com/tudum/top10/thailand/tv","buzzSignal":"稳定热门","wikiTitle":"Daemons of the Shadow Realm"},
 {"catCn":"其他热搜","country":"th","titleCn":"吉伊卡哇电影联名UT热卖","titleOrig":"CHIIKAWA UT (UNIQLO)","summary":"为纪念《剧场版CHIIKAWA 人鱼岛的秘密》，UNIQLO推CHIIKAWA联名UT(7/27发售)，治愈萌系角色印花T恤在亚洲持续热销。","sourceUrl":"https://faq-hk.uniqlo.com/pkb_Home_UQ_HK?id=kA0fQ000000AAm5","buzzSignal":"稳定热门","wikiTitle":"Chiikawa"},
 {"catCn":"影视剧","country":"th","titleCn":"KATSEYE纪录片今日上映","titleOrig":"KATSEYE WILD HEARTS","summary":"全球化女团KATSEYE纪录电影《WILD HEARTS》8/12在泰国Major Cineplex上映，多元少女团体话题度高，应援色与团徽T恤有空间。","sourceUrl":"https://www.majorcineplex.com/","buzzSignal":"新发布","wikiTitle":"Katseye"},
 {"catCn":"游戏电竞","country":"th","titleCn":"原神7.0至冬国今日上线","titleOrig":"Genshin Impact 7.0 'Everwinter without Mercy'","summary":"《原神》7.0至冬国8/12上线，新增五星Odette和四星Alyosha及新反应机制，开放世界雪国美术带动角色立绘印花T恤。","sourceUrl":"https://www.pockettactics.com/genshin-impact/update","buzzSignal":"新发布","wikiTitle":"Genshin Impact"},
 {"catCn":"游戏电竞","country":"th","titleCn":"ROBLOX 2026引擎大更新","titleOrig":"Roblox Update 2026","summary":"ROBLOX 2026上线AI创作工具、XR混合现实与云渲染，创作者分成升至70%，平台头像/游戏梗适合做像素风趣味印花T恤。","sourceUrl":"https://devforum.roblox.com/t/weekly-recap-june-22-26-2026/4704424","buzzSignal":"稳定热门","wikiTitle":"Roblox"},
 {"catCn":"影视剧","country":"th","titleCn":"电竞BL《玩家二号》热播","titleOrig":"Be My Player Two","summary":"WeTV泰腐《Be My Player Two》讲电竞选手恋曲，8/6播EP4、8/13播EP5，游戏+BL双流量，键盘手柄与CP名印花T恤适配。","sourceUrl":"https://usa.soapcentral.com/shows/ready-next-round-be-my-player-two-release-schedule-revealed","buzzSignal":"上升中","wikiTitle":""},
 {"catCn":"明星八卦","country":"th","titleCn":"Lisa世界杯曲+十周年回归","titleOrig":"LISA - 'Goals' & BLACKPINK 10th","summary":"Lisa凭FIFA世界杯曲《Goals》成首位登世界杯开幕式的泰籍艺人，8/8又逢BLACKPINK出道十周年，国民热度与周边T恤双高。","sourceUrl":"https://en.thairath.co.th/sport/worldcup/2934092","buzzSignal":"稳定热门","wikiTitle":"Lisa (rapper)"},
 {"catCn":"其他热搜","country":"th","titleCn":"优衣库马里奥赛车UT8月","titleOrig":"UNIQLO UT x Mario Kart World","summary":"UNIQLO UT携手任天堂《Mario Kart World》推联名Tee与卫衣，8月中男装童装Tee发售，经典赛车角色印花全民向热卖。","sourceUrl":"https://hypebeast.com/zh/2026/6/uniqlo-ut-mario-kart-world-collection-release-info","buzzSignal":"新发布","wikiTitle":"Mario Kart"},
 {"catCn":"其他热搜","country":"th","titleCn":"优衣库YOASOBI联名UT热卖","titleOrig":"UNIQLO UT x YOASOBI","summary":"UNIQLO时隔五年再推YOASOBI联名UT(7/17上市)，四位艺术家诠释音乐世界，宽松版型四款图案，音乐粉与潮流客通吃。","sourceUrl":"https://news.taiwannet.com.tw/news/210399/uniqlo-%E7%9D%BD%E9%81%94%E4%BA%94%E5%B9%B4%E5%86%8D%E5%BA%A6%E6%94%9C%E6%89%8B-yoasobi-%E6%8E%A8%E5%87%BA%E5%85%A8%E6%96%B0-ut-%E7%B3%BB%E5%88%97.html","buzzSignal":"稳定热门","wikiTitle":"Yoasobi"},
 # MY
 {"catCn":"明星八卦","country":"my","titleCn":"马区X热搜泰腐CP霸榜","titleOrig":"#LingOrmAtDior #MizuMixPhuwin #WEIRDO101","summary":"马来西亚X/推特实时热搜被多对泰腐CP(LingOrm、PhuwinMix、WilliamEst)及《WEIRDO101》刷屏，粉丝饭圈流量极高，适合CP同人印花T恤。","sourceUrl":"https://www.trends24.in/malaysia/ipoh/","buzzSignal":"稳定热门","wikiTitle":"LingOrm"},
 {"catCn":"明星八卦","country":"my","titleCn":"西蒂30周年传奇演唱会","titleOrig":"Konsert Legacy 30 Siti Nurhaliza","summary":"马来歌后Siti Nurhaliza今年1月武吉加里尔6.5万人Legacy 30演唱会大获成功，新专辑《Gema Bumantara》融合传统歌谣，国民级IP适合歌词语录印花。","sourceUrl":"https://www.kitepunye.com/konsert-legacy-30-siti-nurhaliza-bakal-janji-persembahan-wow/","buzzSignal":"稳定热门","wikiTitle":"Siti_Nurhaliza"},
 {"catCn":"影视剧","country":"my","titleCn":"苏利亚《Vishwanath》8月上映","titleOrig":"Vishwanath and Sons (Tamil, Suriya)","summary":"印度泰米尔大片《Vishwanath and Sons》由Suriya主演，定档8月14日马来西亚同步上映，被视为8月最大Kollywood票房之作。","sourceUrl":"https://cinematimes.in/upcoming-kollywood-movies-releasing-in-august-2026","buzzSignal":"新发布","wikiTitle":"Suriya"},
 {"catCn":"影视剧","country":"my","titleCn":"《Jana Nayagan》泰米尔爆款","titleOrig":"Jana Nayagan","summary":"泰米尔语电影《Jana Nayagan》7月23日大马上映，预售即破RM300万，连续登顶本地票房，南马Tamil观众观影热情高涨。","sourceUrl":"https://enewspapermy.com/entertainment/how-asian-films-are-stealing-the-spotlight-from-hollywood-at-malaysias-2026-box-office-enews-malaysia","buzzSignal":"上升中","wikiTitle":"Kollywood"},
 {"catCn":"影视剧","country":"my","titleCn":"《Tarung》本土票房冠军","titleOrig":"Tarung: Unforgiven","summary":"马来本土动作片《Tarung: Unforgiven》以RM2330万成为2026年大马最卖座国产片，连庄三周票房冠军，本土英雄题材适合武打印花。","sourceUrl":"https://enewspapermy.com/entertainment/how-asian-films-are-stealing-the-spotlight-from-hollywood-at-malaysias-2026-box-office-enews-malaysia","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"社会民生","country":"my","titleCn":"国庆日Jalur Gemilang","titleOrig":"Merdeka 2026: Malaysia MADANI","summary":"2026国庆与马来西亚日主题为Malaysia MADANI: Kesejahteraan Dinikmati，8/31国庆临近，官方力推一户一面国旗，爱国印花T恤进入销售旺季。","sourceUrl":"https://www.bernama.com/en/general/news.php?id=2582856","buzzSignal":"上升中","wikiTitle":"Flag_of_Malaysia"},
 {"catCn":"其他热搜","country":"my","titleCn":"蜡染街头风回潮","titleOrig":"Batik Streetwear / KLFW 2026","summary":"KLFW 2026以回归本源为主题，BATIK蜡染工艺融入日常街头服饰成核心趋势，Gen Z追捧传统×现代拼贴，极适合蜡染图腾印花T恤。","sourceUrl":"https://www.tatlerasia.com/style/fashion/six-fashion-trends-klfw-2026-zh-hans","buzzSignal":"上升中","wikiTitle":"Batik"},
 {"catCn":"其他热搜","country":"my","titleCn":"现代Kebaya回潮","titleOrig":"Modern Kebaya with indie twist","summary":"2026年马来传统Kebaya以现代独立风回潮，Gen Z偏好轻盈飘逸pastel色调日常款，传统娘惹服饰文化复兴带动民族风印花需求。","sourceUrl":"https://arah.my/category/tmr/life-arts","buzzSignal":"上升中","wikiTitle":"Kebaya"},
 {"catCn":"游戏电竞","country":"my","titleCn":"MPL大马S18开赛","titleOrig":"MPL Malaysia Season 18 (Mobile Legends)","summary":"手游电竞联赛MPL Malaysia S18于8月14日开赛，八队竞逐CelcomDigi梦舞台，MLBB迎来10周年，大马电竞粉丝基数庞大。","sourceUrl":"https://en.moonton.com/news/363.html","buzzSignal":"新发布","wikiTitle":"Mobile_Legends:_Bang_Bang"},
 {"catCn":"影视剧","country":"my","titleCn":"Netflix马区韩剧霸榜","titleOrig":"Our Sticky Love / Bulan Henti Bicara","summary":"Netflix马来西亚Top10中韩剧《Our Sticky Love》与本土剧《Bulan Henti Bicara》稳居前列，8月新片《Mikael》上线，影视台词印花有受众。","sourceUrl":"https://www.netflix.com/tudum/top10/malaysia/tv/2021-11-14","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"影视剧","country":"my","titleCn":"Viu《Aku Pilih Pelangi》","titleOrig":"Aku Pilih Pelangi (Viu Original, Mira Filzah)","summary":"Viu马来西亚2026原创剧《Aku Pilih Pelangi》由顶流Mira Filzah主演引爆讨论，平台八部原创转向复仇惊悚，本地明星剧照印花受年轻女性欢迎。","sourceUrl":"https://themalaytribune.com/viu-malaysia-goes-darker-in-2026-with-eight-originals-revenge-dramas-and-a-psychological-thriller-slate","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"影视剧","country":"my","titleCn":"海贼王Elbaph篇热播","titleOrig":"ONE PIECE – Elbaph Arc (Crunchyroll Summer 2026)","summary":"Crunchyroll东南亚暑期档新增《ONE PIECE Elbaph篇》，海贼王长期霸榜马来动漫搜索，路飞等角色是T恤印花常青题材。","sourceUrl":"https://techsabado.com/2026/07/09/anime-crunchyroll-expands-summer-2026-anime-lineup/","buzzSignal":"稳定热门","wikiTitle":"One_Piece"},
 {"catCn":"明星八卦","country":"my","titleCn":"Stray Kids RUN IT巡演","titleOrig":"Stray Kids World Tour RUN IT","summary":"Stray Kids于2026/7/25启动RUN IT世界巡演覆盖亚洲多城，东南亚粉圈狂热，虽未定大马场但周边需求外溢，成员头像印花走俏。","sourceUrl":"https://wiki.kfd.me/wiki/Stray_Kids_World_Tour_%22RUN_IT%22","buzzSignal":"上升中","wikiTitle":"Stray_Kids"},
 {"catCn":"明星八卦","country":"my","titleCn":"Neelofa清真时尚霸榜","titleOrig":"Neelofa / Naelofar modest fashion","summary":"马来西亚顶流网红Neelofa(840万粉)及Naelofar清真时尚品牌持续霸榜社媒，本土名人+清真审美组合是马来T恤联名高信任度IP。","sourceUrl":"https://influencers.feedspot.com/malaysian_instagram_influencers","buzzSignal":"稳定热门","wikiTitle":"Neelofa"},
 {"catCn":"电商政策","country":"my","titleCn":"TikTok Shop本土化收紧","titleOrig":"TikTok Shop Malaysia 本地化与SSM审核","summary":"TikTok Shop马来西亚2026年正式本地化：马来语界面、Touch'n Go本地支付、Q2起新店前3月免佣金，但SSM资质与本地仓审核明显收紧。","sourceUrl":"https://www.xusuna.com/article/311439","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"电商政策","country":"my","titleCn":"Lazada 8.8/9.9大促","titleOrig":"Lazada MY Q3 Sale Calendar 8.8 & 9.9","summary":"Lazada马来西亚公布2026 Q3大促日历，8.8结合国庆(Merdeka)主推时尚美妆、9.9为全年第二大促，建议卖家提前备货提报。","sourceUrl":"https://www.tkmmm.com/archives/6751","buzzSignal":"上升中","wikiTitle":""},
 {"catCn":"平台热搜","country":"my","titleCn":"Shopee国旗T恤热搜","titleOrig":"Jalur Gemilang / Merdeka T-shirt","summary":"Shopee马来西亚站内Jalur Gemilang、Merdeka T-shirt搜索飙升，国旗、双子塔、木槿花印花T恤RM17–70价位段热卖，国庆季刚需。","sourceUrl":"https://compare.iprice.my/s/jalur%20gemilang%20shirt","buzzSignal":"上升中","wikiTitle":"Flag_of_Malaysia"},
 {"catCn":"平台热搜","country":"my","titleCn":"Lazada T恤品类热词","titleOrig":"T-Shirts & Tanks / Batik / Muslim Dress","summary":"Lazada马来西亚首页热推T-Shirts & Tanks、Batik、Muslim Dress等服饰词，蜡染与穆斯林长裙印花款及手持小风扇为夏季高频搜索。","sourceUrl":"https://www.lazada.com.my/","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"平台热搜","country":"my","titleCn":"TikTok蜡染街头热","titleOrig":"Batik streetwear & Square Hijab (TikTok MY)","summary":"TikTok Shop马来西亚数据中Batik街头服饰与方巾头巾进入趋势Top10，穆斯林时尚内容互动密度高，短视频种草转化强。","sourceUrl":"https://smmnut.com/blog/trending-tiktok-products-april-2026","buzzSignal":"上升中","wikiTitle":"Batik"},
 {"catCn":"体育","country":"my","titleCn":"2026世界杯西班牙夺冠","titleOrig":"2026 FIFA World Cup (Spain champions)","summary":"2026美加墨世界杯7月落幕，西班牙时隔16年夺冠，足球周边与国旗印花在全球及大马仍具余温。","sourceUrl":"https://new.qq.com/rain/a/20260808A02TYE00","buzzSignal":"稳定热门","wikiTitle":"2026_FIFA_World_Cup"},
 {"catCn":"网络热梗","country":"my","titleCn":"马哈蒂尔死讯谣言","titleOrig":"#RIP Mahathir Mohamad hoax","summary":"2026年7月网传前首相马哈蒂尔死讯假消息在FB/X病毒式扩散后被证伪，反映大马社媒谣言生态，可作讽刺/梗图印花素材。","sourceUrl":"https://cn.mediamass.net/yule/mahathir-mohamad/siwang-yaoyan.html","buzzSignal":"稳定热门","wikiTitle":"Mahathir_Mohamad"},
 {"catCn":"其他热搜","country":"my","titleCn":"本土街头品牌HYPE联名","titleOrig":"HYPE Streetwear x Malaysian identity","summary":"大马本土街头品牌HYPE以文化×态度定位年轻人，RIUH生活市集推动本土品牌联名，国族标识+街头graphic是印花T恤潮流方向。","sourceUrl":"https://partners.segi.edu.my/everse/souvenirs","buzzSignal":"稳定热门","wikiTitle":""},
 {"catCn":"明星八卦","country":"my","titleCn":"BLACKPINK巡演跳过大马","titleOrig":"BLACKPINK DEADLINE World Tour skips Malaysia","summary":"BLACKPINK DEADLINE世界巡演公布城市未含马来西亚，大马Blinks在社媒集体请愿，话题持续发酵，可借想念BLACKPINK情绪做粉丝印花。","sourceUrl":"https://www.sarawaktribune.com/?p=478454","buzzSignal":"稳定热门","wikiTitle":"Blackpink"},
 {"catCn":"影视剧","country":"my","titleCn":"好莱坞《奥德赛》在映","titleOrig":"The Odyssey / Insidious: Out of the Further","summary":"8月大马院线好莱坞大片《The Odyssey》仍在映，恐怖续作《Insidious: Out of the Further》8/21上映，IP粉丝向印花可作小众爆款。","sourceUrl":"https://www.mensxp.com/entertainment/bollywood/185013-august-2026-theatrical-releases-16-movies-awarapan-2-batwara-1947-toxic.html","buzzSignal":"新发布","wikiTitle":"The_Odyssey_2026_film"},
]

def main():
    raw = open(BASE, encoding="utf-8").read()
    base, _ = json.JSONDecoder().raw_decode(raw, raw.index("["))
    cat_pool = build_cat_pool(base)
    existing = {e.get("titleCn") for e in base}
    added, skipped = [], 0
    for c in CANDIDATES:
        if c["titleCn"] in existing:
            skipped += 1; continue
        existing.add(c["titleCn"])
        added.append(make_event(c, cat_pool))
    out = base + added
    # 统一 cat 英文枚举（规范对齐）
    for e in out:
        if e.get("catCn") in CAT_MAP:
            e["cat"] = CAT_MAP[e["catCn"]]
    # 写盘 + 磁盘复核
    txt = "window.EVENTS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n"
    open(DATA_JS, "w", encoding="utf-8").write(txt)
    # 复核
    reread = open(DATA_JS, encoding="utf-8").read()
    chk, _ = json.JSONDecoder().raw_decode(reread, reread.index("["))
    assert len(chk) == len(out), f"disk mismatch {len(chk)} != {len(out)}"
    # 门禁
    b64 = sum(1 for e in chk if str(e.get("cover", "")).startswith("data:image"))
    broken = 0
    for e in chk:
        cc = e.get("cover", "")
        if cc.startswith("real/"):
            p = os.path.join(REAL, os.path.basename(cc))
            if not os.path.exists(p) or os.path.getsize(p) < 2000:
                broken += 1
    fresh = sum(1 for e in chk if e.get("fresh"))
    print(f"BASE={len(base)} + ADDED={len(added)} (skipped dup={skipped}) = TOTAL={len(chk)}")
    print(f"GATE: base64={b64} | broken/missing={broken} | fresh={fresh}")
    # 配图来源统计
    real_wiki = sum(1 for e in added if "维基" in (e.get("imageSource") or ""))
    print(f"added imageSource: wiki={real_wiki} | fallback={len(added)-real_wiki}")

if __name__ == "__main__":
    main()
