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
  function stars(n) { return "★".repeat(n) + "☆".repeat(4 - n); }
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

  function coverHtml(e) {
    const local = e.localFlag ? '<span class="local-badge">🇹🇭🇲🇾 本地</span>' : "";
    const isRemote = e.coverType === "remote" || (e.cover && /^https?:\/\//.test(e.cover));
    if (e.cover && isRemote) {
      const label = "远程配图";
      return `<div class="cover ${e.coverType}">
        <img class="rt-img" src="${escapeHtml(e.cover)}" alt="${escapeHtml(e.titleCn)}" loading="lazy" onclick="openLightbox('${escapeHtml(e.cover)}')" />
        <div class="rt-ph" style="--cg:${catGradient(e.catCn)}"><span class="ph-emoji">${CAT_EMOJI[e.catCn] || "🔥"}</span></div>
        <span class="cover-badge ${e.coverType}">${label}</span>${local}
      </div>`;
    }
    if (e.cover) {
      const label = "真实配图";
      return `<div class="cover ${e.coverType}" onclick="openLightbox('img/${escapeHtml(e.cover)}')">
        <img src="img/${escapeHtml(e.cover)}" alt="${escapeHtml(e.titleCn)}" loading="lazy" />
        <span class="cover-badge ${e.coverType}">${label}</span>${local}
      </div>`;
    }
    return `<div class="cover none" style="--cg:${catGradient(e.catCn)}">
      <span class="ph-emoji">${CAT_EMOJI[e.catCn] || "🔥"}</span>
      <span class="cover-badge none">暂无配图</span>${local}
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

  // ---------- modal ----------
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

    const isRemote = e.coverType === "remote" || (e.cover && /^https?:\/\//.test(e.cover));
    const coverBig = e.cover && isRemote
      ? `<img class="m-cover rt-img" src="${escapeHtml(e.cover)}" alt="" onclick="openLightbox('${escapeHtml(e.cover)}')" /><div class="m-cover none rt-ph" style="--cg:${catGradient(e.catCn)}"><span>${CAT_EMOJI[e.catCn] || "🔥"}</span></div>`
      : e.cover
        ? `<img class="m-cover" src="img/${escapeHtml(e.cover)}" alt="" onclick="openLightbox('img/${escapeHtml(e.cover)}')" />`
        : `<div class="m-cover none" style="--cg:${catGradient(e.catCn)}"><span>${CAT_EMOJI[e.catCn] || "🔥"}</span></div>`;

    const hasVerified = e.timeline.some((n) => n.verified);
    return `
      <button class="m-close" onclick="closeModal()">×</button>
      ${coverBig}
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

  // 远程图加载失败 → 显示分类占位（仅作用于实时层 rt-img）
  document.addEventListener("error", function (e) {
    const t = e.target;
    if (t && t.tagName === "IMG" && t.classList && t.classList.contains("rt-img")) {
      const ph = t.parentNode ? t.parentNode.querySelector(".rt-ph") : null;
      if (ph) { t.style.display = "none"; ph.style.display = "flex"; }
    }
  }, true);

  // ---------- 实时层（云端榜单，关电脑也更新，零 Key） ----------
  const RT_META = document.querySelector('meta[name="realtime-src"]');
  const REALTIME_SRC = RT_META ? RT_META.getAttribute("content") : "";
  let rtUpdated = window.REALTIME_UPDATED || "";
  let rtFirst = true;

  function rebuildEvents() {
    const base = window.EVENTS || [];
    const rt = window.EVENTS_REALTIME || [];
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
