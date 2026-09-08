// 印选站 · 电商日历（读取 window.CALENDAR = { meta, items }）
(function () {
  var CAL = window.CALENDAR || { meta: {}, items: [] };
  var items = CAL.items || [];
  var meta = CAL.meta || {};
  var TYPE = {
    festival: { label: "节日", color: "#7ee0a0" },
    promo: { label: "大促", color: "#ff9aa6" },
    seasonal: { label: "季节", color: "#ffd479" },
    micro: { label: "微节日", color: "#8fd3ff" },
    news: { label: "跨境新闻", color: "#c792ea" },
  };
  var FLAG = { th: "🇹🇭", my: "🇲🇾", both: "🇹🇭🇲🇾", multi: "🌏", global: "🌐" };
  var MONTHS = ["", "1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];

  function monthOf(s) { var m = s.split("-").map(Number); return m.length === 3 ? m[1] : m[0]; }
  function dayOf(s) { var m = s.split("-").map(Number); return m.length === 3 ? m[2] : m[1]; }
  function parseNext(s, ref) {
    var y, mo, d;
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) { var a = s.split("-").map(Number); y = a[0]; mo = a[1]; d = a[2]; }
    else { var b = s.split("-").map(Number); mo = b[0]; d = b[1]; y = ref.getFullYear(); }
    var cand = new Date(y, mo - 1, d);
    if (cand < ref) cand = new Date(y + 1, mo - 1, d);
    return cand;
  }

  var ref = new Date(meta.updated || new Date().toISOString().slice(0, 10));
  var type = "全部", country = "全部";

  function card(x) {
    var color = (TYPE[x.type] || {}).color || "#888";
    var label = (TYPE[x.type] || {}).label || x.type;
    return '<div class="cal-card" style="border-left:4px solid ' + color + '">' +
      '<div class="cal-top"><b>' + x.title + '</b><span class="muted">' + (FLAG[x.country] || "") + " " + x.date + (x.cadence === "monthly" ? " 每月" : "") + "</span></div>" +
      '<span class="cal-type" style="background:' + color + '">' + label + "</span>" +
      '<div class="cal-desc">' + x.desc + "</div>" +
      (x.designTip ? '<div class="cal-tip">🎯 ' + x.designTip + "</div>" : "") +
      (x.source ? '<div class="cal-src">来源：' + x.source + "</div>" : "") +
      "</div>";
  }

  function apply() {
    var f = items.filter(function (x) {
      if (type !== "全部" && x.type !== type) return false;
      if (country !== "全部" && x.country !== country && x.country !== "both" && x.country !== "multi" && x.country !== "global") return false;
      return true;
    });
    // 未来60天
    var up = f.filter(function (x) { return x.cadence !== "monthly"; })
      .map(function (x) { return { x: x, next: parseNext(x.date, ref) }; })
      .filter(function (o) { var diff = (o.next - ref) / 86400000; return diff >= -3 && diff <= 75; })
      .sort(function (a, b) { return a.next - b.next; })
      .map(function (o) { return o.x; });
    // 每月固定
    var monthly = f.filter(function (x) { return x.cadence === "monthly"; });
    // 按月
    var byM = {};
    f.forEach(function (x) {
      if (x.cadence === "monthly") return;
      var mo = monthOf(x.date); (byM[mo] = byM[mo] || []).push(x);
    });
    Object.keys(byM).forEach(function (k) { byM[k].sort(function (a, b) { return dayOf(a.date) - dayOf(b.date); }); });

    document.getElementById("calUpcoming").innerHTML = up.length ? up.map(card).join("") : '<div class="muted">暂无。</div>';
    document.getElementById("calMonthly").innerHTML = monthly.length ? monthly.map(card).join("")
      : '<div class="muted">暂无。</div>';
    var yhtml = "";
    Object.keys(byM).sort(function (a, b) { return a - b; }).forEach(function (mo) {
      yhtml += '<div class="cal-month"><div class="cal-month-h">' + MONTHS[+mo] + "</div>" + byM[mo].map(card).join("") + "</div>";
    });
    document.getElementById("calYear").innerHTML = yhtml || '<div class="muted">当前筛选无结果。</div>';
  }

  // 筛选按钮
  function bind(selector, cb) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), function (b) {
      b.addEventListener("click", function () {
        Array.prototype.forEach.call(document.querySelectorAll(selector), function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        cb(b.getAttribute("data-v"));
        apply();
      });
    });
  }
  bind(".cal-type-btn", function (v) { type = v; });
  bind(".cal-country-btn", function (v) { country = v; });

  document.getElementById("calMeta").textContent =
    "数据更新：" + (meta.updated || "-") + " · 共 " + items.length + " 条（节日/大促/季节/微节日/跨境新闻）";
  apply();
})();
