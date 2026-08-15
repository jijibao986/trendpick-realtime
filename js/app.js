// 印选 TrendPick v2 — 泰马热点选品雷达 前端逻辑
// Schema v2: sources(结构化) / credibilityScore / buzzIndex / timeline(脉络) / media / primaryUrl / localFlag
(function () {
  let EVENTS = window.EVENTS || [];

  const CATS = [
    { key: "all", cn: "全部", icon: "🌐" },
    { key: "明星八卦", cn: "明星八卦", icon: "🌟" },
    { key: "演唱会综艺", cn: "演唱会综艺", icon: "🎤" },
    { key: "影视剧", cn: "影视剧", icon: "🎬" },
    { key: "游戏电竞", cn: "游戏电竞", icon: "🎮" },
    { key: "网络热梗", cn: "网络热梗", icon: "😂" },
    { key: "其他热搜", cn: "其他热搜", icon: "🔥" },
    { key: "社会民生", cn: "社会民生", icon: "🏘" },
    { key: "体育", cn: "体育", icon: "⚽" },
    { key: "政党选举", cn: "政党选举", icon: "🗳" },
    { key: "电商政策", cn: "电商政策", icon: "📦" },
    { key: "平台热搜", cn: "平台热搜", icon: "🔍" },
  ];
  const CAT_EMOJI = {
    "明星八卦": "🌟", "演唱会综艺": "🎤", "影视剧": "🎬", "游戏电竞": "🎮",
    "网络热梗": "😂", "其他热搜": "🔥", "社会民生": "🏘", "体育": "⚽", "政党选举": "🗳",
    "电商政策": "📦", "平台热搜": "🔍",
  };
  const CAT_GRAD = {
    "明星八卦": "linear-gradient(135deg,#f472b6,#a855f7)",
    "演唱会综艺": "linear-gradient(135deg,#f59e0b,#ef4444)",
    "影视剧": "linear-gradient(135deg,#6366f1,#8b5cf6)",
    "游戏电竞": "linear-gradient(135deg,#10b981,#06b6d4)",
    "网络热梗": "linear-gradient(135deg,#fbbf24,#f97316)",
    "其他热搜": "linear-gradient(135deg,#ef4444,#ec4899)",
    "社会民生": "linear-gradient(135deg,#14b8a6,#0ea5e9)",
    "体育": "linear-gradient(135deg,#22c55e,#16a34a)",
    "政党选举": "linear-gradient(135deg,#64748b,#475569)",
    "电商政策": "linear-gradient(135deg,#0ea5e9,#6366f1)",
    "平台热搜": "linear-gradient(135deg,#8b5cf6,#d946ef)",
  };
  const TYPE_ICON = {
    social: "💬", chart: "📊", streaming: "🎧", news: "📰", film: "🎬",
    gaming: "🎮", trends: "📈", forum: "💡", official: "🏛", music: "🎵",
  };

  const state = {
    country: "all", cat: "all", stars: "all", risk: "all", days: "all",
    sort: "stars", search: "", safe: false, view: "grid", media: false, local: false,
    daily: false,
  };

  // ---------- helpers ----------
  function escapeHtml(s) {
    return (s == null ? "" : String(s)).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function stars(n) {
    let v = Number(n);
    if (!isFinite(v) || v < 0) v = 0;
    if (v > 4) v = 4;
    return "★".repeat(v) + "☆".repeat(4 - v);
  }
  function ptClass(pt) {
    if (pt === "文字款") return "t1";
    if (pt === "图案款") return "t2";
    return "t3";
  }
  function riskClass(r) {
    if (r.startsWith("低")) return "low";
    if (r.startsWith("中")) return "mid";
    if (r.startsWith("高")) return "high";
    return "none";
  }
  function credColor(s) { return s >= 75 ? "#10b981" : s >= 50 ? "#f59e0b" : "#ef4444"; }
  function buzzColor(s) { return s >= 75 ? "#ef4444" : s >= 50 ? "#f59e0b" : "#3b82f6"; }
  function credClass(c) { return c === "高" ? "high" : c === "中" ? "mid" : "low"; }
  function getTypeIcon(t) { return TYPE_ICON[t] || "🔗"; }
  function getRegionFlag(r) { return r === "th" ? "🇹🇭" : r === "my" ? "🇲🇾" : "🌐"; }
  function catGradient(c) { return CAT_GRAD[c] || "linear-gradient(135deg,#94a3b8,#64748b)"; }
  function meter(label, score, color) {
    return `<div class="meter"><span class="meter-l">${label}</span><span class="meter-bar"><i style="width:${score}%;background:${color}"></i></span><span class="meter-v">${score}</span></div>`;
  }

  // ---------- SVG 概念图生成器（替代黑块） ----------
  const CONCEPT_ART = {
    "明星八卦": { bg1:"#f472b6", bg2:"#a855f7", icon:"⭐", pattern:"stars" },
    "演唱会综艺": { bg1:"#f59e0b", bg2:"#ef4444", icon:"🎤", pattern:"wave" },
    "影视剧": { bg1:"#6366f1", bg2:"#8b5cf6", icon:"🎬", pattern:"clapper" },
    "游戏电竞": { bg1:"#10b981", bg2:"#06b6d4", icon:"🎮", pattern:"gamepad" },
    "网络热梗": { bg1:"#fbbf24", bg2:"#f97316", icon:"😂", pattern:"zap" },
    "其他热搜": { bg1:"#ef4444", bg2:"#ec4899", icon:"🔥", pattern:"flame" },
    "社会民生": { bg1:"#14b8a6", bg2:"#0ea5e9", icon:"🏘", pattern:"home" },
    "体育": { bg1:"#22c55e", bg2:"#16a34a", icon:"⚽", pattern:"ball" },
    "政党选举": { bg1:"#64748b", bg2:"#475569", icon:"🗳", pattern:"vote" },
    "电商政策": { bg1:"#0ea5e9", bg2:"#6366f1", icon:"📦", pattern:"box" },
    "平台热搜": { bg1:"#8b5cf6", bg2:"#d946ef", icon:"🔍", pattern:"search" },
  };

  function generateConceptSvg(cat, title) {
    const art = CONCEPT_ART[cat] || CONCEPT_ART["其他热搜"];
    const safeTitle = (title || "").slice(0, 20);
    // SVG pattern backgrounds
    const patterns = {
      stars: `<circle cx="30" cy="30" r="2" fill="rgba(255,255,255,.15)"/><circle cx="70" cy="20" r="3" fill="rgba(255,255,255,.12)"/><circle cx="200" cy="60" r="2.5" fill="rgba(255,255,255,.18)"/><circle cx="260" cy="25" r="2" fill="rgba(255,255,255,.1)"/><circle cx="150" cy="80" r="3" fill="rgba(255,255,255,.14)"/><circle cx="100" cy="45" r="1.5" fill="rgba(255,255,255,.16)"/>`,
      wave: `<path d="M0 90 Q50 60 100 80 T200 75 T300 85 L300 120 L0 120Z" fill="rgba(255,255,255,.08)"/><path d="M0 100 Q60 70 120 90 T240 82 L300 95 L300 120 L0 120Z" fill="rgba(255,255,255,.05)"/>`,
      clapper: `<rect x="230" y="15" width="40" height="8" rx="2" fill="rgba(255,255,255,.12)" transform="rotate(-15 250 19)"/><rect x="220" y="30" width="50" height="35" rx="3" fill="rgba(255,255,255,.08)"/><circle cx="235" cy="48" r="5" fill="rgba(255,255,255,.1)"/>`,
      gamepad: `<rect x="180" y="50" width="60" height="40" rx="8" fill="rgba(255,255,255,.08)"/><circle cx="198" cy="70" r="6" fill="rgba(255,255,255,.1)"/><circle cx="222" cy="70" r="6" fill="rgba(255,255,255,.1)"/><rect x="205" y="58" width="10" height="4" rx="2" fill="rgba(255,255,255,.1)"/>`,
      zap: `<path d="M140 30 L155 55 L145 55 L160 85 L135 55 L148 55 Z" fill="rgba(255,255,255,.12)"/><path d="M200 40 L210 58 L204 58 L215 78 L198 58 L206 58 Z" fill="rgba(255,255,255,.08)"/>`,
      flame: `<path d="M250 90 Q260 60 245 40 Q255 55 265 35 Q258 60 270 90Z" fill="rgba(255,255,255,.12)"/><path d="M40 95 Q48 72 36 56 Q44 68 52 50 Q46 72 56 95Z" fill="rgba(255,255,255,.08)"/>`,
      home: `<path d="M30 75 L50 55 L70 75 L70 95 L30 95Z" fill="rgba(255,255,255,.08)"/><rect x="42" y="78" width="16" height="17" fill="rgba(255,255,255,.05)"/>`,
      ball: `<circle cx="250" cy="55" r="22" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="2"/><path d="M238 45 Q250 55 238 65 Q250 55 262 45 Q250 55 262 65" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="1.5"/>`,
      vote: `<rect x="225" y="40" width="30" height="40" rx="4" fill="rgba(255,255,255,.08)"/><path d="M240 48 L248 58 L232 58Z" fill="rgba(255,255,255,.12)"/>`,
      box: `<rect x="210" y="55" width="50" height="35" rx="4" fill="rgba(255,255,255,.08)"/><path d="M210 68 L260 68" stroke="rgba(255,255,255,.1)" stroke-width="1.5"/><line x1="235" y1="55" x2="235" y2="90" stroke="rgba(255,255,255,.08)" stroke-width="1"/>`,
      search: `<circle cx="250" cy="55" r="16" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="2.5"/><line x1="262" y1="67" x2="275" y2="80" stroke="rgba(255,255,255,.1)" stroke-width="2.5"/>`,
    };
    return `<svg class="concept-svg" viewBox="0 0 300 120" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="cg-${cat.replace(/\s/g,'')}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:${art.bg1}"/>
          <stop offset="100%" style="stop-color:${art.bg2}"/>
        </linearGradient>
      </defs>
      <rect width="300" height="120" rx="10" fill="url(#cg-${cat.replace(/\s/g,'')})"/>
      ${patterns[art.pattern] || patterns.stars}
      <text x="150" y="68" text-anchor="middle" font-size="38" fill="rgba(255,255,255,.9)">${art.icon}</text>
      <text x="150" y="98" text-anchor="middle" font-size="13" font-weight="700" fill="rgba(255,255,255,.85)" letter-spacing="1">${escapeHtml(safeTitle)}</text>
    </svg>`;
  }

  // ---------- 多图支持：为每个事件构建图片列表 ----------
  function getEventImages(e) {
    const imgs = [];
    // 1. 主 cover
    if (e.cover) {
      if (e.coverType === "remote" || /^https?:\/\//.test(e.cover)) {
        imgs.push({ url: e.cover, type: "remote" });
      } else {
        imgs.push({ url: "img/" + e.cover, type: "local" });
      }
    }
    // 2. media 数组中的图片
    if (Array.isArray(e.media)) {
      e.media.forEach(m => {
        if (m && (m.url || m.src || m.image)) {
          const u = m.url || m.src || m.image;
          if (u && !imgs.some(i => i.url === u)) {
            imgs.push({ url: u, type: /^https?:\/\//.test(u) ? "remote" : "local", caption: m.caption || m.alt || "" });
          }
        }
      });
    }
    // 3. 如果完全没有图，生成概念图
    if (imgs.length === 0) {
      imgs.push({ url: generateConceptSvg(e.catCn, e.titleCn), type: "svg", isSvg: true });
    }
    return imgs;
  }

  function buildImgStrip(images, maxShow) {
    maxShow = maxShow || 5;
    if (images.length <= 1) return "";
    const thumbs = images.slice(0, maxShow).map((img, i) =>
      img.isSvg
        ? `<div class="thumb more" onclick="event.stopPropagation();switchGalleryImg(${i})">🖼${images.length}</div>`
        : `<img class="thumb${i===0?' active':''}" src="${escapeHtml(img.url)}" alt="" loading="lazy" onclick="event.stopPropagation();switchGalleryImg(${i})" />`
    ).join("");
    if (images.length > maxShow) {
      thumbs += `<div class="thumb more" onclick="event.stopPropagation()">+${images.length - maxShow}</div>`;
    }
    return `<div class="img-strip">${thumbs}</div>`;
  }

  // 当前弹窗的图片画廊状态
  let _galleryImages = [];
  let _galleryIdx = 0;

  window.switchGalleryImg = function(idx) {
    _galleryIdx = idx;
    const main = document.getElementById("mGalleryMain");
    const dots = document.querySelectorAll(".m-gallery-dot");
    const count = document.getElementById("mGalleryCount");
    if (main && _galleryImages[idx]) {
      const img = _galleryImages[idx];
      if (img.isSvg) {
        main.outerHTML = `<div class="m-gallery-none" id="mGalleryMain" style="--cg:${catGradient(img.catCn || '')}"><span>${CAT_EMOJI[img.catCn] || '🔥'}</span></div>`;
      } else {
        main.outerHTML = `<img class="m-gallery-main" id="mGalleryMain" src="${escapeHtml(img.url)}" onclick="openLightbox('${escapeHtml(img.url)}')" />`;
      }
    }
    dots.forEach((d, i) => d.classList.toggle("active", i === idx));
    if (count) count.textContent = (idx + 1) + "/" + _galleryImages.length;
  };

  window.galleryPrev = function() {
    if (_galleryIdx > 0) switchGalleryImg(_galleryIdx - 1);
  };
  window.galleryNext = function() {
    if (_galleryIdx < _galleryImages.length - 1) switchGalleryImg(_galleryIdx + 1);
  };

  // ---------- init ----------
  function init() {
    const cc = document.getElementById("catChips");
    cc.innerHTML = CATS.map((c) =>
      `<button class="chip ${c.key === "all" ? "active" : ""}" data-cat="${c.key}">${c.icon} ${c.cn}</button>`
    ).join("");
    cc.querySelectorAll(".chip").forEach((b) =>
      b.addEventListener("click", () => {
        cc.querySelectorAll(".chip").forEach((x) => x.classList.remove("active"));
        b.classList.add("active"); state.cat = b.dataset.cat; render();
      }));

    document.querySelectorAll("#countryTabs .ctab").forEach((b) =>
      b.addEventListener("click", () => {
        document.querySelectorAll("#countryTabs .ctab").forEach((x) => x.classList.remove("active"));
        b.classList.add("active"); state.country = b.dataset.c; render();
      }));

    document.querySelectorAll("#viewToggle .vbtn").forEach((b) =>
      b.addEventListener("click", () => {
        document.querySelectorAll("#viewToggle .vbtn").forEach((x) => x.classList.remove("active"));
        b.classList.add("active"); state.view = b.dataset.v;
        document.getElementById("gridView").style.display = state.view === "grid" ? "grid" : "none";
        document.getElementById("timelineView").style.display = state.view === "timeline" ? "block" : "none";
        render();
      }));

    document.querySelectorAll(".fbtn").forEach((b) =>
      b.addEventListener("click", () => {
        const f = b.dataset.f;
        document.querySelectorAll(`.fbtn[data-f="${f}"]`).forEach((x) => x.classList.remove("active"));
        b.classList.add("active"); state[f] = b.dataset.v; render();
      }));

    document.getElementById("searchInput").addEventListener("input", (e) => {
      state.search = e.target.value.trim().toLowerCase(); render();
    });
    document.getElementById("mediaToggle").addEventListener("change", (e) => { state.media = e.target.checked; render(); });
    document.getElementById("localToggle").addEventListener("change", (e) => { state.local = e.target.checked; render(); });

    const dt = document.getElementById("dailyToggle");
    if (dt) dt.addEventListener("click", () => {
      state.daily = !state.daily;
      dt.classList.toggle("active", state.daily);
      render();
    });

    renderHeroStats();
    render();
  }

  // ---------- filtering ----------
  function todayBatch() {
    const u = window.SITE_UPDATED || "";
    const d = u.slice(0, 10);
    return d ? "daily-" + d : "";
  }
  function filtered() {
    return EVENTS.filter((e) => {
      if (state.country !== "all" && e.country !== state.country) return false;
      if (state.cat !== "all" && e.catCn !== state.cat) return false;
      if (state.stars !== "all" && e.stars < Number(state.stars)) return false;
      if (state.risk !== "all" && !e.risk.startsWith(state.risk)) return false;
      if (state.days !== "all" && e.hotDays > Number(state.days)) return false;
      if (state.media && !e.hasMedia) return false;
      if (state.local && !e.localFlag) return false;
      if (state.daily && e.batch !== todayBatch()) return false;
      if (state.search) {
        const hay = (e.titleCn + " " + e.titleOrig + " " + e.summary + " " + e.tags.join(" ")).toLowerCase();
        if (!hay.includes(state.search)) return false;
      }
      return true;
    });
  }
  function sortFn(a, b) {
    if (state.sort === "stars") return b.stars - a.stars || b.hotDays - a.hotDays;
    if (state.sort === "hot") return b.hotDays - a.hotDays || b.stars - a.stars;
    if (state.sort === "buzz") return b.buzzIndex - a.buzzIndex || b.stars - a.stars;
    if (state.sort === "new") return (b.timeAbs || "").localeCompare(a.timeAbs || "");
    return 0;
  }

  // ---------- render ----------
  function render() {
    const list = filtered().sort(sortFn);
    document.getElementById("resultCount").textContent = `共 ${list.length} 条热点`;
    const dt = document.getElementById("dailyToggle");
    if (dt) { const dn = EVENTS.filter((e) => e.batch === todayBatch()).length; dt.textContent = "🔥 今日日报(" + dn + ")"; }
    document.getElementById("statMedia").textContent = list.filter((e) => e.hasMedia).length;
    document.getElementById("statLocal").textContent = list.filter((e) => e.localFlag).length;
    if (state.view === "grid") renderGrid(list);
    else renderTimeline(list);
  }

  // ---------- 前端 IP 硬编码兜底（知名游戏/艺人/动漫 永不黑块）----------
  const FE_FALLBACK = {
    // 游戏
    "genshin": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5d/Genshin_Impact_logo.svg/960px-Genshin_Impact_logo.svg.png",
    "原神": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5d/Genshin_Impact_logo.svg/960px-Genshin_Impact_logo.svg.png",
    "black myth wukong": "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/Black_Myth_Wukong_cover_art.jpg/800px-Black_Myth_Wukong_cover_art.jpg",
    "黑神话": "https://upload.wikimedia.org/wikipedia/en/thumb/8/87/Black_Myth_Wukong_cover_art.jpg/800px-Black_Myth_Wukong_cover_art.jpg",
    "honkai star rail": "https://upload.wikimedia.org/wikipedia/en/thumb/f/fd/Honkai_Star_Rail_logo.png/800px-Honkai_Star_Rail_logo.png",
    "崩坏": "https://upload.wikimedia.org/wikipedia/en/thumb/f/fd/Honkai_Star_Rail_logo.png/800px-Honkai_Star_Rail_logo.png",
    "roblox": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Roblox_logo_2022.svg/800px-Roblox_logo_2022.svg.png",
    "minecraft": "https://upload.wikimedia.org/wikipedia/en/thumb/6/60/Minecraft_logo.svg/800px-Minecraft_logo.svg.png",
    "我的世界": "https://upload.wikimedia.org/wikipedia/en/thumb/6/60/Minecraft_logo.svg/800px-Minecraft_logo.svg.png",
    "league of legends": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b3/League_of_Legends_2019_vector_logo.svg/800px-League_of_Legends_2019_vector_logo.svg.png",
    "英雄联盟": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b3/League_of_Legends_2019_vector_logo.svg/800px-League_of_Legends_2019_vector_logo.svg.png",
    "pubg": "https://upload.wikimedia.org/wikipedia/en/thumb/2/26/PlayerUnknown%27s_Battlegrounds_logo.svg/800px-PlayerUnknown%27s_Battlegrounds_logo.svg.png",
    "apex legends": "https://upload.wikimedia.org/wikipedia/en/thumb/e/ec/Apex_Legends_logo.svg/800px-Apex_Legends_logo.svg.png",
    "dota 2": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d9/Dota_2_logo.svg/800px-Dota_2_logo.svg.png",
    "valorant": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Valorant_logo_-_color.svg/800px-Valorant_logo_-_color.svg.png",
    "gta v": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/Grand_Theft_Auto_V.png/800px-Grand_Theft_Auto_V.png",
    "gta5": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a5/Grand_Theft_Auto_V.png/800px-Grand_Theft_Auto_V.png",
    // K-Pop / 国际艺人
    "blackpink": "https://upload.wikimedia.org/wikipedia/en/thumb/1/1b/BLACKPINK_2019_photo.png/800px-BLACKPINK_2019_photo.png",
    "bts": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/BTS_for_%EB%9D%BC%EB%B8%8C%ED%94%84%EC%96%B4%ED%8A%B8%EC%A6%88_in_2019.png/800px-BTS_for_%EB%9D%BC%EB%B8%8C%ED%94%84%EC%96%B4%ED%8A%B8%EC%A6%88_in_2019.png",
    "newjeans": "https://upload.wikimedia.org/wikipedia/en/thumb/8/82/NewJeans_%282023%29.png/800px-NewJeans_%282023%29.png",
    "ive": "https://upload.wikimedia.org/wikipedia/en/thumb/5/54/IVE_%282023%29.png/800px-IVE_%282023%29.png",
    "taylor swift": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cd/Taylor_Swift_%28The_Eras_Tour%29.png/800px-Taylor_Swift_%28The_Eras_Tour%29.png",
    // 动漫
    "jujutsu kaisen": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Jujutsu_Kaisen_logo.png/800px-Jujutsu_Kaisen_logo.png",
    "咒术回战": "https://upload.wikimedia.org/wikipedia/en/thumb/a/a7/Jujutsu_Kaisen_logo.png/800px-Jujutsu_Kaisen_logo.png",
    "demon slayer": "https://upload.wikimedia.org/wikipedia/en/thumb/7/77/Demon_Slayer_Kimetsu_no_Yaiba_logo.png/800px-Demon_Slayer_Kimetsu_no_Yaiba_logo.png",
    "鬼灭之刃": "https://upload.wikimedia.org/wikipedia/en/thumb/7/77/Demon_Slayer_Kimetsu_no_Yaiba_logo.png/800px-Demon_Slayer_Kimetsu_no_Yaiba_logo.png",
    "attack on titan": "https://upload.wikimedia.org/wikipedia/en/thumb/2/29/Attack_on_Titan_logo.png/800px-Attack_on_Titan_logo.png",
    "one piece": "https://upload.wikimedia.org/wikipedia/en/thumb/8/86/One_Piece_Logo.png/800px-One_Piece_Logo.png",
    "海贼王": "https://upload.wikimedia.org/wikipedia/en/thumb/8/86/One_Piece_Logo.png/800px-One_Piece_Logo.png",
    "naruto": "https://upload.wikimedia.org/wikipedia/en/thumb/7/75/Naruto_logo.png/800px-Naruto_logo.png",
    "火影忍者": "https://upload.wikimedia.org/wikipedia/en/thumb/7/75/Naruto_logo.png/800px-Naruto_logo.png",
    "dragon ball": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Dragon_Ball_logo.svg/800px-Dragon_Ball_logo.svg.png",
    "龙珠": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9f/Dragon_Ball_logo.svg/800px-Dragon_Ball_logo.svg.png",
    "spy x family": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Spy_x_Family_logo.png/800px-Spy_x_Family_logo.png",
    "间谍过家家": "https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Spy_x_Family_logo.png/800px-Spy_x_Family_logo.png",
    "chainsaw man": "https://upload.wikimedia.org/wikipedia/en/thumb/3/39/Chainsaw_Man_logo.png/800px-Chainsaw_Man_logo.png",
    "电锯人": "https://upload.wikimedia.org/wikipedia/en/thumb/3/39/Chainsaw_Man_logo.png/800px-Chainsaw_Man_logo.png",
    // 泰国 BL / GMMTV
    "gmmtv": "https://upload.wikimedia.org/wikipedia/en/thumb/e/e0/GMMTV_logo.svg/800px-GMMTV_logo.svg.png",
    "lingorm": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Ling_Orm_at_GMMTV_2024.jpg/800px-Ling_Orm_at_GMMTV_2024.jpg",
  };

  function feFallbackImg(e) {
    const combined = ((e.titleOrig || "") + " " + (e.titleCn || "")).toLowerCase();
    for (const [kw, url] of Object.entries(FE_FALLBACK)) {
      if (combined.includes(kw)) return { url, src: "前端IP兜底(" + kw + ")" };
    }
    return null;
  }

  function coverHtml(e) {
    const local = e.localFlag ? '<span class="local-badge">🇹🇭🇲🇾 本地</span>' : "";
    const isRemote = e.coverType === "remote" || (e.cover && /^https?:\/\//.test(e.cover));
    const images = getEventImages(e);

    if (e.cover && isRemote) {
      // 有远程主图 + 可能多图
      return `<div class="cover ${e.coverType}" data-cat="${escapeHtml(e.catCn)}" data-title="${escapeHtml(e.titleCn)}">
        <img class="rt-img" src="${escapeHtml(e.cover)}" alt="${escapeHtml(e.titleCn)}" loading="lazy" onclick="event.stopPropagation();openLightbox('${escapeHtml(e.cover)}')" />
        <div class="rt-ph" style="--cg:${catGradient(e.catCn)};display:none"><span class="ph-emoji">${CAT_EMOJI[e.catCn] || "🔥"}</span></div>
        ${buildImgStrip(images)}
        <span class="cover-badge ${e.coverType}">远程配图${images.length>1?' · '+images.length+'张':''}</span>${local}
      </div>`;
    }
    if (e.cover) {
      // 本地图片（带降级）
      return `<div class="cover ${e.coverType}" data-cat="${escapeHtml(e.catCn)}" data-title="${escapeHtml(e.titleCn)}">
        <img src="img/${escapeHtml(e.cover)}" alt="${escapeHtml(e.titleCn)}" loading="lazy" onclick="event.stopPropagation();openLightbox('img/${escapeHtml(e.cover)}')" />
        <div class="rt-ph" style="--cg:${catGradient(e.catCn)};display:none"><span class="ph-emoji">${CAT_EMOJI[e.catCn] || "🔥"}</span></div>
        ${buildImgStrip(images)}
        <span class="cover-badge ${e.coverType}">真实配图${images.length>1?' · '+images.length+'张':''}</span>${local}
      </div>`;
    }
    // 无图 → 先检查前端 IP 硬编码兜底 → 再用 SVG 概念图
    const fb = feFallbackImg(e);
    if (fb) {
      return `<div class="cover remote" data-cat="${escapeHtml(e.catCn)}" data-title="${escapeHtml(e.titleCn)}">
        <img class="rt-img" src="${escapeHtml(fb.url)}" alt="${escapeHtml(e.titleCn)}" loading="lazy" onclick="event.stopPropagation();openLightbox('${escapeHtml(fb.url)}')" />
        <div class="rt-ph" style="--cg:${catGradient(e.catCn)};display:none"><span class="ph-emoji">${CAT_EMOJI[e.catCn] || "🔥"}</span></div>
        <span class="cover-badge remote">前端兜底${local}</span>
      </div>`;
    }
    return `<div class="cover none concept" style="--cg:${catGradient(e.catCn)}">
      ${generateConceptSvg(e.catCn, e.titleCn)}
      <span class="cover-badge none">AI概念图</span>${local}
    </div>`;
  }

  function renderGrid(list) {
    const g = document.getElementById("gridView");
    if (!list.length) {
      g.innerHTML = `<div style="grid-column:1/-1;padding:40px;text-align:center;color:#9aa1ac">没有匹配的热点，试试放宽筛选条件 🔍</div>`;
      return;
    }
    g.innerHTML = list.map((e) => `
      <div class="card" onclick="openModal('${e.id}')">
        ${e.fresh ? '<div class="fresh-flag">🔥 今日日报</div>' : ""}
        ${coverHtml(e)}
        <div class="card-body">
          <div class="card-top">
            <span class="cat-tag">${e.catCn}</span>
            <span class="stars">${stars(e.stars)}</span>
          </div>
          <h3>${escapeHtml(e.titleCn)}</h3>
          <div class="title-orig">${escapeHtml(e.titleOrig)}</div>
          <div class="summary">${escapeHtml(e.summary)}</div>
          <div class="card-foot">
            <span class="pt ${ptClass(e.printType)}">${e.printType}</span>
            <span class="risk ${riskClass(e.risk)}">${e.risk}</span>
            <span class="meta">还热 ${e.hotDays}天</span>
          </div>
          <div class="card-meters">
            ${meter("可信", e.credibilityScore, credColor(e.credibilityScore))}
            ${meter("热度", e.buzzIndex, buzzColor(e.buzzIndex))}
          </div>
          <div class="card-src">📡 ${e.sources.length} 来源 · 本地 ${e.sourceBreadth.local} / 全球 ${e.sourceBreadth.global}</div>
        </div>
      </div>`).join("");
  }

  function renderTimeline(list) {
    const t = document.getElementById("timelineView");
    const groups = {};
    list.forEach((e) => { (groups[e.catCn] = groups[e.catCn] || []).push(e); });
    const cats = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);
    if (!cats.length) { t.innerHTML = `<div style="padding:40px;text-align:center;color:#9aa1ac">没有匹配的热点</div>`; return; }
    t.innerHTML = cats.map((c) => `
      <div class="tl-day">
        <div class="tl-date">${CAT_EMOJI[c] || "🔥"} ${c} <span style="color:#9aa1ac;font-weight:500;font-size:13px">（${groups[c].length} 条）</span></div>
        <div class="tl-items">
          ${groups[c].map((e) => `
            <div class="card" onclick="openModal('${e.id}')">
              ${e.fresh ? '<div class="fresh-flag">🔥 今日日报</div>' : ""}
              <div class="card-top"><span class="cat-tag">${e.catCn}</span><span class="stars">${stars(e.stars)}</span></div>
              <h3>${escapeHtml(e.titleCn)}</h3>
              <div class="card-foot">
                <span class="pt ${ptClass(e.printType)}">${e.printType}</span>
                <span class="risk ${riskClass(e.risk)}">${e.risk}</span>
                <span class="meta">还热 ${e.hotDays}天</span>
              </div>
            </div>`).join("")}
        </div>
      </div>`).join("");
  }

  function renderHeroStats() {
    const th = EVENTS.filter((e) => e.country === "th").length;
    const my = EVENTS.filter((e) => e.country === "my").length;
    const top = EVENTS.filter((e) => e.stars >= 4).length;
    const media = EVENTS.filter((e) => e.hasMedia).length;
    const local = EVENTS.filter((e) => e.localFlag).length;
    const html = [
      { num: EVENTS.length, lbl: "热点总数" },
      { num: th, lbl: "🇹🇭 泰国" },
      { num: my, lbl: "🇲🇾 马来西亚" },
      { num: top, lbl: "★4 爆款候选" },
      { num: media, lbl: "🖼 含配图" },
      { num: local, lbl: "🇹🇭🇲🇾 本地媒体" },
    ].map((s) => `<div class="stat"><div class="num">${s.num}</div><div class="lbl">${s.lbl}</div></div>`).join("");
    document.getElementById("heroStats").innerHTML = html;
  }

  // ---------- 印花关键词分析引擎 ----------
  function keywordAnalysis(e) {
    const t = (e.titleCn || "") + " " + (e.titleOrig || "") + " " + (e.summary || "") + " " + (e.tags.join(" "));
    const cat = e.catCn || "其他热搜";
    const country = e.country || "multi";
    const isTh = country === "th";
    const isMy = country === "my";

    // 1️⃣ 提取核心关键词（去重、过滤停用词）
    const stopWords = new Set(["的","了","在","是","我","有","和","就","不","人","都","一","一个","上","也","很","到","说","要","去","你","会","着","没有","看","好","自己","这","他","她","它","们","那","被","从","把","对","与","而","但","或","及","等","之","用","可以","这个","那个","什么","如何","为什么","因为","所以","如果","the","a","an","is","are","was","were","be","been","being","have","has","had","do","does","did","will","would","could","should","may","might","must","shall","can","this","that","these","those","with","from","for","about","into","through","during","before","after","above","below","between","under","again","further","then","once","here","there","when","where","why","how","all","each","few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","just","และ","ที่","มี","เป็น","การ","นั้น","นี้","ได้","จะ","แต่","หรือ","ไม่","ใน","จาก","เพื่อ","สำหรับ","dan","yang","ada","pada","dengan","untuk","dari","ini","itu","atau","bukan","dalam"]);
    const words = [...new Set(t.toLowerCase().split(/[\s,，.。!！?？:：;；""''【】\[\]（）()\/\/\\|｜\-—_]+/).filter(w => w.length > 1 && !stopWords.has(w)))].slice(0, 15);

    // 2️⃣ 推荐印花文案（基于分类智能生成）
    const slogans = generateSlogans(e, cat, isTh, isMy);

    // 3️⃣ 图案元素推荐
    const elements = generateElements(e, cat);

    // 4️⃣ 色彩风格
    const colors = generateColors(e, cat, e.stars);

    // 5️⃣ 目标客群
    const audience = generateAudience(e, cat, country);

    // 6️⃣ 定价区间
    const pricing = generatePricing(e, e.stars, e.printType);

    // 7️⃣ 搜索/SEO 关键词
    const seoKw = generateSeoKw(words, e, cat, isTh, isMy);

    // 8️⃣ 类似爆款方向
    const similarTrends = generateSimilarTrends(cat, country);

    return { slogans, elements, colors, audience, pricing, seoKw, similarTrends, rawWords: words.slice(0, 10) };
  }

  function generateSlogans(e, cat, isTh, isMy) {
    const title = e.titleCn || "";
    const orig = e.titleOrig || "";
    // 截取安全长度
    const short = (s) => (s || "").slice(0, 14);
    const shortO = (s) => (s || "").slice(0, 12);

    // ── 泰国专属：真泰文 + 中文翻译 ──
    const thSlogans = {
      "明星八卦": [
        { cn: `${title} · 粉丝团专属`, th: `${short(title)} Fan Club เฉพาะ` },
        { cn: `${shortO(orig)} 官方周边`, th: `${shortO(orig)} Official Merch` },
        { cn: `追星必备 · ${short(title)}`, th: `ของแท้! ${short(title)} ต้องมี` },
        { cn: `偶像同款T恤`, th: `เสื้อยืดไอดอลเดียวกัน` },
      ],
      "演唱会综艺": [
        { cn: `${title} 巡演2026`, th: `${short(title)} TOUR 2026` },
        { cn: `我去过现场！`, th: `เคยดูจริง! ${shortO(title)}` },
        { cn: `${title} · 限量巡演款`, th: `${short(title)} Limited Edition` },
        { cn: `演唱会纪念款`, th: `Concert Memorial Tee` },
      ],
      "影视剧": [
        { cn: `"${short(e.summary || "")}"`, th: `"${shortO(orig)}" Quote Art` },
        { cn: `${title} · 剧迷认证`, th: `${short(title)} Series Lover` },
        { cn: `角色名印花 / 经典台词`, th: `Character Name · บทพูดคลาสสิก` },
      ],
      "游戏电竞": [
        { cn: `${title} · 职业玩家`, th: `${short(title)} PRO PLAYER 🎮` },
        { cn: `段位升级！`, th: `RANK UP! ${shortO(title)}` },
        { cn: `${title} · 皮肤/装备印花`, th: `${short(title)} Skin Collection` },
        { cn: `GG 赢了！`, th: `GG WP! Victory Royale 🏆` },
      ],
      "网络热梗": [
        { cn: `${title} · 病毒式传播`, th: `${short(title)} 🔥 ไวรัล` },
        { cn: `梗图文字直接印花`, th: `Meme Template T-Shirt` },
        { cn: `${title} · 懂的都懂`, th: `${short(title)} Inside Joke 😂` },
      ],
      "音乐榜单": [
        { cn: `${title} · 今日神曲`, th: `${short(title)} Hit Song Of The Day 🎵` },
        { cn: `单曲循环中...`, th: `On Repeat... ${shortO(title)}` },
        { cn: `${title} · 音乐节款`, th: `${short(title)} Festival Vibe` },
      ],
      "平台热搜": [
        { cn: `${title} · 全网热搜`, th: `${short(title)} Trending #1 🔥` },
        { cn: `热搜话题印花`, th: `Hot Topic Print` },
        { cn: `${title} · 大家都在搜`, th: `${short(title)} Everyone Searching` },
      ],
      "动漫热度": [
        { cn: `${title} · 动漫迷必备`, th: `${short(title)} Anime Fan Must Have` },
        { cn: `二次元印花`, th: `2D Anime Style Art` },
        { cn: `${title} · 角色立绘`, th: `${short(title)} Character Art` },
      ],
      "游戏热度": [
        { cn: `${title} · 游戏达人`, th: `${short(title)} Gamer Level Up ⬆️` },
        { cn: `Steam热门同款`, th: `Steam Top Seller Tee` },
        { cn: `${title} · 开黑必备`, th: `${short(title)} Squad Game On` },
      ],
    };

    // ── 马来西亚专属：真马来文 + 中文翻译 ──
    const mySlogans = {
      "明星八卦": [
        { cn: `${title} · 粉丝团专属`, my: `${short(title)} Fan Club Exclusive` },
        { cn: `${shortO(orig)} 官方正品`, my: `${shortO(orig)} Original Authentik` },
        { cn: `追星必备 · ${short(title)}`, my: `Wajib Ada! ${short(title)} Fan` },
        { cn: `偶像同款T恤`, my: `T-Shirt Idola Sama` },
      ],
      "演唱会综艺": [
        { cn: `${title} 巡演2026`, my: `${short(title)} Tour 2026 KL` },
        { cn: `我在现场！`, my: `Saya Ada Di Sana! Live` },
        { cn: `${title} · 限量版`, my: `${short(title)} Edisi Terhad` },
        { cn: `演唱会纪念`, my: `Konsert Memorial` },
      ],
      "影视剧": [
        { cn: `"${short(e.summary || "")}"`, my: `"${shortO(orig)}" Petikan Klasik` },
        { cn: `${title} · 剧迷认证`, my: (short(title) || "") + " Peminat Drama" },
        { cn: `角色名 / 经典台词`, my: `Nama Watak · Dialog Ikonik` },
      ],
      "游戏电竞": [
        { cn: `${title} · 电竞达人`, my: `${short(title)} GG WP Pro` },
        { cn: `上分成功！`, my: `Rank Up! Menang Terus 🏆` },
        { cn: `${title} · 装备/皮肤`, my: `${short(title)} Gear & Skin` },
        { cn: `赢了兄弟！`, my: `BOOYAH! Menang Bossku` },
      ],
      "网络热梗": [
        { cn: `${title} · 爆红中`, my: `${short(title)} Viral Terkini 🔥` },
        { cn: `梗图直接印`, my: `Meme Template Shirt` },
        { cn: `${title} · 你懂的`, my: `${short(title)} Faham Lah 😂` },
      ],
      "音乐榜单": [
        { cn: `${title} · 今日金曲`, my: `${short(title)} Lagu Hits Hari Ini 🎵` },
        { cn: `单曲循环...`, my: `On Repeat... ${shortO(title)}` },
        { cn: `${title} · 音乐节款`, my: `${short(title)} Festival Vibes` },
      ],
      "平台热搜": [
        { cn: `${title} · 全网热搜`, my: `${short(title)} Trending #1 🔥` },
        { cn: `热搜话题款`, my: `Hot Topic Print` },
        { cn: `${title} · 人气搜索`, my: `${short(title)} Carian Popular` },
      ],
      "动漫热度": [
        { cn: `${title} · 动漫迷必入`, my: `${short(title)} Anime Fan Wajib` },
        { cn: `二次元风格`, my: `Gaya Anime 2D` },
        { cn: `${title} · 角色设计`, my: `${short(title)} Character Design` },
      ],
      "游戏热度": [
        { cn: `${title} · 游戏高手`, my: `${short(title)} Gamer Pro ⬆️` },
        { cn: `Steam热销同款`, my: `Steam Best Seller Tee` },
        { cn: `${title} · 组队开黑`, my: `${short(title)} Team Squad` },
      ],
    };

    // ── 多市场/其他：中英双语 ──
    const multiSlogans = {
      "明星八卦": [
        { cn: `${title} · FAN CLUB`, th: `${short(title)} Fan Club`, my: `${short(title)} Squad` },
        { cn: `Official Merch`, th: `${shortO(orig)} Official`, my: `${shortO(orig)} Original` },
        { cn: `追星必备`, th: `Must Have!`, my: `Wajib Punya!` },
      ],
      "演唱会综艺": [
        { cn: `${title} TOUR 2026`, th: `LIVE in TH`, my: `KL Stop` },
        { cn: `I WAS THERE`, th: `เคยดูแล้ว`, my: `Saya Ada Di Sana` },
        { cn: `限量巡演款`, th: `Limited Edition`, my: `Edisi Terhad` },
      ],
      "影视剧": [
        { cn: `"${short(e.summary || "")}"`, th: `Quote Art`, my: `Petikan Klasik` },
        { cn: `${title} · 剧粉认证`, th: `Fan Club`, my: `Lovers` },
        { cn: `角色名印花`, th: `Character Name`, my: `Nama Watak` },
      ],
      "游戏电竞": [
        { cn: `${title} · GAMER`, th: `PRO PLAYER`, my: `GG WP` },
        { cn: `RANK UP!`, th: `Victory Royale`, my: `BOOYAH!` },
        { cn: `${title} · 皮肤印花`, th: `Skin Collection`, my: `Gear Up!` },
      ],
      "网络热梗": [
        { cn: `${title} · VIRAL`, th: `🔥 Trending`, my: `Viral Terkini` },
        { cn: `梗图印花`, th: `Meme Template`, my: `Meme Shirt` },
        { cn: `${title} · 懂的都懂`, th: `Inside Joke`, my: `Faham Lah` },
      ],
      "音乐榜单": [
        { cn: `${title} · 热门单曲`, th: `Hit Song 🎵`, my: `Lagu Hits` },
        { cn: `循环播放中`, th: `On Repeat`, my: `Main Bergilir` },
        { cn: `${title} · 音乐节`, th: `Festival`, my: `Festival Vibes` },
      ],
      "平台热搜": [
        { cn: `${title} · 热搜爆款`, th: `Trending 🔥`, my: `Viral 🔥` },
        { cn: `热搜关键词`, th: `Hot Topic`, my: `Topik Panas` },
        { cn: `${title} · 全网关注`, th: `Everyone Watching`, my: `Semua Tengok` },
      ],
      "动漫热度": [
        { cn: `${title} · 动漫爆款`, th: `Anime Hot`, my: `Anime Viral` },
        { cn: `二次元必备`, th: `2D Style`, my: `Gaya Anime` },
        { cn: `${title} · 角色款`, th: `Character Art`, my: `Design Watak` },
      ],
      "游戏热度": [
        { cn: `${title} · 游戏热榜`, th: `Gaming Top`, my: `Game Popular` },
        { cn: `Steam热销`, th: `Steam Hit`, my: `Steam Best` },
        { cn: `${title} · 开黑款`, th: `Squad Game`, my: `Team Game` },
      ],
    };

    // 根据国家选择词库
    let base;
    if (isTh) {
      base = thSlogans[cat] || thSlogans["平台热搜"];
    } else if (isMy) {
      base = mySlogans[cat] || mySlogans["平台热搜"];
    } else {
      base = multiSlogans[cat] || multiSlogans["平台热搜"];
    }

    return base;
  }

  function generateElements(e, cat) {
    const elMap = {
      "明星八卦": ["人物剪影/侧脸轮廓", "名字艺术字设计", "生日年份数字", "星座符号", "粉丝团Logo元素", "签名风格字体"],
      "演唱会综艺": ["舞台灯光效果", "Tour日期城市列表", "麦克风/乐器图标", "门票票根设计", "乐队/歌手Logo", "霓虹灯管风格"],
      "影视剧": ["经典台词字幕框", "角色Q版形象", "电影胶片边框", "剧名艺术字+副标题", "场景剪影（地标/道具）", "上映日期纪念"],
      "游戏电竞": ["游戏角色立绘/像素风", "装备/武器图标", "段位徽章设计", "战队Logo+ID", "操作按键布局(WASD)", "胜利/升级特效字"],
      "网络热梗": ["表情包主角形象", "梗图文字排版", "对比图/meme模板", "emoji大字报组合", "对话气泡框", "极简文字冲击"],
      "体育": ["球衣号码+名字", "冠军奖杯图案", "运动剪影动态线", "球队配色条纹", "比分牌设计", "体育场轮廓"],
      "其他热搜": ["事件关键词云", "时间节点数字", "地点轮廓/地图元素", "报纸头条排版", "极简信息图", "话题标签#hashtag"],
    };
    return elMap[cat] || elMap["其他热搜"];
  }

  function generateColors(e, cat, stars) {
    const highStars = stars >= 3;
    const colorPalettes = {
      "明星八卦": { name: "星光渐变系", colors: ["#FF6B9D → #C44569", "#E84393 → #6C5CE7", "#FD79A8 → #FDCB6E"], desc: "粉紫渐变为主，符合粉丝经济调性" },
      "演唱会综艺": { name: "霓虹舞台系", colors: ["#00D2FF → #3A7BD5", "#F7DF1E → #FF6B6B", "#A29BFE → #6C5CE7"], desc: "高饱和霓虹色，模拟舞台灯光感" },
      "影视剧": { name: "电影质感系", colors: ["#2D3436 → #636E72", "#DFE6E9 → #B2BEC3", "#6C5CE7 → #0984E3"], desc: "深色调+金属质感，高级感强" },
      "游戏电竞": { name: "RGB电竞系", colors: ["#00FF00 → #00FFFF", "#FF0040 → #800080", "#FFD700 → #FF4500"], desc: "RGB高对比度，赛博朋克风" },
      "网络热梗": { name: "高对比撞色", colors: ["#000000 → #FFFFFF", "#FF4500 → #FFD700", "#00FFFF → #FF00FF"], desc: "黑白或强烈撞色，视觉冲击力max" },
      "体育": { name: "运动活力系", colors: ["#27AE60 → #2ECC71", "#E74C3C → #C0392B", "#3498DB → #2980B9"], desc: "队服配色+活力绿/红/蓝" },
    };
    const pal = colorPalettes[cat] || { name: "百搭潮流系", colors: ["#2D3436 → #636E72", "#E17055 → #FDCB6E", "#00B894 → #00CEC9"], desc: "中性色+点缀色，适配多场景" };
    if (highStars) pal.desc += " ⭐ 高潜力爆款建议加大首版备货";
    return pal;
  }

  function generateAudience(e, cat, country) {
    const audMap = {
      "明星八卦": { primary: "18-30岁女性粉丝", secondary: "追星族/偶像团体粉丝", th: "泰国K-pop/BLKpop粉丝圈", my: "马来西亚韩流/泰流粉丝" },
      "演唱会综艺": { primary: "16-35岁音乐爱好者", secondary: "现场观众/巡演收藏者", th: "泰国Concert常客/KKBox用户", my: "大马演唱会人群/Spotify MY" },
      "影视剧": { primary: "18-40岁剧迷", secondary: "Netflix/Disney+订阅用户", th: "泰国Netflix用户/剧集讨论区", my: "马来西亚Viu/WeTV用户" },
      "游戏电竞": { primary: "16-28岁男性玩家", secondary: "Steam/Mobile Gamer", th: "泰国Steam/Garena玩家", my: "马来西亚Mobile Legends/PUBG玩家" },
      "网络热梗": { primary: "15-30岁Z世代", secondary: "TikTok/Twitter重度用户", th: "泰国Twitter/TikTok网民", my: "马来西亚TikTok/IG用户" },
      "体育": { primary: "18-45岁体育迷", secondary: "球迷/健身人群", th: "泰国足球迷/拳击迷", my: "马来西亚足球/羽球爱好者" },
    };
    return audMap[cat] || audMap["其他热搜"];
  }

  function generatePricing(e, stars, pt) {
    if (stars >= 4) {
      return { range: "฿199-499 / RM25-65", cost: "印花成本￥3-8", suggest: "★4爆款候选 — 首批建议50-100件测试，可设阶梯价" };
    } else if (stars >= 3) {
      return { range: "฿149-349 / RM18-45", cost: "印花成本￥2-5", suggest: "★3潜力款 — 小批量30件起测，关注转化率" };
    } else {
      return { range: "฿99-249 / RM12-32", cost: "印花成本￥1-3", suggest: "低星测试款 — 按需生产/POD模式，控制库存风险" };
    }
  }

  function generateSeoKw(words, e, cat, isTh, isMy) {
    const kw = [...words];
    // 按国家返回对应语言的SEO关键词（含本地语言+中文）
    if (isTh) {
      const thKw = {
        "明星八卦": ["เสื้อไอดอล", "แฟนคลับ", "idol shirt", "เสื้อยืดคนดัง", "ของแท้", "fan club tee", "kpop merch", "เสื้อซุปตาร์"],
        "演唱会综艺": ["เสื้อคอนเสิร์ต", "concert tee", "tour merch", "เสื้อถ่ายทอด", "live event", "festival shirt", "เสื้อดนตรี"],
        "影视剧": ["เสื้อหนัง", "drama tee", "movie quote", "เสื้อละคร", "series merch", "character art", "บทพูดคลาสสิก"],
        "游戏电竞": ["เสื้อเกมเมอร์", "gamer shirt", "gaming tee", "เกมสุดฮิต", "steam top", "skin collection", "pro player"],
        "网络热梗": ["เสื้อมีม", "viral shirt", "meme tee", "ไวรัล", "trending", "hot topic", "meme template"],
        "音乐榜单": ["เพลงฮิต", "hit song", "music chart", "apple music", "เสื้อดนตรี", "festival vibe", "on repeat"],
        "平台热搜": ["กระแสโซเชียล", "trending", "hot topic", "twitter viral", "คำค้นยอดนิยม", "hashtag ฮิต", "search popular"],
        "动漫热度": ["อนิเมะฮิต", "anime shirt", "manga style", "character tee", "2D art", "otaku", "cosplay"],
        "游戏热度": ["เกมยอดนิยม", "gaming hot", "steam best seller", "top game", "gamer pro", "rank up", "GG WP"],
      };
      return [...kw.slice(0, 6), ...(thKw[cat] || thKw["平台热搜"])];
    }
    if (isMy) {
      const myKw = {
        "明星八卦": ["baju idol", "fan club", "kpop merchandise", "baju artis", "original authentik", "idol shirt", "baju superstar"],
        "演唱会综艺": ["baju konsert", "concert shirt", "tour merch", "edisi terhad", "live show", "festival tee", "baju artis"],
        "影视剧": ["baju drama", "movie quote", "drama merch", "nama watak", "dialog ikonik", "series lover", "baju filem"],
        "游戏电竞": ["baju gamer", "gaming shirt", "GG WP", "steam top", "gear up", "pro player", "rank up", "menang terus"],
        "网络热梗": ["baju viral", "meme shirt", "trending now", "faham lah", "hot topic", "template meme", "viral terkini"],
        "音乐榜单": ["lagu hits", "music chart", "hit song", "apple music", "baju muzik", "festival vibes", "main bergilir"],
        "平台热搜": ["topik panas", "trending", "viral", "carian popular", "hashtag viral", "sosial media", "search hot"],
        "动漫热度": ["baju anime", "anime fan", "gaya anime", "character design", "2D style", "otaku", "manga art"],
        "游戏热度": ["game popular", "baju gaming", "steam best", "team squad", "gamer pro", "bossku", "booyah"],
      };
      return [...kw.slice(0, 6), ...(myKw[cat] || myKw["平台热搜"])];
    }
    // 多市场：中英泰马混合
    const multiKw = {
      "明星八卦": ["idol shirt", "fan club tee", "เสื้อไอดอล", "baju idol", "kpop merch", "star tee"],
      "演唱会综艺": ["concert tour tee", "tour merch", "เสื้อคอนเสิร์ต", "baju konsert", "festival shirt", "live event"],
      "影视剧": ["movie quote shirt", "drama tee", "เสื้อหนัง", "baju drama", "character art", "series merch"],
      "游戏电竞": ["gamer shirt", "gaming tee", "เสื้อเกมเมอร์", "baju gamer", "steam top", "GG WP"],
      "网络热梗": ["viral meme shirt", "trending tee", "เสื้อมีม", "baju viral", "hot topic", "meme template"],
      "音乐榜单": ["hit song tee", "music chart", "เพลงฮิต", "lagu hits", "festival vibes", "apple music"],
      "平台热搜": ["trending shirt", "hot topic", "กระแสฮิต", "topik panas", "viral", "search popular"],
      "动漫热度": ["anime shirt", "manga style", "อนิเมะ", "baju anime", "character art", "2D design"],
      "游戏热度": ["gaming hot", "steam best", "เกมฮิต", "game popular", "team squad", "rank up"],
    };
    return [...kw.slice(0, 6), ...(multiKw[cat] || multiKw["平台热搜"])];
  }

  function generateSimilarTrends(cat, country) {
    const trends = {
      "明星八卦": ["同组合/剧团其他成员周边", "同期选秀/综艺衍生", "明星联名潮牌合作款", "粉丝应援色系T恤"],
      "演唱会综艺": ["音乐节通用款(Summer Sonic/Big Mountain)", "DJ/Producer系列", "乐器品牌联名(Fender/Gibson)", "Live House巡演地图"],
      "影视剧": ["同导演/编剧其他作品", "流平台Top10联动", "漫画原著改编联动", "经典老剧复刻(Nostalgia Wave)"],
      "游戏电竞": ["同IP手游/端游联动", "电竞赛事战队周边", "主播/Streamer联名", "游戏外设品牌联名"],
      "网络热梗": ["同类meme变体延展", "TikTok挑战赛关联", "表情包系列(Blind Box概念)", "时事梗后续跟进"],
      "体育": ["国家队/俱乐部主场客场", "传奇球员退役纪念", "奥运会/世界杯周期", "极限运动跨界"],
    };
    return trends[cat] || trends["其他热搜"];
  }

  function kwAnalysisHtml(analysis) {
    // 防御：确保 analysis 存在且各字段有默认值
    if (!analysis || typeof analysis !== "object") return "";
    const slogans = Array.isArray(analysis.slogans) ? analysis.slogans : [];
    const elements = Array.isArray(analysis.elements) ? analysis.elements : [];
    const colorsObj = (analysis.colors && typeof analysis.colors === "object") ? analysis.colors : { name: "百搭潮流系", colors: ["#2D3436 → #636E72"], desc: "中性配色" };
    const colorArr = Array.isArray(colorsObj.colors) ? colorsObj.colors : [String(colorsObj.colors || "#888")];
    const seoKw = Array.isArray(analysis.seoKw) ? analysis.seoKw : [];
    const similarTrends = Array.isArray(analysis.similarTrends) ? analysis.similarTrends : [];
    const audience = (analysis.audience && typeof analysis.audience === "object") ? analysis.audience : { primary: "泛兴趣人群", secondary: "热点关注者" };
    const pricing = (analysis.pricing && typeof analysis.pricing === "object") ? analysis.pricing : { range: "฿99-299", cost: "￥2-5", suggest: "小批量测试" };

    const flagTh = slogans.some(s => s && s.th);
    const flagMy = slogans.some(s => s && s.my);

    // 文案行
    const sloganRows = slogans.map(s => `
      <div class="kw-slogan-row">
        <span class="kw-lang-cn">🇨🇳 ${escapeHtml((s && s.cn) || "")}</span>
        ${flagTh ? `<span class="kw-lang-th">🇹🇭 ${escapeHtml((s && s.th) || "")}</span>` : ""}
        ${flagMy ? `<span class="kw-lang-my">🇲🇾 ${escapeHtml((s && s.my) || "")}</span>` : ""}
      </div>`).join("");

    // 图案元素
    const elHtml = elements.map(el => `<span class="kw-el-tag">${escapeHtml(el)}</span>`).join("");

    // 色彩（colorsObj.colors 才是数组）
    const colorHtml = colorArr.map(c => `<span class="kw-color-chip" style="background:linear-gradient(135deg,${c})">${escapeHtml(c)}</span>`).join("");

    // SEO关键词
    const seoHtml = seoKw.map(k => `<span class="kw-seo-tag">${escapeHtml(k)}</span>`).join("");

    // 类似爆款
    const simHtml = similarTrends.map(t => `<li>${escapeHtml(t)}</li>`).join("");

    return `
      <div class="m-section m-kw-section">
        <h4>🎨 印花关键词分析 <span class="m-sub">AI驱动 · 可直接用于打样</span></h4>

        <div class="kw-block">
          <div class="kw-block-title">📝 推荐印花文案（可直接印）</div>
          <div class="kw-slogans">${sloganRows}</div>
        </div>

        <div class="kw-block">
          <div class="kw-block-title">🖼 图案元素建议</div>
          <div class="kw-tags">${elHtml}</div>
        </div>

        <div class="kw-block kw-block-half">
          <div class="kw-block-title">🎨 色彩风格 · ${escapeHtml(colorsObj.name || "")}</div>
          <div class="kw-colors">${colorHtml}</div>
          <div class="kw-color-desc">${escapeHtml(colorsObj.desc || "")}</div>
        </div>

        <div class="kw-block kw-block-half">
          <div class="kw-block-title">👥 目标客群</div>
          <div class="kw-audience">
            <div><b>核心：</b>${escapeHtml(audience.primary || "")}</div>
            <div><b>延伸：</b>${escapeHtml(audience.secondary || "")}</div>
            ${audience.th ? `<div>🇹🇭 ${escapeHtml(audience.th)}</div>` : ""}
            ${audience.my ? `<div>🇲🇾 ${escapeHtml(audience.my)}</div>` : ""}
          </div>
        </div>

        <div class="kw-block kw-block-half">
          <div class="kw-block-title">💰 定价参考</div>
          <div class="kw-pricing">
            <div class="kw-price-range">${escapeHtml(pricing.range || "")}</div>
            <div>成本：${escapeHtml(pricing.cost || "")}</div>
            <div class="kw-price-tip">${escapeHtml(pricing.suggest || "")}</div>
          </div>
        </div>

        <div class="kw-block kw-block-half">
          <div class="kw-block-title">🔍 搜索/Lazada关键词</div>
          <div class="kw-tags kw-seo">${seoHtml}</div>
        </div>

        <div class="kw-block">
          <div class="kw-block-title">📈 类似爆款方向（可提前布局）</div>
          <ul class="kw-similar">${simHtml}</ul>
        </div>
      </div>`;
  }

  function suggestion(e) {
    let s = "";
    if (e.printType === "文字款") s += "建议以<b>文字款</b>为主，突出泰文/中文口号，成本低、上架快，适合快速测试。";
    else if (e.printType === "图案款") s += "建议以<b>图案款</b>为主，视觉冲击强，适合做主推爆款。";
    else s += "建议采用<b>文字+图案</b>组合款，兼顾口号传播与视觉识别。";
    if (e.stars >= 4) s += " 印花指数 ★4，属高潜力爆款候选，";
    else if (e.stars === 3) s += " 印花指数 ★3，可小批量试水，";
    else s += " 印花指数偏低，建议仅做低成本测试，";
    s += `当前还热约 <b>${e.hotDays} 天</b>，建议在此窗口内完成打样上架。`;
    if (e.risk.startsWith("高")) s += " ⚠️ <b>高风险</b>：涉及争议或敏感内容，请核定授权与合规，谨慎备货或规避。";
    else if (e.risk.startsWith("中")) s += " 中风险：可上架，但注意图案避免直接搬运原 IP/肖像。";
    else s += " 低风险：可放心开发。";
    return s;
  }

  function modalHtml(e) {
    const sourcesHtml = e.sources.map((s) => {
      const link = s.url
        ? `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener" class="src-link">${escapeHtml(s.name)} ↗</a>`
        : `<span class="src-name">${escapeHtml(s.name)}</span>`;
      return `<div class="src-item">
        <span class="src-type" title="${escapeHtml(s.type)}">${getTypeIcon(s.type)}</span>
        ${link}
        <span class="src-region">${getRegionFlag(s.region)}</span>
        <span class="src-cred ${credClass(s.credibility)}">${escapeHtml(s.credibility)}可信</span>
      </div>`;
    }).join("");

    const tlHtml = e.timeline.map((n) => `
      <div class="tl-node ${n.verified ? "verified" : ""}">
        <div class="tl-dot"></div>
        <div class="tl-content">
          <div class="tl-date">${escapeHtml(n.date)}</div>
          <div class="tl-label">${escapeHtml(n.label)} ${n.verified ? '<span class="tl-verified">已核实</span>' : '<span class="tl-est">示意</span>'}</div>
          <div class="tl-desc">${escapeHtml(n.desc)}</div>
        </div>
      </div>`).join("");

    const primaryBtn = e.primaryUrl
      ? `<a class="m-primary" href="${escapeHtml(e.primaryUrl)}" target="_blank" rel="noopener">🔗 查看原始报道 ↗</a>` : "";

    // 图片画廊（支持多图切换）
    const images = getEventImages(e);
    _galleryImages = images.map(img => Object.assign({}, img, { catCn: e.catCn }));
    _galleryIdx = 0;

    let galleryHtml;
    if (images.length === 0 || (images.length === 1 && images[0].isSvg)) {
      // 纯概念图
      galleryHtml = `<div class="m-gallery"><div class="m-gallery-none" style="--cg:${catGradient(e.catCn)}">${CAT_EMOJI[e.catCn] || "🔥"}</div></div>`;
    } else {
      const firstImg = images[0];
      const mainEl = firstImg.isSvg
        ? `<div class="m-gallery-none" id="mGalleryMain" style="--cg:${catGradient(e.catCn)}"><span>${CAT_EMOJI[e.catCn] || "🔥"}</span></div>`
        : `<img class="m-gallery-main" id="mGalleryMain" src="${escapeHtml(firstImg.url)}" onclick="openLightbox('${escapeHtml(firstImg.url)}')" onerror="this.onerror=null;this.style.display='none';var ph=document.getElementById('mGalleryFallback');if(ph)ph.style.display='flex';" /><div class="m-gallery-none" id="mGalleryFallback" style="--cg:${catGradient(e.catCn)};display:none"><span>${CAT_EMOJI[e.catCn] || "🔥"}</span></div>`;
      const dots = images.map((_, i) => `<button class="m-gallery-dot${i===0?' active':''}" onclick="switchGalleryImg(${i})"></button>`).join("");
      const navBtns = images.length > 1
        ? `<button class="m-gallery-nav m-gallery-prev" onclick="galleryPrev()">◀</button><button class="m-gallery-nav m-gallery-next" onclick="galleryNext()">▶</button>`
        : "";
      galleryHtml = `<div class="m-gallery">
        ${mainEl}
        ${navBtns}
        ${images.length > 1 ? `<div class="m-gallery-count" id="mGalleryCount">1/${images.length}</div>` : ""}
        ${images.length > 1 ? `<div class="m-gallery-dots">${dots}</div>` : ""}
      </div>`;
    }

    const hasVerified = e.timeline.some((n) => n.verified);
    return `
      <button class="m-close" onclick="closeModal()">×</button>
      ${galleryHtml}
      <span class="m-cat">${escapeHtml(e.catCn)} · ${e.country === "th" ? "🇹🇭 泰国" : e.country === "my" ? "🇲🇾 马来西亚" : "🌏 多市场"}${e.localFlag ? " · 🇹🇭🇲🇾 含本地媒体" : ""}</span>
      <h2>${escapeHtml(e.titleCn)}</h2>
      <div class="m-orig">${escapeHtml(e.titleOrig)}</div>
      <div class="m-badges">
        <span class="stars" style="font-size:16px">${stars(e.stars)} 印花指数</span>
        <span class="pt ${ptClass(e.printType)}">${escapeHtml(e.printType)}</span>
        <span class="risk ${riskClass(e.risk)}">${escapeHtml(e.risk)}</span>
        ${meter("可信度", e.credibilityScore, credColor(e.credibilityScore))}
        ${meter("讨论热度", e.buzzIndex, buzzColor(e.buzzIndex))}
      </div>
      <div class="m-summary">${escapeHtml(e.summary)}</div>

      <div class="m-section">
        <h4>📡 数据来源分析 <span class="m-sub">${e.sources.length} 个来源 · 本地 ${e.sourceBreadth.local} / 全球 ${e.sourceBreadth.global} / 社媒 ${e.sourceBreadth.social_only}</span></h4>
        <div class="src-list">${sourcesHtml}</div>
      </div>

      <div class="m-section">
        <h4>🕒 事件脉络 <span class="m-sub">${hasVerified ? "含已核实节点" : "当前为推断示意，将由研究逐步核实"}</span></h4>
        <div class="tl">${tlHtml}</div>
      </div>

      ${kwAnalysisHtml(keywordAnalysis(e))}

      ${primaryBtn}
    ${e.imageSource ? `<div class="m-imgsrc">🖼 配图来源：${escapeHtml(e.imageSource)}</div>` : ""}
      <div class="m-meta">
        <div>🔥 还热 <b>${e.hotDays}</b> 天</div>
        <div>🕒 ${escapeHtml(e.timeRel)}</div>
        <div>📰 ${e.sources.length} 来源</div>
      </div>
      <div class="m-tags">${e.tags.map((t) => `<span>${escapeHtml(t)}</span>`).join("")}</div>
      <div class="m-suggest">💡 印花建议：${suggestion(e)}</div>
    `;
  }

  window.openModal = function (id) {
    const e = EVENTS.find((x) => x.id === id);
    if (!e) return;
    document.getElementById("modal").innerHTML = modalHtml(e);
    document.getElementById("modalMask").classList.add("open");
    document.body.style.overflow = "hidden";
  };
  window.closeModal = function () {
    document.getElementById("modalMask").classList.remove("open");
    document.body.style.overflow = "";
  };
  window.openLightbox = function (src) {
    document.getElementById("lbImg").src = src;
    document.getElementById("lbMask").classList.add("open");
  };
  window.closeLightbox = function () {
    document.getElementById("lbMask").classList.remove("open");
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeModal(); closeLightbox(); }
  });

  // 全局图片加载失败处理 → 显示分类概念图/占位（覆盖所有卡片图片）
  document.addEventListener("error", function (e) {
    const t = e.target;
    if (!t || t.tagName !== "IMG") return;
    // 只处理卡片内的图片
    const cover = t.closest ? t.closest(".cover") : null;
    if (!cover) return;
    // 隐藏失败的图片
    t.style.display = "none";
    // 查找或创建占位
    let ph = cover.querySelector(".rt-ph");
    if (ph) {
      ph.style.display = "flex";
    } else {
      // 没有 rt-ph → 生成 SVG 概念图插入
      const cat = cover.getAttribute("data-cat") || "";
      const title = cover.getAttribute("data-title") || "";
      t.insertAdjacentHTML("afterend", generateConceptSvg(cat, title));
    }
  }, true);

  // ---------- 实时层（云端榜单，关电脑也更新，零 Key） ----------
  const RT_META = document.querySelector('meta[name="realtime-src"]');
  const REALTIME_SRC = RT_META ? RT_META.getAttribute("content") : "";
  let rtUpdated = window.REALTIME_UPDATED || "";
  let rtFirst = true;

  // 把任意来源的事件规范成统一结构，避免缺字段导致渲染/弹窗崩溃
  function normalizeEvent(e) {
    if (!e || typeof e !== "object") return e;
    // stars：数字或 🔥/★ 字符串 → 数字 0~4
    let s = e.stars;
    if (typeof s === "string") {
      const cnt = (s.match(/🔥|★/g) || []).length;
      s = cnt > 0 ? cnt : (parseInt(s, 10) || 3);
    }
    e.stars = Math.max(0, Math.min(4, Number(s) || 0));
    // country：中文 → 代码
    if (e.country === "泰国") e.country = "th";
    else if (e.country === "马来西亚") e.country = "my";
    else if (e.country === "多市场") e.country = "multi";
    // 兜底缺失字段
    if (!Array.isArray(e.sources)) e.sources = [];
    e.sources = e.sources.map((x) => {
      const c = x && x.credibility;
      let cs = c;
      if (typeof c === "number") cs = c >= 75 ? "高" : c >= 50 ? "中" : "低";
      return Object.assign({}, x, { credibility: cs });
    });
    if (!Array.isArray(e.timeline)) e.timeline = [];
    if (!Array.isArray(e.tags)) e.tags = [];
    if (!e.sourceBreadth || typeof e.sourceBreadth !== "object") e.sourceBreadth = { local: 0, global: 0, social_only: 0 };
    if (typeof e.credibilityScore !== "number") e.credibilityScore = Number(e.credibilityScore) || 60;
    if (typeof e.buzzIndex !== "number") e.buzzIndex = Number(e.buzzIndex) || 50;
    if (typeof e.hotDays !== "number") e.hotDays = Number(e.hotDays) || 1;
    if (typeof e.hasMedia !== "boolean") e.hasMedia = !!e.hasMedia;
    if (typeof e.localFlag !== "boolean") e.localFlag = !!e.localFlag;
    if (typeof e.cover !== "string") e.cover = "";
    if (typeof e.coverType !== "string") e.coverType = "placeholder";
    if (typeof e.printType !== "string") e.printType = "文字+图案";
    if (typeof e.risk !== "string") e.risk = "低";
    if (typeof e.titleCn !== "string") e.titleCn = String(e.titleCn || e.titleOrig || "未命名");
    if (typeof e.summary !== "string") e.summary = "";
    if (typeof e.catCn !== "string") e.catCn = "其他热搜";
    if (typeof e.timeRel !== "string") e.timeRel = "";
    if (typeof e.timeAbs !== "string") e.timeAbs = "";
    if (typeof e.imageSource !== "string") e.imageSource = "";
    if (typeof e.primaryUrl !== "string") e.primaryUrl = "";
    return e;
  }

  function rebuildEvents() {
    const base = (window.EVENTS || []).map(normalizeEvent);
    const rt = (window.EVENTS_REALTIME || []).map(normalizeEvent);
    const seen = new Set();
    const out = [];
    for (const e of base.concat(rt)) {
      if (e && e.id && !seen.has(e.id)) { seen.add(e.id); out.push(e); }
    }
    EVENTS = out;
    return out.length;
  }

  function loadRealtimeScript(cb) {
    if (!REALTIME_SRC) return;
    const s = document.createElement("script");
    s.src = REALTIME_SRC + "?_=" + Date.now();
    s.onload = function () { try { cb && cb(); } catch (e) {} };
    s.onerror = function () {};
    document.head.appendChild(s);
  }

  function refreshRealtime() {
    loadRealtimeScript(function () {
      const u = window.REALTIME_UPDATED || "";
      const has = (window.EVENTS_REALTIME || []).length > 0;
      if (!has) return;
      const changed = u && u !== rtUpdated;
      rtUpdated = u || rtUpdated;
      rebuildEvents();
      renderHeroStats();
      render();
      // 右上角日期改为云端实时更新时间 + 下次更新倒计时
      const ud = document.getElementById("updatedDate");
      const lu = document.getElementById("lastUpdate");
      if (ud && rtUpdated) ud.textContent = rtUpdated.slice(0, 10);
      if (lu) {
        lu.textContent = "🔄 实时榜单：" + (rtUpdated || "").replace("T", " ").slice(0, 16) + " · 每30分钟自动刷新";
        // 显示下次预计更新（约30分钟后）
        const nextEl = document.getElementById("nextUpdate");
        if (nextEl && rtUpdated) {
          try {
            const last = new Date(rtUpdated);
            const next = new Date(last.getTime() + 30 * 60 * 1000);
            nextEl.textContent = "⏰ 下次约 " + next.toISOString().replace("T", " ").slice(0, 16) + " 更新";
            nextEl.style.display = "";
          } catch(e) { nextEl.style.display = "none"; }
        }
      }
      if (changed && !rtFirst) {
        showToast("🔄 实时榜单已更新：" + (u || "").replace("T", " ").slice(0, 16) + "，共 " + EVENTS.length + " 条热点");
      }
      rtFirst = false;
    });
  }

  function setupLiveUpdate() {
    const lu = document.getElementById("lastUpdate");
    const ud = document.getElementById("updatedDate");
    let cur = window.SITE_UPDATED || "";
    if (lu) lu.textContent = cur ? ("最后更新：" + cur.replace("T", " ").slice(0, 16)) : "";
    if (ud && cur) ud.textContent = cur.slice(0, 10);

    function parseDataJs(txt) {
      try {
        const fn = new Function("window", txt + "\n;return {E: window.EVENTS, U: window.SITE_UPDATED};");
        const r = fn({});
        return { events: r.E || [], updated: r.U || "" };
      } catch (e) { return null; }
    }

    async function checkMeta() {
      try {
        const mres = await fetch("js/meta.js?_=" + Date.now(), { cache: "no-store" });
        const mt = await mres.text();
        const mm = mt.match(/SITE_META\s*=\s*(\{[^}]*\})/);
        if (!mm) return;
        const meta = JSON.parse(mm[1]);
        if (!meta.updated || meta.updated === cur) return;
        const dres = await fetch("js/data.js?_=" + Date.now(), { cache: "no-store" });
        const dt = await dres.text();
        const parsed = parseDataJs(dt);
        if (!parsed || !parsed.events.length) return;
        const y = window.scrollY;
        window.EVENTS = parsed.events;
        window.SITE_UPDATED = parsed.updated;
        cur = parsed.updated;
        rebuildEvents();
        if (lu) lu.textContent = "最后更新：" + cur.replace("T", " ").slice(0, 16);
        if (ud) ud.textContent = cur.slice(0, 10);
        renderHeroStats();
        render();
        window.scrollTo(0, y);
        showToast("🔄 已更新至 " + cur.replace("T", " ").slice(0, 16) + "，共 " + EVENTS.length + " 条热点");
      } catch (e) {}
    }

    setInterval(checkMeta, 45 * 1000);
    checkMeta();

    // 实时层：每 5 分钟拉取云端榜单（关电脑也更新，零 Key）
    refreshRealtime();
    setInterval(refreshRealtime, 5 * 60 * 1000);
  }

  function showToast(msg) {
    let t = document.getElementById("liveToast");
    if (!t) {
      t = document.createElement("div");
      t.id = "liveToast";
      t.className = "live-toast";
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove("show"), 4000);
  }
  document.addEventListener("DOMContentLoaded", init);
  document.addEventListener("DOMContentLoaded", setupLiveUpdate);
})();
