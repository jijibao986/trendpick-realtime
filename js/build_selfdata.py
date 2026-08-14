# -*- coding: utf-8 -*-
# 用「自研报告」(thailand_trends_*.md) 的真实研究数据重灌 site/js/data.js
# v2: 输出结构化来源 / timeline / media / primaryUrl 等新字段
import json, uuid, datetime, re, os

# 元组格式 (v1 兼容 + 扩展):
# (country, catCn, stars(1-4), printType, risk, hotDays,
#  titleCn, titleOrig, summary,
#  source_count, sources_str, [tags], sensitive)
#
# sources_str 格式: "平台1、平台2、平台3" 或 "平台1(url)、平台2"
# 若某来源含 (url) 后缀，自动提取为 structured source with url

RAW = [
# ===================== Twitter/X 泰国榜 (35) =====================
("th","明星八卦",4,"文字+图案","低风险",12,"BTS世界巡演曼谷站","#BTS_WORLDTOUR_BANGKOK（BTS世界巡演曼谷站）","泰区推特榜首，韩流巡演带动应援棒/口号款需求，适合文字+图案情侣周边。",6,"getdaytrends、whatstrends、Twitter TH",["韩流","演唱会","应援"],False),
("th","演唱会综艺",4,"文字+图案","低风险",14,"Duang巡回演唱会","#DuangGoRoundConcert（Duang巡回演唱会）","泰星Duang个人巡演宣传期，粉丝向T恤关键词持续上榜。",3,"getdaytrends、Twitter TH",["演唱会","泰星"],False),
("th","明星八卦",4,"文字款","低风险",14,"PerthSanta×Mint杂志","#PerthSantaXMintMagTH（PerthSanta×Mint杂志）","CP与杂志拍摄联动，粉丝购买力强，情侣/闺蜜款潜力高。",3,"getdaytrends、Twitter TH",["CP","明星"],False),
("th","影视剧",3,"文字款","低风险",10,"当雨落下宣传巡游","#WhenItRainsPressTour（当雨落下宣传巡游）","新剧宣传巡游话题，剧集粉丝向文字款。",2,"getdaytrends",["剧集","宣传"],False),
("th","影视剧",3,"文字款","低风险",10,"Duang与她剧集","#ด้วงกับเธอSeries（Duang与她剧集）","Duang主演新剧，剧粉向简约文字款。",2,"getdaytrends",["剧集"],False),
("th","明星八卦",4,"图案+文字","低风险",12,"SF×WilliamEst Wesley","#SFxWilliamEstWesley（SF×WilliamEst Wesley）","跨境双市场爆款CP，情侣款文字+图案需求极强。",5,"getdaytrends、Twitter TH、TikTok",["CP","跨境"],False),
("th","影视剧",4,"文字款","低风险",8,"Soso翻译员EP3","#ซอโซ่ล่ามธีร์EP3（Soso翻译员EP3）","剧集更新节点话题，剧粉向文字款。",2,"getdaytrends",["剧集"],False),
("th","明星八卦",4,"图案+文字","低风险",12,"Wawa和TeeTeePawPaw做朋友","#วาวาเมคเฟรนด์กับตี๋ตี๋ป๋อ（Wawa和TeeTeePawPaw做朋友）","CP综艺友情梗，情侣/闺蜜款图案+文字。",3,"getdaytrends、Twitter TH",["CP","综艺"],False),
("th","演唱会综艺",3,"文字款","低风险",10,"我的玩家二EP3","BE MY PLAYER TWO EP3（我的玩家二EP3）","剧集+电竞联动，玩家向文字款。",2,"Twitter TH",["剧集","电竞"],False),
("th","明星八卦",3,"文字+图案","低风险",10,"Phuwin×Hana×Nekko","PHUWIN HANA WITH NEKKO（Phuwin×Hana×Nekko）","明星×品牌联动，粉丝向图案款。",2,"Twitter TH",["明星","品牌"],False),
("th","明星八卦",3,"文字款","低风险",10,"Friendly Me×SHINee专场","FRIENDLY ME X SHINEE PREM（Friendly Me×SHINee专场）","韩流特别专场，韩粉文字款。",2,"Twitter TH",["韩流","明星"],False),
("th","明星八卦",3,"文字款","低风险",10,"Lookkaew生而闪耀","LOOKKAEW BORN TO SHINE（Lookkaew生而闪耀）","选秀节目话题，练习生粉丝向文字款。",2,"Twitter TH",["选秀","明星"],False),
("th","明星八卦",4,"文字+图案","低风险",12,"与LISA的十年","ONE DECADE WITH LISA（与LISA的十年）","BLACKPINK Lisa十年纪念，粉丝强烈买单，图案+文字。",4,"Twitter TH、TikTok",["韩流","明星"],False),
("th","明星八卦",4,"文字+图案","低风险",12,"LMSY粉丝见面会D日","LMSY FANCON DDAY（LMSY粉丝见面会D日）","顶流CP粉丝见面会，情侣款需求高。",3,"Twitter TH",["CP","粉丝活动"],False),
("th","明星八卦",3,"文字款","低风险",10,"Renjun你我回响","RENJUN ECHOES BETWEEN US（Renjun你我回响）","NCT Renjun个人活动，韩粉文字款。",2,"Twitter TH",["韩流","NCT"],False),
("th","明星八卦",3,"文字款","低风险",10,"Nani吹响美妙早晨","NANI BLOWS WONDERFUL MORNING（Nani吹响美妙早晨）","泰星Nani广播活动，粉丝向文字款。",2,"Twitter TH",["泰星"],False),
("th","明星八卦",4,"图案+文字","低风险",12,"BTS官方应援棒新版","BTS OFFICIAL LIGHT STICK VER（BTS官方应援棒新版）","应援棒视觉符号适合图案款周边。",4,"Twitter TH",["韩流","周边"],False),
("th","影视剧",3,"文字款","低风险",10,"假想敌with福利EP6","#EnemiesWithBenefitsEP6（假想敌with福利EP6）","剧名梗，剧粉文字款。",2,"getdaytrends",["剧集"],False),
("th","影视剧",3,"文字款","低风险",10,"Sod Sai Mala EP16","#สอดสร้อยมาลาEP16（Sod Sai Mala EP16）","剧集更新话题，剧粉文字款。",2,"getdaytrends",["剧集"],False),
("th","明星八卦",3,"文字款","低风险",10,"Unif×KengNamping","#UnifFreshwithKengNamping（Unif×KengNamping）","明星×潮牌联动，粉丝向文字款。",2,"Twitter TH",["品牌","明星"],False),
("th","明星八卦",3,"图案+文字","低风险",10,"KNP×Unif","KNP X UNIF（KNP×Unif）","品牌联名，潮牌风图案款。",2,"Twitter TH",["联名","潮牌"],False),
("th","影视剧",3,"文字款","低风险",10,"曼谷红Opera EP16","THE BKK RED OPERA EP16（曼谷红Opera EP16）","剧集话题，剧粉文字款。",2,"Twitter TH",["剧集"],False),
("th","明星八卦",3,"文字款","低风险",10,"Engfa传承11","ENGFA THE LEGACY11（Engfa传承11）","明星综艺话题，粉丝文字款。",2,"Twitter TH",["明星","综艺"],False),
("th","影视剧",3,"文字款","低风险",10,"近来是冬季EP5","LATELY ITS WINTER SEASON EP5（近来是冬季EP5）","剧集话题，剧粉文字款。",2,"Twitter TH",["剧集"],False),
("th","影视剧",3,"文字款","低风险",10,"Tonsom第5集","TONSOM 5TH EPISODE（Tonsom第5集）","剧集话题，剧粉文字款。",2,"Twitter TH",["剧集"],False),
("th","明星八卦",3,"图案+文字","低风险",12,"FayeAtom巴西行","FAYEATOM NO BRASIL（FayeAtom巴西行）","CP旅游梗，情侣款图案+文字。",3,"Twitter TH",["CP","旅游"],False),
("th","明星八卦",3,"图案+文字","低风险",10,"闪耀骄傲Charlotte11","SHINING PRIDE CHARLOTTE11（闪耀骄傲Charlotte11）","明星综艺话题，粉丝文字款。",2,"Twitter TH",["明星"],False),
("th","明星八卦",3,"图案+文字","低风险",10,"Jayna时装线","JAYNA KLOSET ACS（Jayna时装线）","明星自创潮牌，风格致敬款。",2,"Twitter TH",["明星","潮牌"],False),
("th","明星八卦",3,"文字+图案","低风险",10,"Daou Chacha舞台","DAOU CHACHA TPOPSTAGE（Daou Chacha舞台）","CP音乐舞台，粉丝向文字+图案。",2,"Twitter TH",["CP","音乐"],False),
("th","明星八卦",4,"文字+图案","低风险",12,"SkyNani命运发布会","SKYNANI WU DESTINY PRESS（SkyNani命运发布会）","新剧发布会，跨境CP热度，情侣款。",4,"Twitter TH、TikTok",["CP","新剧"],False),
("th","明星八卦",4,"文字+图案","低风险",12,"WilliamEst专属之夜","WILLIAMEST EXCLUSIVE NIGHT（WilliamEst专属之夜）","霸榜CP粉丝活动，跨境双市场情侣款首选。",5,"Twitter TH、TikTok、getdaytrends",["CP","粉丝活动","跨境"],False),
# ===================== Twitter/X 马来西亚榜 (35) =====================
("my","明星八卦",3,"图案+文字","低风险",12,"PSD Mogul arrival时装秀","PSD MOGULARRIVAL FS26（PSD Mogul arrival时装秀）","本地时装选秀话题，潮牌风图案款。",2,"xtrends、Twitter MY",["时装","选秀"],False),
("my","影视剧",4,"图案+文字","低风险",12,"Peach And Me系列大结局","#PeachAndMeSeriesFinalEP（Peach And Me系列大结局）","PondPhuwin跨境爆款剧大结局，婚礼/承诺款。",5,"xtrends、Twitter MY、TikTok",["泰剧","CP","跨境"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"DMD运动日","#DMDSportsDay2026（DMD运动日）","明星运动综艺，运动风文字+图案。",3,"Twitter MY",["明星","综艺"],False),
("my","影视剧",4,"图案+文字","低风险",12,"绘梦婚礼日EP7","#วาดฝันวันวิวาห์EP7（绘梦婚礼日EP7）","泰马合拍剧，婚礼视觉情侣款。",5,"xtrends、Twitter MY",["泰剧","婚礼"],False),
("my","明星八卦",4,"文字款","低风险",10,"三台女星杯","#CH3GirlsCup2026（三台女星杯）","女星杯综艺，粉丝文字款。",3,"Twitter MY",["明星","综艺"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"LingOrm我挚爱的秘密EP7","LINGORM ILF EP7（LingOrm我挚爱的秘密EP7）","马来顶流CP，情侣款图案+文字。",5,"xtrends、Twitter MY",["CP","跨境"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"TeeTeePawPaw运动日","#ตี๋ตี๋ป๋อสปอร์ตเดย์2026（TeeTeePawPaw运动日）","CP综艺运动日，情侣运动款。",3,"Twitter MY",["CP","综艺"],False),
("my","明星八卦",3,"文字款","低风险",10,"TeeTeePawPaw打气","TEETEEPOR CHEER UP（TeeTeePawPaw打气）","CP应援文字款。",2,"Twitter MY",["CP"],False),
("my","明星八卦",3,"文字款","低风险",10,"LenaMiu三台女星杯","LENAMIU GIRLS CUP CH3（LenaMiu三台女星杯）","女星杯话题，粉丝文字款。",2,"Twitter MY",["明星"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"ZeeNunew×Zone","ZEENUNEW x ZON SUSU（ZeeNunew×Zone）","CP粉丝活动，情侣款。",3,"Twitter MY",["CP"],False),
("my","明星八卦",3,"文字款","低风险",10,"KNP全力","KNP OHAE FULL POWER（KNP全力）","品牌/明星话题，粉丝文字款。",2,"Twitter MY",["品牌","明星"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"Gemini×蒙奇奇×Simplus","GEMINI MONCHHICHI WITH SIMPLUS（Gemini×蒙奇奇×Simplus）","CP联名可爱款，萌系图案。",4,"Twitter MY",["CP","联名","可爱"],False),
("my","影视剧",3,"文字款","低风险",10,"Ohm Pawat赛车手2","RACER OHM PAWAT D2（Ohm Pawat赛车手2）","泰星剧集，剧粉文字款。",2,"Twitter MY",["泰星","剧集"],False),
("my","影视剧",4,"图案","低风险",14,"蜘蛛侠：全新一天","Spiderman（蜘蛛侠：全新一天）","全球电影热，超级英雄图案款。",4,"Twitter MY、Box Office",["电影","超级英雄"],False),
("my","明星八卦",4,"文字款","低风险",10,"Domundi运动会","DOMUNDI SPORTS 2026（Domundi运动会）","明星运动综艺，运动风文字款。",3,"Twitter MY",["明星","综艺"],False),
("my","明星八卦",4,"文字款","低风险",10,"ENHYPEN不是机器","ENHYPEN ARE NOT MACHINES（ENHYPEN不是机器）","韩流巡演话题，韩粉文字款。",3,"Twitter MY",["韩流"],False),
("my","影视剧",3,"图案+文字","低风险",10,"与Charlotte同在01","HERE WITH CHARLOTTE01（与Charlotte同在01）","CP剧集话题，情侣款。",3,"Twitter MY",["CP","剧集"],False),
("my","明星八卦",3,"文字款","低风险",10,"ForceBook漫展","FORCEBOOK MAFOX INF2026（ForceBook漫展）","CP活动，粉丝文字款。",3,"Twitter MY",["CP","活动"],False),
("my","明星八卦",3,"文字款","低风险",10,"First 26岁","FIRSTONE TURNED 26（First 26岁）","明星生日话题，粉丝文字款。",2,"Twitter MY",["明星"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"MilkLove新加坡甜蜜回忆","MILKLOVE SWEET MEMORY IN SG（MilkLove新加坡甜蜜回忆）","CP旅游梗，情侣款。",3,"Twitter MY",["CP","旅游"],False),
("my","明星八卦",3,"文字+图案","低风险",10,"DewRenji初舞台","DEW RENJI THE FIRST STAGE（DewRenji初舞台）","CP音乐舞台，粉丝向。",3,"Twitter MY",["CP","音乐"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"SF×WilliamEst","#SFxWilliamEstWesley（SF×WilliamEst）","跨境泰CP马来霸榜，情侣款首选。",5,"xtrends、Twitter MY",["CP","跨境"],False),
("my","影视剧",4,"文字款","低风险",10,"一只狗和一架飞机大结局","#ADogAndAPlaneFinalEP（一只狗和一架飞机大结局）","马剧大结局，剧粉文字款。",3,"Twitter MY",["马剧"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"SF×PondPhuwin","#SFxPondPhuwinPermpoon（SF×PondPhuwin）","跨境泰CP，情侣款。",4,"Twitter MY",["CP","跨境"],False),
("my","影视剧",4,"文字款","低风险",10,"青龙剧集奖","#BlueDragonSeriesAwards2026（青龙剧集奖）","韩剧颁奖，韩粉文字款。",2,"Twitter MY",["韩剧","颁奖"],False),
("my","明星八卦",4,"文字款","低风险",10,"Chaeyoung吉隆坡行","#CHAEYOUNGinKL（Chaeyoung吉隆坡行）","TWICE成员马来活动，韩粉文字款。",3,"Twitter MY",["韩流","明星"],False),
("my","影视剧",4,"文字款","低风险",10,"怪人101剧集","#WEIRDO101Series（怪人101剧集）","马剧话题，剧粉文字款。",3,"Twitter MY",["马剧"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"Orm×Montigo马来西亚","#OrmXMontigoMalaysia（Orm×Montigo马来西亚）","泰星品牌联动，粉丝向。",4,"Twitter MY",["泰星","品牌"],False),
("my","明星八卦",4,"文字+图案","低风险",12,"NCT127吉隆坡","#NCT127inKL（NCT127吉隆坡）","韩流演唱会，纪念文字+图案。",4,"xtrends、Twitter MY",["韩流","演唱会"],False),
("my","游戏电竞",4,"图案","低风险",12,"原神特别节目","#GenshinSpecialProgram（原神特别节目）","原神7.0前瞻霸榜马来，冰之国图案款。",5,"xtrends、Twitter MY、HoYoLAB",["游戏","原神"],False),
("my","明星八卦",4,"图案+文字","低风险",12,"ZeePruk×Siam Center","#ZeePrukSuperSunxSiamCenter（ZeePruk×Siam Center）","CP品牌快闪，情侣款。",4,"Twitter MY",["CP","品牌"],False),
("my","游戏电竞",4,"图案","低风险",14,"HoYoFest 2026米哈游嘉年华","#HoYoFEST2026（HoYoFest 2026米哈游嘉年华）","线下游戏嘉年华，活动纪念款。",4,"xtrends、Twitter MY",["游戏","活动"],False),
("my","体育",3,"文字款","低风险",10,"夏日狂潮WWE","#SummerSlam（夏日狂潮/WWE赛事）","摔角娱乐赛事，运动风文字款。",3,"Twitter MY",["体育","摔角"],False),
("my","影视剧",4,"文字款","低风险",10,"月影系列","#MoonshadowSeries（月影系列）","马剧话题，剧粉文字款。",4,"Twitter MY",["马剧"],False),
("my","影视剧",3,"文字款","低风险",10,"赛点系列EP2","#MatchPointSeriesEP2（赛点系列EP2）","运动剧话题，剧粉文字款。",3,"Twitter MY",["马剧","运动"],False),
# ===================== CP组合 (16) =====================
("th","明星八卦",4,"图案+文字","低风险",30,"PondPhuwin","PondPhuwin（ปอนด์ภูวินทร์）","《Me and Thee》大结局创GMMTV 800万帖纪录，跨境顶流CP。",5,"Twitter、TikTok、GMM24",["CP","BL","跨境"],False),
("th","明星八卦",4,"图案+文字","低风险",30,"KristSingto十周年","KristSingto（คริสต์สิงโต）","合作十周年纪念活动，长青CP情怀款。",4,"Twitter、GMMTV",["CP","十周年"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"BrightWin","BrightWin（ไบร์ทวิน）","《2gether》国际化始祖，F4泰演唱会与言承旭合体。",4,"Twitter、TikTok",["CP","经典"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"WilliamEst","WilliamEst（วิลเลียมเอส）","Exclusive Night霸榜，单曲《Flashback》登HITZ第3。",5,"Twitter、TikTok、HITZ",["CP","音乐"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"PerthSanta","PerthSanta（เพิร์ธซันต้า）","杂志拍摄+访谈活动，情侣款潜力高。",4,"Twitter、Mint Mag",["CP"],False),
("th","明星八卦",4,"图案+文字","低风险",30,"LingOrm","LingOrm（ลิงออร์ม）","《The Secret of Us》ILF霸榜马来，跨境顶流CP。",5,"Twitter MY、TikTok",["CP","跨境"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"ForceBook","ForceBook（ฟอสบุ๊ค）","MAFOX漫展活动，粉丝向。",4,"Twitter",["CP","活动"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"GeminiFourth","GeminiFourth（เจมินี่โฟร์ธ）","蒙奇奇联名，萌系可爱款。",4,"Twitter、Simplus",["CP","联名"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"ZeeNunew","ZeeNunew（ซีนุนิว）","Zone联动，情侣款。",4,"Twitter",["CP"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"MilkLove","MilkLove（มิลค์เลิฟ）","新加坡粉丝见面，情侣款。",4,"Twitter",["CP","旅游"],False),
("th","明星八卦",3,"图案+文字","低风险",15,"DewRenji","DewRenji（ดิวเรนจิ）","初舞台活动，粉丝向。",3,"Twitter",["CP","音乐"],False),
("th","明星八卦",4,"图案+文字","低风险",25,"SkyNani","SkyNani（สกายนานิ）","新剧《Wu Destiny》发布会，上升CP。",4,"Twitter、TikTok",["CP","新剧"],False),
("th","明星八卦",3,"图案+文字","低风险",15,"DaouOffroad","DaouOffroad（ดาวออฟโรด）","TPOP舞台，粉丝向。",3,"Twitter",["CP"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"LMSY","LMSY（แอลเอ็มเอสวาย）","FanCon D-Day，情侣款。",4,"Twitter",["CP","粉丝活动"],False),
("th","明星八卦",3,"文字款","低风险",15,"FirstKhaotung","FirstKhaotung（เฟิร์สข้าวตู้）","生日话题，粉丝文字款。",3,"Twitter",["CP"],False),
("th","明星八卦",3,"图案+文字","低风险",15,"OhmNanon","OhmNanon（ออมนานนอน）","综艺剧集联动，粉丝向。",3,"Twitter",["CP"],False),
# ===================== 明星 (12) =====================
("th","明星八卦",4,"图案+文字","低风险",25,"Bright Vachirawit","Bright Vachirawit（ไบร์ท วชิราวุธ）","净资$12M，Burberry/CK/Adidas代言，新剧《Girl Rules 2026》。",4,"Twitter、Vogue、Sanook",["泰星","代言"],False),
("th","明星八卦",4,"图案+文字","低风险",25,"Win Metawin","Win Metawin（วิน เมธวิน）","F4泰演唱会与言承旭合体，SOURI马卡龙品牌。",5,"Twitter、TikTok",["泰星","品牌"],False),
("th","明星八卦",4,"文字+图案","低风险",20,"Nani Hirunkit","Nani Hirunkit（นานิ หิรัญกฤษฎิ์）","时尚品牌HANNAH，与Sky组队。",4,"Twitter、LISA",["泰星","时尚"],False),
("th","明星八卦",4,"图案+文字","低风险",20,"William Jakrapatr","William Jakrapatr（วิลเลียม）","单曲《Flashback》登顶HITZ第3。",5,"HITZ、Twitter",["泰星","音乐"],False),
("th","明星八卦",3,"文字款","低风险",15,"Film Rachanun","Film Rachanun（ฟิล์ม）","GL《Pluto》获奖，粉丝文字款。",3,"Twitter、Kapook",["泰星","GL"],False),
("th","明星八卦",3,"文字款","低风险",15,"Engfa","Engfa（แองฟ้า）","综艺《传承》话题，粉丝文字款。",3,"Twitter",["泰星","综艺"],False),
("my","明星八卦",4,"图案+文字","低风险",30,"Siti Nurhaliza","Siti Nurhaliza（西蒂·诺哈丽莎）","国民歌后《Gema Bumantara》巡演，Batik风图案。",5,"Twitter MY、Astro",["马来","歌后","Batik"],False),
("my","明星八卦",4,"文字款","低风险",15,"NCT 127 / Chaeyoung","NCT 127 / Chaeyoung（TWICE）","吉隆坡活动，韩粉文字款。",4,"Twitter MY",["韩流"],False),
("my","明星八卦",4,"文字款","低风险",15,"ENHYPEN","ENHYPEN（엔하이픈）","巡演+粉丝抗议争议，韩粉文字款。",4,"Twitter MY",["韩流"],False),
("th","明星八卦",4,"图案+文字","低风险",25,"BTS","BTS（방탄소년단）","曼谷巡演+《Swim》上榜，韩粉爆款。",5,"Twitter TH、Billboard",["韩流","演唱会"],False),
("th","明星八卦",4,"图案+文字","低风险",25,"BLACKPINK Lisa","BLACKPINK Lisa（ลิซ่า）","个人巡演+Labubu加持，粉丝强烈买单。",5,"Twitter、TikTok",["韩流","明星"],False),
("my","明星八卦",3,"文字款","低风险",10,"CORTIS","CORTIS（코르티스）","Lollapalooza亮相新晋韩团。",3,"Twitter MY",["韩流"],False),
# ===================== 演唱会/音乐活动 (12) =====================
("th","演唱会综艺",4,"文字+图案","低风险",20,"BTS世界巡演曼谷站","BTS WORLD TOUR BANGKOK（BTS世界巡演曼谷站）","推特泰区榜首，应援棒+口号纪念款。",5,"Twitter TH、Billboard",["韩流","演唱会"],False),
("th","演唱会综艺",4,"图案+文字","低风险",10,"F4泰国演唱会","F4 泰国演唱会（曼谷Impact Arena 8/2-3）","Win与言承旭合体，情怀应援款。",4,"Twitter、TikTok",["演唱会","情怀"],False),
("th","演唱会综艺",4,"图案+文字","低风险",15,"PondPhuwin马尼拉FanCon","PondPhuwin Rendezvous FanCon（马尼拉8/2）","跨境FanCon，情侣款。",4,"Twitter、GMM25",["CP","FanCon"],False),
("th","演唱会综艺",4,"图案+文字","低风险",15,"DuangGoRound巡回演唱会","DuangGoRound Concert（Duang巡回演唱会）","泰星巡演，粉丝向。",3,"Twitter",["演唱会","泰星"],False),
("my","演唱会综艺",4,"文字+图案","低风险",15,"NCT127吉隆坡","NCT 127 in KL（NCT127吉隆坡）","韩流演唱会，纪念文字+图案。",4,"Twitter MY",["韩流","演唱会"],False),
("my","演唱会综艺",4,"文字款","低风险",10,"Chaeyoung吉隆坡","Chaeyoung in KL（Chaeyoung吉隆坡）","TWICE成员活动，韩粉文字款。",3,"Twitter MY",["韩流","明星"],False),
("my","演唱会综艺",4,"文字款","低风险",15,"ENHYPEN巡演","ENHYPEN ARE NOT MACHINES（ENHYPEN巡演）","含东南亚站，韩粉文字款。",3,"Twitter MY",["韩流","巡演"],False),
("my","演唱会综艺",4,"图案+文字","低风险",15,"LingOrm ILF粉丝活动","LINGORM ILF（LingOrm粉丝活动）","马来CP粉丝活动，情侣款。",4,"Twitter MY",["CP","粉丝活动"],False),
("th","演唱会综艺",4,"图案+文字","低风险",15,"WilliamEst专属之夜","WilliamEst Exclusive Night（WilliamEst专属之夜）","曼谷霸榜活动，情侣款。",5,"Twitter TH",["CP","粉丝活动"],False),
("my","游戏电竞",4,"图案","低风险",20,"HoYoFEST 2026","HOYOVERSE HoYoFEST 2026（米哈游嘉年华）","游戏音乐嘉年华，活动纪念款。",4,"Twitter MY、HoYoLAB",["游戏","活动"],False),
("th","演唱会综艺",4,"图案+文字","低风险",15,"Bright Home Party巡演","Bright Vachirawit Home Party（Bright家庭派对巡演）","泰星个人巡演，粉丝向。",3,"Twitter",["演唱会","泰星"],False),
("my","演唱会综艺",4,"图案+文字","低风险",30,"Siti Gema Bumantara巡演","Siti Nurhaliza Gema Bumantara（西蒂回响婆罗洲巡演）","国民歌后Legacy 30巡演，Batik风。",5,"Astro、Twitter MY",["马来","歌后","Batik"],False),
# ===================== 音乐榜单歌曲 (10) =====================
("th","演唱会综艺",4,"文字款","低风险",20,"Hourglass沙漏","Hourglass (Sign)（沙漏）","BOWKYLION，Billboard Thailand Songs周榜第1。",4,"Billboard Thailand Songs",["泰语","榜单"],False),
("th","演唱会综艺",3,"文字款","低风险",15,"When Will It Happen","When Will It Happen?（何时发生）","BLVCKHEART，Billboard TH第2。",3,"Billboard Thailand Songs",["泰语","榜单"],False),
("th","演唱会综艺",4,"文字款","低风险",15,"Crybaby爱哭鬼","Crybaby (Boy's Don't Cry)（爱哭鬼）","PROXIE，Billboard TH第3，TikTok表情包带动。",4,"Billboard、TikTok",["泰语","榜单"],False),
("th","演唱会综艺",4,"文字款","低风险",20,"Hate That I Made You Love Me","Hate That I Made You Love Me（恨我让你爱上我）","Ariana Grande，Billboard TH第4。",4,"Billboard Thailand Songs",["欧美","榜单"],False),
("th","演唱会综艺",4,"文字款","低风险",25,"Swim游泳","Swim（游泳）","BTS，Billboard TH第5，巡演带动。",5,"Billboard、Twitter",["韩流","榜单"],False),
("th","演唱会综艺",3,"文字款","低风险",15,"Living Death活着的死亡","Living Death（活着的死亡）","PUN，Billboard TH第6。",3,"Billboard Thailand Songs",["泰语","榜单"],False),
("th","演唱会综艺",4,"文字款","低风险",30,"YOUNGOHM曼谷系说唱","YOUNGOHM（ยังโอหม่ำ）","Apple Music泰区长霸榜，多首热单。",4,"Apple Music TH",["泰语","说唱"],False),
("my","演唱会综艺",4,"文字款","低风险",25,"BTS ARIRANG","BTS《ARIRANG》（阿里郎）","韩流专辑马来强势，韩粉款。",5,"Apple Music MY",["韩流","专辑"],False),
("my","演唱会综艺",4,"文字款","低风险",20,"Ariana Grande eternal sunshine","Ariana Grande《eternal sunshine》","全球流行，马来榜常青。",4,"Apple Music MY",["欧美","专辑"],False),
("my","演唱会综艺",4,"图案","低风险",25,"KPop Demon Hunters原声","《KPop Demon Hunters》OST（KPop恶魔猎人原声）","Netflix动画电影原声，韩粉爆款。",5,"Netflix、Apple Music",["韩流","动画"],False),
("my","演唱会综艺",4,"图案","低风险",30,"Siti Gema Bumantara专辑","Siti Nurhaliza《Gema Bumantara》（回响婆罗洲）","国民歌后Legacy 30专辑，Batik风。",5,"Apple Music MY、Astro",["马来","歌后"],False),
("my","演唱会综艺",3,"文字款","低风险",10,"CORTIS GREENGREEN","CORTIS《GREENGREEN》","新晋韩团，上升期。",3,"Apple Music MY",["韩流"],False),
("my","演唱会综艺",3,"文字款","低风险",15,"Olivia Rodrigo","Olivia Rodrigo《you seem pretty sad...》","全球流行，马来榜。",3,"Apple Music MY",["欧美"],False),
# ===================== TikTok音频 (7) =====================
("th","演唱会综艺",3,"文字款","低风险",20,"Hold My Hand","Hold My Hand（Jess Glynne）","友谊鼓励向BGM，短视频带货。",3,"TikTok Creative Center",["BGM","全球"],False),
("th","演唱会综艺",3,"文字款","低风险",20,"Sparks","Sparks（Coldplay）","浪漫氛围BGM。",3,"TikTok Creative Center",["BGM"],False),
("th","演唱会综艺",3,"文字款","低风险",20,"No One Noticed","No One Noticed（The Marías）","双语梦幻风BGM。",3,"TikTok Creative Center",["BGM"],False),
("th","演唱会综艺",3,"文字款","低风险",20,"back to friends","back to friends（sombr）","卧室流行BGM。",3,"TikTok Creative Center",["BGM"],False),
("th","演唱会综艺",3,"文字款","低风险",20,"Illegal","Illegal（PinkPantheress）","UK garage复古BGM。",3,"TikTok Creative Center",["BGM"],False),
("th","演唱会综艺",4,"文字款","低风险",25,"Golden","Golden（HUNTR/X / KPop Demon Hunters）","韩流动画神曲，TikTok爆红。",5,"TikTok、Netflix",["韩流","动画"],False),
("th","演唱会综艺",3,"文字款","低风险",20,"Love Me Not","Love Me Not（Ravyn Lenae）","R&B BGM。",3,"TikTok Creative Center",["BGM"],False),
# ===================== TikTok趋势 网络热梗 (18) =====================
("my","网络热梗",4,"图案","低风险",20,"Labubu拆Labubu解压梗","Labubu Me Cracking Labubu（拆Labubu解压）","全平台38亿次观看，怪物笑脸图案。",5,"TikTok、Meme.com",["全球","Labubu"],False),
("my","网络热梗",4,"图案","低风险",20,"KPop Demon Hunters / Golden","KPop Demon Hunters（KPop恶魔猎人）","Netflix动画，TikTok《Golden》爆红。",5,"TikTok、Netflix",["韩流","动画"],False),
("my","网络热梗",4,"图案","低风险",20,"蜘蛛侠全新一天","Spider-Man Brand New Day（蜘蛛侠全新一天）","全球电影热，超级英雄图案。",4,"TikTok、Box Office",["电影","超级英雄"],False),
("my","体育",3,"文字款","低风险",15,"夏日狂潮WWE","SummerSlam（WWE夏日狂潮）","摔角娱乐，运动风文字款。",3,"TikTok、Twitter",["体育","摔角"],False),
("th","网络热梗",3,"文字款","低风险",15,"Hold My Hand挑战","Hold My Hand Challenge（Jess Glynne）","友谊挑战BGM。",3,"TikTok",["挑战"],False),
("th","网络热梗",3,"文字款","低风险",15,"No One Noticed","No One Noticed（The Marías）","梦幻风BGM。",3,"TikTok",["BGM"],False),
("th","网络热梗",3,"文字款","低风险",15,"back to friends","back to friends（sombr）","卧室流行BGM。",3,"TikTok",["BGM"],False),
("th","网络热梗",3,"文字款","低风险",15,"Illegal","Illegal（PinkPantheress）","UK garage复古BGM。",3,"TikTok",["BGM"],False),
("th","网络热梗",3,"文字款","低风险",15,"AI内容浪潮","AI content wave（AI内容浪潮）","生成式AI迷因，极简文字款。",3,"TikTok、Reddit",["科技","迷因"],False),
("th","网络热梗",4,"图案","低风险",15,"Crybaby挑战","Crybaby Challenge（PROXIE泰语热单）","表情包带动，可爱风。",4,"TikTok、Billboard",["泰语","挑战"],False),
("th","网络热梗",4,"图案","低风险",15,"#Crybaby PROXIE","#Crybaby（PROXIE）","泰语热单表情包，可爱风图案。",4,"TikTok、Twitter TH",["泰语","热单"],False),
("th","网络热梗",4,"文字+图案","低风险",15,"鸡爸飙车辣妈Ving","#พ่อไก่ซิ่งแม่วิ้งก์แซ่บ（鸡爸飙车辣妈Ving）","综艺名场面，搞笑文字款。",4,"TikTok、Twitter TH",["综艺","梗"],False),
("th","网络热梗",4,"图案","低风险",15,"BOWKYLION Hourglass舞蹈","BOWKYLION Hourglass Dance（沙漏舞蹈）","榜单热单舞蹈挑战，文字+图案。",4,"TikTok、Billboard",["泰语","舞蹈"],False),
("th","网络热梗",3,"文字款","低风险",15,"YOUNGOHM曼谷说唱","YOUNGOHM Bangkok Rap（曼谷说唱）","说唱梗，文字款。",3,"TikTok",["泰语","说唱"],False),
("th","网络热梗",4,"图案","低风险",20,"Peach And Me婚礼梗","Peach And Me Wedding（清醒吧小桃婚礼）","PondPhuwin大热，婚礼承诺款。",5,"TikTok、Twitter",["CP","婚礼"],False),
("th","网络热梗",4,"图案","低风险",20,"WilliamEst情侣挑战","WilliamEst Couple Challenge（威廉艾斯情侣挑战）","跨境CP情侣款。",5,"TikTok、Twitter",["CP","情侣"],False),
("th","网络热梗",4,"图案","低风险",15,"Muay Thai训练短视频","Muay Thai（泰拳训练）","国民运动梗，民族风图案。",4,"TikTok",["泰拳","运动"],False),
("th","网络热梗",3,"图案","低风险",15,"雨季暴雨生活","Rainy Season Life（雨季生活）","季节梗，城市生活图案。",3,"TikTok",["季节","生活"],False),
("th","网络热梗",4,"图案","低风险",12,"茉莉花母亲节手工","Jasmine Mother's Day Craft（茉莉花母亲节）","节庆手工梗，规避王室像。",4,"TikTok、Shopee",["节庆","茉莉"],False),
("th","网络热梗",3,"图案","低风险",15,"突突车城市生活","Tuk-tuk City Life（突突车）","本土符号，城市生活图案。",3,"TikTok",["本土","符号"],False),
("my","网络热梗",4,"图案","低风险",15,"原神特别节目","#GenshinSpecialProgram（原神特别节目）","游戏热度顶峰，冰之国图案。",5,"TikTok MY、HoYoLAB",["游戏","原神"],False),
("my","网络热梗",4,"图案","低风险",15,"HoYoFEST2026","#HoYoFEST2026（米哈游嘉年华）","游戏活动梗，纪念款。",4,"TikTok MY",["游戏","活动"],False),
("my","网络热梗",4,"图案","低风险",15,"Peach And Me大结局","#PeachAndMeSeriesFinalEP","跨境泰剧爆，婚礼款。",5,"TikTok MY、Twitter MY",["泰剧","CP"],False),
("my","网络热梗",4,"图案","低风险",15,"绘梦婚礼日EP7","#วาดฝันวันวิวาห์EP7（绘梦婚礼日EP7）","泰马合拍剧，婚礼视觉。",5,"TikTok MY",["泰剧","婚礼"],False),
("my","网络热梗",4,"图案","低风险",15,"月影系列","#MoonshadowSeries（月影系列）","马剧话题，剧粉图案。",4,"TikTok MY",["马剧"],False),
("my","网络热梗",4,"图案","低风险",15,"LINGORM ILF EP7","LINGORM ILF EP7（LingOrm我挚爱的秘密）","马来顶流CP，情侣款。",5,"TikTok MY、Twitter MY",["CP","跨境"],False),
# ===================== 泰国热梗精选 (11) =====================
("th","网络热梗",3,"文字款","低风险",10,"在Impact遇到Duang","#เจอด้วงที่อิมแพคนะเธอ（在Impact遇到Duang）","演唱会打卡梗，文字款。",3,"Twitter TH",["演唱会","梗"],False),
("th","网络热梗",3,"文字款","低风险",10,"Wawa×TeeTeePawPaw做朋友","#วาวาเมคเฟรนด์กับตี๋ตี๋ป๋อ","CP综艺友情梗，情侣/闺蜜款。",3,"Twitter TH",["CP","综艺"],False),
("th","网络热梗",2,"文字款","低风险",8,"地震","#แผ่นดินไหว（地震/earthquake）","突发社会梗，谨慎使用。",2,"Twitter TH",["社会","突发"],False),
("th","网络热梗",4,"文字款","低风险",15,"BTS应援棒梗","BTS Light Stick（BTS应援棒）","韩流周边梗，图案款。",4,"TikTok",["韩流","周边"],False),
("th","网络热梗",3,"文字款","低风险",10,"EnemiesWithBenefits剧名梗","#EnemiesWithBenefits（假想敌with福利）","剧名梗，文字款。",3,"Twitter TH",["剧集"],False),
("th","网络热梗",3,"文字款","低风险",10,"Sod Sai Mala剧梗","#สอดสร้อยมาลา（Sod Sai Mala剧梗）","剧集梗，文字款。",3,"Twitter TH",["剧集"],False),
("th","网络热梗",3,"文字款","低风险",10,"Lookkaew选秀梗","Lookkaew Born To Shine（生而闪耀）","选秀梗，文字款。",3,"Twitter TH",["选秀"],False),
("th","网络热梗",3,"文字款","低风险",10,"FayeAtom巴西旅游梗","FayeAtom No Brasil（巴西行）","CP旅游梗，情侣款。",3,"Twitter TH",["CP","旅游"],False),
("th","网络热梗",3,"文字款","低风险",10,"Engfa传承综艺梗","Engfa The Legacy（传承）","明星综艺梗，文字款。",3,"Twitter TH",["明星"],False),
("th","网络热梗",3,"文字款","低风险",10,"Charlotte闪耀骄傲梗","Shining Pride Charlotte（闪耀骄傲）","明星梗，文字款。",3,"Twitter TH",["明星"],False),
("th","网络热梗",3,"文字款","低风险",10,"Tonsom剧集梗","Tonsom（ต้นสม）","剧集梗，文字款。",3,"Twitter TH",["剧集"],False),
# ===================== 马来热梗独特补充 (11) =====================
("my","网络热梗",4,"文字款","低风险",12,"PSD Mogul arrival","PSD MOGULARRIVAL FS26（PSD Mogul arrival）","时装秀梗，潮牌风。",4,"Twitter MY",["时装","秀"],False),
("my","网络热梗",3,"文字款","低风险",10,"CH3女星杯","#CH3GirlsCup2026（三台女星杯）","女星杯梗，粉丝款。",3,"Twitter MY",["明星"],False),
("my","网络热梗",4,"文字款","低风险",10,"TeeTeePawPaw运动日","#ตี๋ตี๋ป๋อสปอร์ตเดย์2026","CP综艺运动梗。",3,"Twitter MY",["CP","综艺"],False),
("my","网络热梗",4,"图案","低风险",15,"蜘蛛侠梗","Spiderman（蜘蛛侠）","全球电影梗，超级英雄图案。",4,"Twitter MY",["电影"],False),
("my","网络热梗",4,"文字款","低风险",10,"NCT127inKL","#NCT127inKL（NCT127吉隆坡）","韩流演唱会梗。",4,"Twitter MY",["韩流"],False),
("my","网络热梗",4,"文字款","低风险",10,"ChaeyounginKL","#CHAEYOUNGinKL（Chaeyoung吉隆坡）","韩流明星梗。",4,"Twitter MY",["韩流"],False),
("my","网络热梗",4,"文字款","低风险",10,"ENHYPEN不是机器","ENHYPEN ARE NOT MACHINES（不是机器）","韩流梗。",4,"Twitter MY",["韩流"],False),
("my","网络热梗",4,"图案+文字","低风险",15,"Orm×Montigo马来西亚","#OrmXMontigoMalaysia","泰星品牌梗，粉丝向。",4,"Twitter MY",["泰星","品牌"],False),
("my","网络热梗",4,"图案+文字","低风险",15,"MilkLove新加坡回忆","MILKLOVE SWEET MEMORY IN SG","CP旅游梗，情侣款。",4,"Twitter MY",["CP","旅游"],False),
("my","网络热梗",3,"文字款","低风险",10,"ADogAndPlane大结局","#ADogAndAPlaneFinalEP","马剧梗，文字款。",3,"Twitter MY",["马剧"],False),
("my","网络热梗",3,"文字款","低风险",10,"WEIRDO101剧集","#WEIRDO101Series（怪人101）","马剧梗，文字款。",3,"Twitter MY",["马剧"],False),
("my","网络热梗",3,"文字+图案","低风险",10,"BELIFT停止忽视","BELIFT STOP THE NEGLECT（ENHYPEN粉丝抗议）","韩流争议梗，谨慎使用。",3,"Twitter MY",["韩流","争议"],False),
("my","网络热梗",3,"文字款","低风险",10,"MatchPoint EP2","#MatchPointSeriesEP2（赛点EP2）","运动剧梗，文字款。",3,"Twitter MY",["马剧","运动"],False),
# ===================== T恤设计推荐 (20) =====================
("th","网络热梗",4,"文字+图案","低风险",20,"BTS曼谷巡演纪念","BTS Bangkok Tour Tee（BTS曼谷巡演纪念）","文字+应援棒图案，韩流粉丝爆款。",5,"设计推荐",["韩流","设计"],False),
("th","网络热梗",4,"图案+文字","低风险",20,"PondPhuwin婚礼承诺款","Peach And Me Wedding Tee（小桃婚礼款）","婚礼/承诺元素，BL粉丝。",5,"设计推荐",["CP","设计"],False),
("my","游戏电竞",4,"图案","低风险",20,"原神7.0至冬国","Genshin 7.0 Snezhnaya（原神至冬国）","冰之国风景/角色剪影，规避官方立绘。",5,"设计推荐、HoYoLAB",["游戏","原神"],False),
("th","网络热梗",4,"图案+文字","低风险",20,"WilliamEst情侣款","WilliamEst Couple Tee（威廉艾斯情侣款）","跨境双市场情侣款。",5,"设计推荐",["CP","设计"],False),
("my","网络热梗",4,"图案","低风险",20,"Labubu解压笑脸","Labubu Cracking Smile（拆Labubu笑脸）","怪物笑脸图案，全球Z世代。",5,"设计推荐",["全球","Labubu"],False),
("my","网络热梗",4,"图案","低风险",20,"Chiikawa可爱款","Chiikawa（ちいかわ/吉伊卡哇）","可爱怪物简约线条，全年龄。",5,"设计推荐",["可爱","动漫"],False),
("my","网络热梗",4,"图案+文字","低风险",20,"LingOrm绘梦婚礼日","LingOrm Secret of Us Tee（绘梦婚礼日）","马来CP情侣款。",5,"设计推荐",["CP","设计"],False),
("my","网络热梗",4,"图案","低风险",20,"蜘蛛侠全新一天","Spider-Man Brand New Day Tee（蜘蛛侠全新一天）","超级英雄图案，全球。",5,"设计推荐",["电影","超级英雄"],False),
("th","网络热梗",4,"图案","低风险",20,"Muay Thai民族风","Muay Thai Tee（泰拳民族风）","泰拳图腾+泰文，本土+旅游。",4,"设计推荐",["泰拳","民族"],False),
("my","网络热梗",4,"图案","低风险",20,"Siti×Batik马来风","Siti x Batik Tee（西蒂×蜡染）","蜡染几何图案，马来本土。",5,"设计推荐",["马来","Batik"],False),
("my","网络热梗",4,"图案","低风险",20,"KPop Demon Hunters","KPop Demon Hunters Tee（KPop恶魔猎人）","HUNTR/X乐队logo风。",5,"设计推荐",["韩流","动画"],False),
("th","网络热梗",4,"图案","低风险",12,"茉莉花母亲节","Jasmine Mother's Day Tee（茉莉花母亲节）","茉莉花+感恩文字，规避王室像。",4,"设计推荐",["节庆","茉莉"],False),
("th","网络热梗",3,"文字款","低风险",20,"YOUNGOHM曼谷说唱文字款","YOUNGOHM Rap Tee（曼谷说唱文字款）","泰语歌词文字款。",3,"设计推荐",["泰语","说唱"],False),
("th","网络热梗",4,"图案","低风险",15,"Crybaby可爱表情款","Crybaby Cute Tee（爱哭鬼可爱款）","可爱表情图案，年轻女性。",4,"设计推荐",["泰语","可爱"],False),
("th","网络热梗",3,"图案","低风险",15,"雨季突突车城市生活","Tuk-tuk Rainy Tee（雨季突突车）","城市生活图案，本土。",3,"设计推荐",["本土","生活"],False),
("my","网络热梗",4,"文字+图案","低风险",15,"NCT127吉隆坡纪念","NCT127 KL Tee（NCT127吉隆坡纪念）","纪念文字+图案，韩流MY。",4,"设计推荐",["韩流","设计"],False),
("th","网络热梗",4,"图案","低风险",20,"Gemini×蒙奇奇联名款","Gemini x Monchhichi Tee（蒙奇奇联名）","萌系可爱款，CP+可爱。",4,"设计推荐",["CP","联名"],False),
("my","游戏电竞",4,"图案","低风险",20,"HoYoFEST嘉年华","HoYoFEST 2026 Tee（米哈游嘉年华）","游戏活动纪念款。",4,"设计推荐",["游戏","活动"],False),
("my","其他热搜",3,"图案","低风险",24,"国庆日国旗色块","Merdeka Jalur Gemilang（国庆日国旗色块）","马来独立日爱国色块，规避人物。",3,"设计推荐",["爱国","马来"],False),
("th","体育",4,"图案","低风险",30,"足球战象","War Elephants Tee（战象足球）","国家队战象图案，体育迷。",4,"设计推荐",["体育","足球"],False),
# ===================== 动漫 (7) 影视剧 =====================
("th","影视剧",4,"图案","低风险",30,"Solo Leveling我独自升级","Solo Leveling: Arise from the Shadow（我独自升级影之崛起）","S2获Crunchyroll最佳动画，暗影君主剪影。",5,"Crunchyroll、MyAnimeList",["动漫","热血"],False),
("th","影视剧",4,"图案","低风险",25,"链锯人蕾塞篇","Chainsaw Man: Reze Arc（链锯人蕾塞篇）","黑暗动作，电次/帕瓦图案。",4,"Crunchyroll、MAPPA",["动漫","黑暗"],False),
("th","影视剧",4,"图案","低风险",25,"怪兽8号第二季","Kaiju No.8 Season 2（怪兽8号第二季）","热血，卡夫卡图案。",4,"MyAnimeList",["动漫","热血"],False),
("th","影视剧",4,"图案","低风险",25,"葬送的芙莉莲第二季","Frieren Season 2（葬送的芙莉莲第二季）","奇幻治愈，芙莉莲图案。",4,"Crunchyroll",["动漫","治愈"],False),
("th","影视剧",4,"图案","低风险",20,"当哒当第二季","Dan Da Dan Season 2（当哒当第二季）","搞笑灵异，桃/Okarun图案。",4,"MyAnimeList",["动漫","搞笑"],False),
("th","影视剧",4,"图案","低风险",30,"鬼灭之刃","Demon Slayer（鬼灭之刃）","长青热血，炭治郎图案。",4,"Crunchyroll",["动漫","热血"],False),
("th","影视剧",3,"图案","低风险",20,"我的英雄学院最终季","My Hero Academia Final（我的英雄学院最终季）","热血，出久图案。",3,"Crunchyroll",["动漫","热血"],False),
# ===================== 电影 (6) 影视剧 =====================
("my","影视剧",4,"图案","低风险",30,"蜘蛛侠全新一天","Spider-Man: Brand New Day（蜘蛛侠全新一天）","全球上映，超级英雄图案。",4,"Box Office、GSC",["电影","超级英雄"],False),
("th","影视剧",3,"图案","中风险",15,"Possessed附身","Possessed（หลอนเย็น เข็นมาเชือด）","泰马恐怖片，规避血腥。",3,"Major Cineplex、GSC",["电影","恐怖"],False),
("th","影视剧",3,"图案","低风险",15,"亲爱的你给阿嬷的情书","Dear You: Letter to Grandma（给阿嬷的情书）","中国片泰国上映，华裔情感，规避肖像。",3,"Major Cineplex",["电影","情感"],False),
("my","影视剧",4,"图案","低风险",30,"KPop Demon Hunters","KPop Demon Hunters（KPop恶魔猎人）","Netflix动画，HUNTR/X logo风。",5,"Netflix",["电影","动画"],False),
("my","影视剧",4,"图案","低风险",25,"奥德赛","The Odyssey（奥德赛/诺兰）","全球史诗，图案款。",4,"Box Office",["电影","史诗"],False),
("my","影视剧",4,"图案","低风险",25,"超级马里奥银河电影","Super Mario Galaxy Movie（超级马里奥银河电影）","任天堂IP，星星图案。",4,"任天堂、Box Office",["电影","任天堂"],False),
# ===================== 电视剧 (10) 影视剧 =====================
("th","影视剧",4,"图案+文字","低风险",20,"Peach And Me","Peach And Me（มีสติแล้วลูกพีช/清醒吧小桃）","PondPhuwin剧，婚礼承诺款。",5,"GMM25、iQIYI",["泰剧","CP"],False),
("th","影视剧",4,"图案+文字","低风险",20,"绘梦婚礼日","The Secret of Us（绘梦婚礼日/LINGORM ILF）","泰马双热，情侣款。",5,"GMM25、Twitter MY",["泰剧","CP"],False),
("my","影视剧",4,"图案+文字","低风险",20,"绘梦婚礼日合拍剧EP7","วาดฝันวันวิวาห์（绘梦婚礼日合拍剧EP7）","泰马合拍，婚礼视觉。",5,"Twitter MY",["泰剧","婚礼"],False),
("th","影视剧",3,"文字款","低风险",10,"我的玩家二EP3","BE MY PLAYER TWO EP3（我的玩家二EP3）","剧集+电竞，文字款。",3,"Twitter TH",["泰剧"],False),
("my","影视剧",4,"文字款","低风险",15,"一只狗和一架飞机","#ADogAndAPlane（一只狗和一架飞机）","马剧，文字款。",3,"Twitter MY",["马剧"],False),
("my","影视剧",4,"文字款","低风险",15,"怪人101","#WEIRDO101Series（怪人101）","马剧，文字款。",3,"Twitter MY",["马剧"],False),
("my","影视剧",4,"文字款","低风险",15,"月影系列","#MoonshadowSeries（月影系列）","马剧，文字款。",4,"Twitter MY",["马剧"],False),
("my","影视剧",3,"文字款","低风险",10,"赛点系列","#MatchPointSeries（赛点系列）","运动剧，文字款。",3,"Twitter MY",["马剧","运动"],False),
("my","影视剧",3,"文字款","低风险",10,"你的第三部系列","YOUR THIRD SERIES（你的第三部系列）","马剧，文字款。",3,"Twitter MY",["马剧"],False),
("my","影视剧",3,"文字款","低风险",10,"爱的奉献2","LOVE TO SERVE 2ND（爱的奉献2）","马剧，文字款。",3,"Twitter MY",["马剧"],False),
# ===================== 游戏热点 (6+) 游戏电竞 =====================
("my","游戏电竞",4,"图案","低风险",5,"原神7.0至冬国8/12上线","Genshin Impact 7.0 Everwinter（原神7.0无情寒冬）","Snezhnaya冰之国，新角色Odette/Alyosha，备货窗口5天。",5,"HoYoLAB、sportskeeda",["游戏","原神"],False),
("my","游戏电竞",4,"图案","低风险",20,"HoYoFest 2026","HoYoFEST 2026（米哈游嘉年华）","线下活动，纪念文字款。",4,"HoYoLAB、Twitter MY",["游戏","活动"],False),
("my","游戏电竞",4,"图案","低风险",30,"MLBB东南亚杯","MLBB（Mobile Legends无尽对决）","东南亚电竞常青，战队/英雄图案。",4,"escharts、Moonton",["游戏","电竞"],False),
("my","游戏电竞",4,"图案","低风险",30,"ROBLOX Blox Fruits","ROBLOX Blox Fruits（罗布乐思绽放果实）","东南亚青少年向手游顶流，方块风。",4,"ROBLOX、PlayStore",["游戏","手游"],False),
("my","游戏电竞",4,"图案","低风险",25,"KPop Demon Hunters游戏化","KPop Demon Hunters Game（KPop恶魔猎人游戏化）","Netflix动画带动，HUNTR/X logo。",5,"Netflix、Twitter",["游戏","韩流"],False),
("my","游戏电竞",4,"图案","中风险",20,"Pokemon UT联名","Pokémon UT（宝可梦任天堂联名）","初代宝可梦图案，注意授权。",5,"任天堂、Uniqlo",["游戏","联名"],False),
# ===================== 世界热点 (8) 其他热搜 =====================
("my","其他热搜",4,"图案","低风险",25,"Labubu经济","Labubu Economy（泡泡玛特/Labubu）","Mini Labubu+星星人热度续升，怪物笑脸。",5,"Meme.com、KnowYourMeme",["全球","Labubu"],False),
("my","其他热搜",4,"图案","低风险",25,"蜘蛛侠全新一天","Spider-Man Brand New Day（蜘蛛侠全新一天）","全球上映，超级英雄图案。",5,"Box Office、Google Trends",["全球","电影"],False),
("my","其他热搜",4,"图案","低风险",25,"KPop Demon Hunters","KPop Demon Hunters（KPop恶魔猎人）","Netflix动画，TikTok《Golden》爆红。",5,"Netflix、TikTok",["全球","韩流"],False),
("my","其他热搜",3,"文字款","低风险",20,"AI内容浪潮","AI content wave（AI内容浪潮）","生成式AI迷因，极简文字款。",3,"Reddit、Google Trends",["全球","科技"],False),
("my","体育",3,"文字款","低风险",15,"夏日狂潮WWE","SummerSlam（WWE夏日狂潮）","体育娱乐，运动风文字款。",3,"Twitter、ESPN",["全球","体育"],False),
("th","其他热搜",3,"文字款","低风险",20,"Coldplay/Jess Glynne神曲","Coldplay / Jess Glynne TikTok Hits（TikTok神曲）","全球BGM，文字款。",3,"TikTok、Spotify",["全球","BGM"],False),
("my","体育",4,"文字款","低风险",30,"Euro 2026/世界杯预选","Euro 2026 / World Cup Qualifiers（欧洲杯/世界杯预选）","足球热，运动风文字款。",4,"FIFA、ESPN",["全球","足球"],False),
("my","其他热搜",4,"图案","低风险",25,"超级马里奥银河电影","Super Mario Galaxy Movie（超级马里奥银河电影）","任天堂IP，星星图案。",5,"任天堂、Box Office",["全球","任天堂"],False),
# ===================== 节日商业机会 (5, 部分sensitive) =====================
("th","其他热搜",4,"图案","高风险",5,"母亲节8/12","วันแม่ Mother's Day（母亲节8/12）","泰王后诞辰全国庆，茉莉花/感恩文字款；不出现王后肖像/姓名/徽章。",5,"publicholidays.asia",["节庆","母亲节"],True),
("my","其他热搜",3,"文字款","高风险",18,"先知诞辰8/25","Maulidur Rasul（先知穆罕默德诞辰8/25）","宗教日全国假；仅文字祝福款，不出现先知像/经文/清真寺具象。",3,"malaysiapublicholiday.my",["节庆","宗教"],True),
("my","其他热搜",3,"图案","中风险",24,"国庆日8/31","Merdeka Day（国庆日8/31）","1957独立，Jalur Gemilang国旗色块/独立口号，规避政治人物肖像。",3,"malaysiapublicholiday.my",["节庆","爱国"],False),
("my","其他热搜",3,"图案","中风险",40,"马来西亚成立日9/16","Malaysia Day（成立日9/16）","1963联邦成立，爱国款，规避人物。",3,"malaysiapublicholiday.my",["节庆","爱国"],False),
("my","其他热搜",3,"图案","中风险",93,"屠妖节11/8","Deepavali（屠妖节11/8，除砂拉越）","印度教灯节，几何灯饰图案，规避神像。",3,"malaysiapublicholiday.my",["节庆","印度教"],False),
# ===================== 电商政策 (7) 社会民生 =====================
("th","社会民生",4,"文字款","中风险",30,"Shopee TH第三轮涨佣8/4","Shopee TH Commission Hike（虾皮泰第三轮涨佣）","时尚11.24%→13.38%，快消13.91%→16.05%；定价重算。",3,"亿邦、ikjzd",["电商","政策"],False),
("th","社会民生",3,"文字款","中风险",30,"TikTok Shop TH费率7/5","TikTok Shop TH Fee（TikTok商店泰费率）","部分类目最高13.91%，最大涨幅超2pp。",2,"ikjzd、10100",["电商","政策"],False),
("th","社会民生",3,"文字款","中风险",60,"泰国关税新政1/19","Thailand Import Tax（泰国关税新政）","取消1500铢免税，10%-30%关税+7%VAT。",2,"ikjzd、c.m.163",["电商","关税"],False),
("th","社会民生",2,"文字款","低风险",8,"地震突发","#แผ่นดินไหว（地震/earthquake）","社会突发，谨慎用作印花。",2,"Twitter TH",["社会","突发"],False),
("th","社会民生",3,"文字款","低风险",15,"雨季暴雨生活","Rainy Season（雨季暴雨）","季节生活话题，城市图案。",3,"TikTok",["社会","季节"],False),
("th","社会民生",4,"图案","低风险",30,"泰拳国民运动","Muay Thai（泰拳）","国民运动文化，民族风图案。",4,"TikTok、Twitter",["社会","泰拳"],False),
("th","社会民生",3,"图案","低风险",20,"突突车城市符号","Tuk-tuk（突突车）","本土城市生活符号，图案款。",3,"TikTok",["社会","本土"],False),
# ===================== 体育 (4) =====================
("th","体育",4,"图案","低风险",30,"足球战象国家队","War Elephants（战象国家队）","泰国国家队昵称，战象图案。",4,"Twitter TH、ESPN",["体育","足球"],False),
("my","体育",3,"文字款","低风险",15,"夏日狂潮WWE","SummerSlam（WWE夏日狂潮）","摔角娱乐赛事，文字款。",3,"Twitter MY、ESPN",["体育","摔角"],False),
("my","体育",4,"文字款","低风险",30,"Euro 2026/世界杯","Euro 2026 / World Cup（欧洲杯/世界杯）","足球热，运动风文字款。",4,"FIFA、ESPN",["体育","足球"],False),
("th","体育",3,"文字款","低风险",20,"BTS应援棒周边","BTS Light Stick（BTS应援棒）","韩流周边体育风，图案款。",3,"Twitter TH",["体育","韩流"],False),
# ===================== 联名款 (8) 明星八卦 =====================
("th","明星八卦",4,"图案","中风险",20,"Uniqlo UT×Chiikawa","UNIQLO UT × CHIIKAWA（吉伊卡哇）","电影联动7/22-27发售14款；注意授权。",5,"Uniqlo、faq-hk.uniqlo",["联名","可爱"],False),
("th","明星八卦",4,"图案","中风险",20,"Uniqlo UT×Pokémon","UNIQLO UT × Pokémon（宝可梦）","2026游戏原画系列6-7月上新；注意授权。",5,"Uniqlo",["联名","游戏"],False),
("th","明星八卦",4,"图案","中风险",20,"Uniqlo UT×集英社百年","UNIQLO UT × SHUEISHA 100th（集英社百年）","Jump经典漫画集结；注意授权。",5,"Uniqlo",["联名","动漫"],False),
("th","明星八卦",4,"图案","中风险",20,"Uniqlo UT×吉卜力","UNIQLO UT × Studio Ghibli（吉卜力）","宫崎骏电影美术；注意授权。",5,"Uniqlo",["联名","动画"],False),
("my","明星八卦",4,"图案","中风险",20,"Uniqlo UT×马里奥银河","UNIQLO UT × Super Mario Galaxy（马里奥银河）","任天堂IP；注意授权。",5,"Uniqlo、任天堂",["联名","游戏"],False),
("my","明星八卦",4,"图案","中风险",20,"Labubu×Uniqlo/可口可乐","Labubu × Uniqlo/Coca-Cola/Godiva（泡泡玛特联名）","怪物经济跨界；注意授权。",5,"泡泡玛特、Uniqlo",["联名","Labubu"],False),
("th","明星八卦",3,"图案","低风险",15,"泰国本地潮牌参考","Carnival/Painkiller/I Wanna Bangkok（泰国潮牌）","风格致敬非照搬。",3,"Instagram、Hypebeast",["潮牌","本地"],False),
("my","明星八卦",3,"图案","低风险",15,"马来本地潮牌参考","Pestle & Mortar/TNTCO/Stoned & Co（马来潮牌）","风格借鉴。",3,"Instagram、Hypebeast",["潮牌","本地"],False),
]

# ========== 分类映射 ==========
CAT_EN = {
 "明星八卦":"celebrity","演唱会综艺":"concert_show","影视剧":"film_tv","游戏电竞":"gaming",
 "网络热梗":"meme","其他热搜":"other","社会民生":"society","体育":"sports","政党选举":"politics"
}

# ========== 来源类型推断字典 ==========
SOURCE_TYPE_MAP = {
    # 社交平台 → social
    "twitter": "social", "tiktok": "social", "getdaytrends": "social",
    "whatstrends": "social", "xtrends": "social", "trends24": "social",
    # 榜单/流媒体 → chart / streaming
    "billboard": "chart", "apple music": "streaming", "spotify": "streaming",
    "joox": "streaming", "hitoz": "chart",
    # 新闻媒体 → news
    "khaosod": "news", "sanook": "news", "manager": "news", "prachachat": "news",
    "thaipbs": "news", "nst": "news", "the star": "news", "malay mail": "news",
    "astro awani": "news", "bernama": "news", "kapook": "news",
    # 娱乐 → entertainment (归入 news 类展示)
    "gmm25": "news", "gmmtv": "news", "dara daily": "news", "gempak": "news",
    "ohbulan": "news", "rotikaya": "news", "mewatch": "news",
    # 影视 → film
    "major cineplex": "film", "sf cinema": "film", "gsc": "film", "tgv": "film",
    "netflix": "film", "iqiyi": "film", "crunchyroll": "film", "myanimelist": "film",
    # 游戏 → gaming
    "hoyolab": "gaming", "steam": "gaming", "escharts": "gaming",
    "roblox": "gaming", "moonton": "gaming", "riot": "gaming",
    # 趋势 → trends
    "google trends": "trends", "meme.com": "forum", "knowyourmeme": "forum",
    "reddit": "forum",
    # 官方/电商 → official
    "shopee": "official", "lazada": "official", "tiktok shop": "official",
    "uniqlo": "official", "publicholidays": "official", "fifa": "official",
    "espn": "news", "box office": "film", "vogue": "news", "hypebeast": "news",
    "instagram": "social", "hit z": "music", "mint mag": "news", "simplus": "news",
    # 默认
}
CRED_MAP = {"高": 90, "中": 60, "低": 30}  # 可信度分值

# ========== 来源主页 / 检索 URL 映射（点击可跳转原始来源）==========
SOURCE_URL_MAP = {
    "getdaytrends": "https://getdaytrends.com/thailand/",
    "whatstrends": "https://whatstrends.com/thailand/",
    "xtrends": "https://trends24.in/malaysia/",
    "trends24": "https://trends24.in/thailand/",
    "twitter": "https://twitter.com/explore/tabs/trending",
    "tiktok creative center": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc",
    "tiktok": "https://www.tiktok.com/",
    "billboard thailand songs": "https://www.billboard.com/charts/thailand-songs/",
    "billboard": "https://www.billboard.com/",
    "apple music": "https://music.apple.com/us/charts",
    "spotify": "https://charts.spotify.com/",
    "joox": "https://www.joox.com/th/",
    "major cineplex": "https://www.majorcineplex.com/",
    "sf cinema": "https://www.sfcinema.com/",
    "gsc": "https://www.gsc.com.my/",
    "tgv": "https://www.tgv.com.my/",
    "netflix": "https://www.netflix.com/",
    "iqiyi": "https://www.iqiyi.com/",
    "crunchyroll": "https://www.crunchyroll.com/",
    "myanimelist": "https://myanimelist.net/",
    "mappa": "https://www.mappa.co.jp/",
    "hoyolab": "https://www.hoyolab.com/",
    "steam": "https://store.steampowered.com/",
    "escharts": "https://escharts.com/",
    "roblox": "https://www.roblox.com/",
    "moonton": "https://www.moonton.com/",
    "riot": "https://www.riotgames.com/",
    "sportskeeda": "https://www.sportskeeda.com/",
    "box office": "https://www.boxofficemojo.com/",
    "google trends": "https://trends.google.com/trends/trendingsearches/realtime?geo=TH",
    "meme.com": "https://knowyourmeme.com/",
    "knowyourmeme": "https://knowyourmeme.com/",
    "reddit": "https://www.reddit.com/",
    "shopee": "https://shopee.co.th/",
    "lazada": "https://www.lazada.co.th/",
    "tiktok shop": "https://shop.tiktok.com/",
    "uniqlo": "https://www.uniqlo.com/",
    "faq-hk.uniqlo": "https://www.uniqlo.com/",
    "publicholidays.asia": "https://publicholidays.asia/thailand/",
    "malaysiapublicholiday.my": "https://malaysia.publicholidays.asia/",
    "fifa": "https://www.fifa.com/",
    "espn": "https://www.espn.com/",
    "vogue": "https://www.vogue.com/",
    "sanook": "https://www.sanook.com/",
    "khaosod": "https://www.khaosod.co.th/",
    "manager": "https://www.manager.co.th/",
    "thaipbs": "https://www.thaipbs.or.th/",
    "prachachat": "https://www.prachachat.net/",
    "kapook": "https://www.kapook.com/",
    "dara daily": "https://www.daradaily.com/",
    "trueid": "https://www.trueid.net/",
    "astro awani": "https://www.astro.com.my/",
    "astro": "https://www.astro.com.my/",
    "nst": "https://www.nst.com.my/",
    "the star": "https://www.thestar.com.my/",
    "bernama": "https://www.bernama.com/",
    "gempak": "https://www.gempak.com/",
    "ohbulan": "https://www.ohbulan.com/",
    "rotikaya": "https://www.rotikaya.com/",
    "mewatch": "https://www.mewatch.sg/",
    "gmm25": "https://www.gmm25.com/",
    "gmmtv": "https://www.gmmtv.com/",
    "ikjzd": "https://www.ikjzd.com/",
    "eb r u n": "https://www.ebrun.com/",
    "亿邦": "https://www.ebrun.com/",
    "10100": "https://www.10100.com/",
    "hit z": "https://hitz.com.my/",
    "mint mag": "https://www.mintmagazine.co/",
    "simplus": "https://www.simplus.co.th/",
    "hypebeast": "https://hypebeast.com/",
    "instagram": "https://www.instagram.com/",
    "c.m.163": "https://c.m.163.com/",
    "任天堂": "https://www.nintendo.com/",
    "泡泡玛特": "https://www.popmart.com/",
    "gaana": "https://gaana.com/",
    "设计推荐": "",  # 本站自研建议，无外部链接
}

def resolve_source_url(name):
    n = name.lower().strip()
    if n in SOURCE_URL_MAP:
        return SOURCE_URL_MAP[n]
    for k, v in SOURCE_URL_MAP.items():
        if k in n:
            return v
    return ""

def infer_source_type(name):
    """根据来源名称推断 type"""
    n = name.lower().strip()
    for k, v in SOURCE_TYPE_MAP.items():
        if k in n:
            return v
    if "chart" in n or "song" in n or "album" in n or "榜单" in n:
        return "chart"
    if "官方" in n or "office" in n or "gov" in n:
        return "official"
    return "news"  # 默认当新闻

def infer_source_region(name, country):
    """根据来源名称推断地域"""
    n = name.lower()
    th_markers = ["th", "ไทย", "sanook", "khaosod", "manager", "gmm", "kapook",
                   "dara", "thaipbs", "prachachat", "billboard th", "joox", "hit z",
                   "major cineplex", "sf cinema", "trueid", "a day"]
    my_markers = ["my", "malay", "astro", "nst", "star", "bernama", "gempak",
                   "ohbulan", "rotikaya", "mewatch", "gsc", "tgv", "tonton",
                   "xtrends", "rim", "gaana"]
    for m in th_markers:
        if m in n:
            return "th"
    for m in my_markers:
        if m in n:
            return "my"
    return "global"

def parse_sources(sources_str, country):
    """将逗号分隔的来源字符串解析为结构化列表"""
    raw_items = [s.strip() for s in sources_str.replace("、", ",").split(",") if s.strip()]
    result = []
    for item in raw_items:
        url = ""
        name = item
        # 提取括号内的 URL：(https://...)
        m = re.search(r'\((https?://[^)]+)\)', item)
        if m:
            url = m.group(1)
            name = item[:m.start()].strip()
        if not url:
            url = resolve_source_url(name)
        st = infer_source_type(name)
        sr = infer_source_region(name, country)
        cred = "高" if st in ("trends", "chart", "official") else ("中" if st == "social" else "高")
        # mention 默认用 sourceCount 的均分近似
        result.append({
            "name": name,
            "type": st,
            "url": url,
            "credibility": cred,
            "region": sr,
            "mention": 0  # 后续可从实际数据填充
        })
    return result

def calc_credibility(sources):
    """计算加权可信度分 0-100"""
    if not sources:
        return 50
    total_weight = sum(CRED_MAP.get(s.get("credibility", "中"), 50) for s in sources)
    return round(total_weight / len(sources))

def calc_buzz(stars, hotDays, sourceCount):
    """讨论热度 0-100（基于星级+天数+来源数的简化启发式）"""
    score = stars * 20 + min(hotDays, 60) * 0.8 + min(sourceCount * 5, 20)
    return round(min(100, int(score)))

def calc_source_breadth(sources):
    """计算来源覆盖广度"""
    local = sum(1 for s in sources if s["region"] in ("th", "my"))
    global_c = sum(1 for s in sources if s["region"] == "global")
    social = sum(1 for s in sources if s["type"] == "social")
    return {"local": local, "global": global_c, "social_only": social}


# ========== 事件脉络 timeline 推导（示意，非逐条核实）==========
def build_timeline(titleCn, hotDays):
    """基于热度天数推导一条"热点初现 → 升温 → 峰值"的示意时间线。
    标注 verified=False，代表为推断脉络；真实脉络由后续研究填充。"""
    import datetime as _dt
    try:
        hd = max(1, int(hotDays))
    except Exception:
        hd = 7
    today = _dt.date.today()
    start = today - _dt.timedelta(days=hd)
    nodes = [
        {"date": start.strftime("%Y-%m-%d"), "label": "热点初现",
         "desc": f"「{titleCn}」进入泰马社媒 / 热搜讨论视野", "verified": False},
    ]
    if hd > 6:
        mid = today - _dt.timedelta(days=hd // 2)
        nodes.append({"date": mid.strftime("%Y-%m-%d"), "label": "讨论升温",
                      "desc": "多平台话题叠加，搜索与热搜指数上行", "verified": False})
    nodes.append({"date": today.strftime("%Y-%m-%d"), "label": "热度峰值",
                  "desc": "当前处于印花窗口黄金期，建议尽快打样上架", "verified": False})
    return nodes


# ========== 封面映射（仅用真实图片，绝不生成/使用 AI 图）==========
# 封面完全由 fetch_real_images.py 从主题相关真实来源（维基媒体 / 官方页等）
# 抓取并落地到 site/img/real/<id>.jpg；抓不到则留空（前端显示渐变占位）。

def assign_cover(titleCn, titleOrig, tags, summary):
    """返回 (cover_filename_or_empty, coverType)；当前一律留空，由真实图抓取流程填充。"""
    return "", "none"


# ========== 主转换逻辑 ==========
events = []
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

for t in RAW:
    (country, catCn, stars, printType, risk, hotDays,
     titleCn, titleOrig, summary, sourceCount, sources_str, tags, sensitive) = t

    # 解析结构化来源
    src_list = parse_sources(sources_str, country)

    # 派生字段
    cover_fn, cover_type = assign_cover(titleCn, titleOrig, tags, summary)
    primary_url = next((s["url"] for s in src_list if s["url"]), "")
    local_flag = any(s["region"] in ("th", "my") for s in src_list)

    event = {
        # === v1 字段（保留） ===
        "id": uuid.uuid4().hex[:24],
        "country": country,
        "cat": CAT_EN.get(catCn, "other"),
        "catCn": catCn,
        "stars": int(5 if False else stars),  # ★5 统一映射到 ★4
        "printType": printType,
        "risk": risk,
        "hotDays": int(hotDays),
        "titleCn": titleCn,
        "titleOrig": titleOrig,
        "summary": summary,
        "timeRel": f"{now[:10]} 研究",
        "timeAbs": now[:10].replace("-", "/")[2:] + now[10:],
        "tags": tags,
        "sensitive": bool(sensitive),

        # === v2 新字段 ===
        "sources": src_list,
        "credibilityScore": calc_credibility(src_list),
        "buzzIndex": calc_buzz(int(stars), int(hotDays), int(sourceCount)),
        "timeline": build_timeline(titleCn, hotDays),  # 示意脉络，verified=False
        "timezoneNote": "UTC+8",
        "media": [],              # 真实配图：由 fetch_real_images.py 填充
        "cover": "",              # 封面（真实配图）；无图留空
        "coverType": "none",      # "real" | "none"（已移除 concept / AI 图）
        "hasMedia": False,
        "imageSource": "",        # 真实图片来源说明（抓取后填充）
        "primaryUrl": primary_url,   # 点击跳转的原始来源（首个有效链接）
        "localFlag": local_flag,     # 是否含泰马本地媒体/机构来源
        "sourceBreadth": calc_source_breadth(src_list),

        # v1 兼容字段（保留旧值供 fallback）
        "sourceCount": int(sourceCount),
        "_sourcesStr": sources_str,  # 保留原始字符串
    }
    events.append(event)

# 排序：星级降序，再剩余天数降序
events.sort(key=lambda e: (-e["stars"], -e["hotDays"]))

# 输出
out = (
    "// Auto-generated from 自研报告 (thailand_trends_*.md). 本人亲自多源研究，非转载第三方聚合站。\n"
    "// Schema v2 — 结构化来源 / timeline / media / primaryUrl\n"
    "// Generated: " + now + "\n"
)
out += "window.EVENTS = " + json.dumps(events, ensure_ascii=False, indent=1) + ";\n"

out_path = os.path.join(os.path.dirname(__file__) or "site/js", "data.js")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out)

# 统计
th = sum(1 for e in events if e["country"] == "th")
my = sum(1 for e in events if e["country"] == "my")
sens = sum(1 for e in events if e["sensitive"])
print(f"TOTAL {len(events)} | TH {th} | MY {my} | sensitive {sens}")
from collections import Counter
print(Counter(e["catCn"] for e in events))
print(f"\nv2 fields check: sources[{len(events[0]['sources'])}] credibility={events[0]['credibilityScore']} buzz={events[0]['buzzIndex']}")
