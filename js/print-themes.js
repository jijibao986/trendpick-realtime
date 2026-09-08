// 印选站 · 近30天热门印花主题风格分析（实时读 window.EVENTS，纯前端渲染，无依赖）
(function () {
  var EVENTS = window.EVENTS || [];
  var UPDATED = window.SITE_UPDATED ? new Date(window.SITE_UPDATED) : new Date();
  var WINDOW = 30;
  var cutoff = new Date(UPDATED.getTime() - WINDOW * 86400000);

  function latestDate(e) {
    var d = null;
    if (e.timeline && e.timeline.length) {
      e.timeline.forEach(function (t) {
        var dt = new Date(t.date);
        if (!isNaN(dt) && (!d || dt > d)) d = dt;
      });
    }
    if (!d && e.timeAbs) {
      var m = String(e.timeAbs).match(/(\d{2})\/(\d{2})\/(\d{2})/);
      if (m) d = new Date(2000 + (+m[1]), +m[2] - 1, +m[3]);
    }
    if (!d && e.timeRel) {
      var m2 = String(e.timeRel).match(/(\d{4})-(\d{2})-(\d{2})/);
      if (m2) d = new Date(+m2[1], +m2[2] - 1, +m2[3]);
    }
    return d;
  }
  function inWindow(e) { var d = latestDate(e); return d && d >= cutoff; }
  function weight(e) { return (Number(e.stars) || 0) * 20 + (Number(e.buzzIndex) || 0); }

  var GEO = { "泰国": 1, "马来西亚": 1, "全球": 1, "中国": 1, "日本": 1, "韩国": 1, "美国": 1, "th": 1, "my": 1, "global": 1, "en": 1, "fr": 1, "X热趋": 1 };
  var TAGRE = /[一-龥A-Za-z]{2,}/;
  function cleanTags(arr) {
    var out = [];
    (arr || []).forEach(function (raw) {
      var t = String(raw).trim();
      if (!t || !TAGRE.test(t) || t.length < 2 || GEO[t]) return;
      out.push(t);
    });
    return out;
  }

  var recent = EVENTS.filter(inWindow);
  var byCat = {}, byType = {}, byCountry = {}, byTag = {};
  recent.forEach(function (e) {
    var w = weight(e);
    var cat = e.catCn || e.cat || "其他";
    byCat[cat] = byCat[cat] || { name: cat, count: 0, weight: 0 };
    byCat[cat].count++; byCat[cat].weight += w;
    var pt = e.printType || "未标注";
    byType[pt] = byType[pt] || { name: pt, count: 0, weight: 0 };
    byType[pt].count++; byType[pt].weight += w;
    var co = e.country === "my" ? "马来西亚" : e.country === "th" ? "泰国" : "全球";
    byCountry[co] = byCountry[co] || { name: co, count: 0 };
    byCountry[co].count++;
    cleanTags(e.tags).forEach(function (t) {
      byTag[t] = byTag[t] || { tag: t, weight: 0, count: 0 };
      byTag[t].weight += w; byTag[t].count++;
    });
  });
  function sortObj(o) { return Object.keys(o).map(function (k) { return o[k]; }).sort(function (a, b) { return b.weight - a.weight; }); }
  var catArr = sortObj(byCat), typeArr = sortObj(byType), tagArr = sortObj(byTag).slice(0, 18);
  var topThemes = recent.slice().sort(function (a, b) { return weight(b) - weight(a); }).slice(0, 14).map(function (e) {
    return {
      titleCn: e.titleCn, catCn: e.catCn || e.cat || "", printType: e.printType || "",
      country: e.country === "my" ? "马来西亚" : e.country === "th" ? "泰国" : "全球",
      stars: Number(e.stars) || 0, tags: cleanTags(e.tags),
      summary: (e.summary || "").slice(0, 150), url: e.primaryUrl || (e.sources && e.sources[0] && e.sources[0].url) || "",
    };
  });

  var topStyle = typeArr[0] ? typeArr[0].name : "-";
  var topCat = catArr[0] ? catArr[0].name : "-";

  // ---- 渲染 ----
  function el(id) { return document.getElementById(id); }
  function stars(n) { return "★".repeat(n) + "☆".repeat(Math.max(0, 5 - n)); }
  function barRows(arr, key, color) {
    var max = Math.max.apply(null, arr.map(function (x) { return x.count; }));
    return arr.map(function (x) {
      var pct = max ? Math.round((x.count / max) * 100) : 0;
      return '<div class="barrow"><span class="barlabel">' + x[key] + '</span><span class="bartrack"><span class="barfill" style="width:' + pct + '%;background:' + color + '"></span></span><span class="barval">' + x.count + '</span></div>';
    }).join("");
  }
  function tagChips(arr) {
    return arr.map(function (x) { return '<span class="chip">' + x.tag + ' <i>' + x.count + '</i></span>'; }).join("");
  }

  el("ptKpi").innerHTML =
    kpi("主题词总数", Object.keys(byTag).length) +
    kpi("主推风格", topStyle) +
    kpi("主推类目", topCat) +
    kpi("泰国事件", byCountry["泰国"] ? byCountry["泰国"].count : 0) +
    kpi("马来事件", byCountry["马来西亚"] ? byCountry["马来西亚"].count : 0);

  el("ptStyle").innerHTML = barRows(typeArr, "name", "#7ee0a0");
  el("ptCat").innerHTML = barRows(catArr, "name", "#6ea8fe");
  el("ptTags").innerHTML = tagChips(tagArr);

  // 主题卡片（带国家筛选）
  var country = "全部";
  function renderThemes() {
    var list = country === "全部" ? topThemes : topThemes.filter(function (t) { return t.country === country; });
    el("ptThemes").innerHTML = list.map(function (t) {
      var tags = (t.tags || []).slice(0, 6).map(function (g) { return '<span class="chip sm">' + g + "</span>"; }).join("");
      return '<div class="tcard"><div class="tchead"><b>' + t.titleCn + '</b><span class="muted">' + t.country + "</span></div>" +
        '<div class="muted sm">' + t.catCn + " · " + t.printType + " · " + stars(t.stars) + "</div>" +
        '<div class="tdesc">' + t.summary + "</div>" +
        '<div class="tchips">' + tags + "</div>" +
        (t.url ? '<a class="src" href="' + t.url + '" target="_blank" rel="noreferrer">查看来源 ↗</a>' : "") +
        "</div>";
    }).join("") || '<div class="muted">该国家暂无主题。</div>';
  }
  renderThemes();
  Array.prototype.forEach.call(document.querySelectorAll(".pt-country"), function (b) {
    b.addEventListener("click", function () {
      country = b.getAttribute("data-c");
      Array.prototype.forEach.call(document.querySelectorAll(".pt-country"), function (x) { x.classList.remove("active"); });
      b.classList.add("active");
      renderThemes();
    });
  });

  el("ptMeta").textContent = "参考日 " + UPDATED.toISOString().slice(0, 10) + " · 窗口 " + WINDOW + " 天 · 近30天事件 " + recent.length + " / 总 " + EVENTS.length;

  function kpi(label, value) {
    return '<div class="pt-kpi"><div class="pt-kpi-v">' + value + '</div><div class="pt-kpi-l">' + label + "</div></div>";
  }
})();
