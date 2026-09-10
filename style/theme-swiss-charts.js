/* ==========================================================================
   Swiss Minimal 瑞士极简 — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.5.html
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-swiss-charts.js"></script>

   原理：
   1. 注册名为 "swiss" 的 ECharts 主题（响应 data-mode 自动切换 Light/Dark 配色）
   2. 拦截 echarts.init，自动套用该主题
   3. 拦截 setOption，将硬编码的旧配色替换为瑞士极简配色
   4. 监听 data-mode 属性变化，切换配色后重新补丁所有图表
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  // —— 瑞士极简配色表 ——
  // Light 调色板
  var S_LIGHT = {
    palette: ["#d62828","#003da5","#007a33","#f77f00","#5c2d91","#008575","#000000","#6c757d"],
    txt:     "#000000",
    txt2:    "rgba(0,0,0,0.50)",
    line:    "rgba(0,0,0,0.12)",
    split:   "rgba(0,0,0,0.06)",
    surface: "#ffffff",
    tipBg:   "rgba(255,255,255,0.95)",
    tipBd:   "rgba(0,0,0,0.15)",
  };
  // Dark 调色板
  var S_DARK = {
    palette: ["#ff4444","#4488ff","#44bb77","#ffaa33","#8844cc","#44bbaa","#ffffff","#adb5bd"],
    txt:     "#f0f0f0",
    txt2:    "rgba(240,240,240,0.55)",
    line:    "rgba(255,255,255,0.12)",
    split:   "rgba(255,255,255,0.06)",
    surface: "#0a0a0a",
    tipBg:   "rgba(17,17,17,0.95)",
    tipBd:   "rgba(255,255,255,0.15)",
  };

  // —— 旧色 → 新色 映射表（Light）——
  var COLOR_MAP_LIGHT = {
    "#0071e3": "#003da5",
    "#2997ff": "#003da5",
    "#34c759": "#007a33",
    "#ff3b30": "#d62828",
    "#ff9f0a": "#f77f00",
    "#5e5ce6": "#5c2d91",
    "#00b8d4": "#008575",
    "#1a7f37": "#007a33",
    "#c0392b": "#d62828",
    "#9a6200": "#f77f00",
    "#4240c8": "#5c2d91",
    "#0a5fb8": "#003da5",
  };
  // —— 旧色 → 新色 映射表（Dark）——
  var COLOR_MAP_DARK = {
    "#0071e3": "#4488ff",
    "#2997ff": "#4488ff",
    "#34c759": "#44bb77",
    "#ff3b30": "#ff4444",
    "#ff9f0a": "#ffaa33",
    "#5e5ce6": "#8844cc",
    "#00b8d4": "#44bbaa",
    "#1a7f37": "#44bb77",
    "#c0392b": "#ff4444",
    "#9a6200": "#ffaa33",
    "#4240c8": "#8844cc",
    "#0a5fb8": "#4488ff",
  };
  // —— rgba 前缀映射（Light）——
  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,":   "rgba(0,61,165,",
    "rgba(41,151,255,":  "rgba(0,61,165,",
    "rgba(52,199,89,":   "rgba(0,122,51,",
    "rgba(255,59,48,":   "rgba(214,40,40,",
    "rgba(255,159,10,":  "rgba(247,127,0,",
    "rgba(94,92,230,":   "rgba(92,45,145,",
    "rgba(0,184,212,":   "rgba(0,133,117,",
  };
  // —— rgba 前缀映射（Dark）——
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,":   "rgba(68,136,255,",
    "rgba(41,151,255,":  "rgba(68,136,255,",
    "rgba(52,199,89,":   "rgba(68,187,119,",
    "rgba(255,59,48,":   "rgba(255,68,68,",
    "rgba(255,159,10,":  "rgba(255,170,51,",
    "rgba(94,92,230,":   "rgba(136,68,204,",
    "rgba(0,184,212,":   "rgba(68,187,170,",
  };

  // —— 获取当前模式 ——
  function currentMode() {
    return document.documentElement.getAttribute("data-mode") === "dark" ? "dark" : "light";
  }
  function palette() { return currentMode() === "dark" ? S_DARK.palette : S_LIGHT.palette; }
  function colors() { return currentMode() === "dark" ? S_DARK : S_LIGHT; }
  function buildColorMap() {
    var mode = currentMode();
    var base = mode === "dark" ? COLOR_MAP_DARK : COLOR_MAP_LIGHT;
    var pal = mode === "dark" ? S_DARK.palette : S_LIGHT.palette;
    var other = mode === "dark" ? S_LIGHT.palette : S_DARK.palette;
    var m = {};
    for (var k in base) { if (base.hasOwnProperty(k)) m[k.toLowerCase()] = base[k]; }
    // 跨模式反向映射：将另一模式的调色板颜色映射回当前模式
    for (var i = 0; i < other.length; i++) { m[other[i].toLowerCase()] = pal[i % pal.length]; }
    // 当前模式调色板自身映射（幂等）
    for (var j = 0; j < pal.length; j++) { m[pal[j].toLowerCase()] = pal[j]; }
    return m;
  }
  var COLOR_MAP = buildColorMap();
  function rgbaMap() { return currentMode() === "dark" ? RGBA_MAP_DARK : RGBA_MAP_LIGHT; }

  // —— 注册 ECharts 主题 ——
  function registerTheme() {
    var c = colors();
    echarts.registerTheme("swiss", {
      color: c.palette,
      backgroundColor: "transparent",
      textStyle: {
        fontFamily: '"Helvetica Neue",Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif',
        color: c.txt,
      },
      title: {
        textStyle: { color: c.txt, fontWeight: 700, fontSize: 14, letterSpacing: 2 },
        subtextStyle: { color: c.txt2 },
      },
      legend: {
        textStyle: { color: c.txt2, fontSize: 12, fontWeight: 700 },
        itemGap: 20,
      },
      tooltip: {
        backgroundColor: c.tipBg,
        borderColor: c.tipBd,
        borderWidth: 1,
        textStyle: { color: c.txt, fontSize: 12 },
        extraCssText: "box-shadow:none;border-radius:0;",
      },
      categoryAxis: {
        axisLine: { lineStyle: { color: c.line, width: 1 } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontSize: 11, fontWeight: 700 },
        splitLine: { show: false },
        splitArea: { show: false },
      },
      valueAxis: {
        axisLine: { lineStyle: { color: c.line, width: 1 } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontSize: 11, fontWeight: 700 },
        splitLine: { lineStyle: { color: c.split, type: "solid", width: 1 } },
        splitArea: { show: false },
      },
      logAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2 },
        splitLine: { lineStyle: { color: c.split } },
      },
      line: {
        itemStyle: { borderWidth: 2 },
        lineStyle: { width: 2 },
        symbolSize: 6,
        symbol: "circle",
        smooth: false,
      },
      bar: {
        itemStyle: { borderRadius: 0 },
      },
      pie: {
        itemStyle: { borderWidth: 2, borderColor: c.surface, borderRadius: 0 },
      },
    });
  }

  // 首次注册
  registerTheme();

  // —— 拦截 setOption：替换硬编码颜色 ——
  function replaceColors(obj) {
    if (!obj || typeof obj !== "object") return obj;
    if (Array.isArray(obj)) { obj.forEach(replaceColors); return obj; }
    var cm = COLOR_MAP;
    var rm = rgbaMap();
    for (var key in obj) {
      if (!obj.hasOwnProperty(key)) continue;
      var val = obj[key];
      if (typeof val === "string") {
        var lower = val.toLowerCase();
        if (cm[lower]) { obj[key] = cm[lower]; continue; }
        for (var oldP in rm) {
          if (val.indexOf(oldP) === 0) { obj[key] = val.replace(oldP, rm[oldP]); break; }
        }
      } else if (typeof val === "object") {
        replaceColors(val);
      }
    }
    return obj;
  }

  // —— 拦截 echarts.init：自动套用 swiss 主题 ——
  if (!window._echartsOrigInit) window._echartsOrigInit = echarts.init;
  var _origInit = window._echartsOrigInit;
  if (window._themeCleanup) { try { window._themeCleanup(); } catch(e){} window._themeCleanup = null; }
  echarts.init = function (dom, theme, opts) {
    var chart = _origInit.call(this, dom, theme || "swiss", opts);
    var _origSetOption = chart.setOption.bind(chart);
    chart.setOption = function (option, opts2) {
      replaceColors(option);
      return _origSetOption(option, opts2);
    };
    return chart;
  };

  // —— 补丁已存在的图表实例 ——
  var patched = new WeakSet();
  function patchExisting() {
    document.querySelectorAll("[_echarts_instance_]").forEach(function (dom) {
      var chart = echarts.getInstanceByDom(dom);
      if (chart && !patched.has(chart)) {
        patched.add(chart);
        delete chart.setOption;  // 清除可能存在的旧主题拦截器
        var _orig = chart.setOption.bind(chart);
        chart.setOption = function (opt, o2) { replaceColors(opt); return _orig(opt, o2); };
        var cur = chart.getOption();
        if (cur) { replaceColors(cur); _orig(cur, { notMerge: false, lazyUpdate: true }); }
      }
    });
  }

  // 定期检查（覆盖异步渲染的图表）
  function cleanup() {
    try { if (iv) clearInterval(iv); } catch (e) {}
    try { if (obs) obs.disconnect(); } catch (e) {}
    try { if (modeObs) modeObs.disconnect(); } catch (e) {}
    try { if (window._echartsOrigInit) echarts.init = window._echartsOrigInit; } catch (e) {}
    try {
      document.querySelectorAll("[_echarts_instance_]").forEach(function(dom) {
        var c = echarts.getInstanceByDom(dom);
        if (c) delete c.setOption;
      });
    } catch (e) {}
  }
  var n = 0;
  var iv = setInterval(function () { patchExisting(); if (++n >= 20) clearInterval(iv); }, 250);

  // DOM 变化监听
  if (typeof MutationObserver !== "undefined") {
    var obs = new MutationObserver(function () { patchExisting(); });
    obs.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { obs.disconnect(); }, 30000);

    // 监听 data-mode 属性变化 → 切换配色后重新补丁所有图表
    var modeObs = new MutationObserver(function () {
      registerTheme();              // 用新调色板重新注册主题
      COLOR_MAP = buildColorMap();   // 重建颜色映射（含跨模式反向映射）
      patched = new WeakSet();       // 重置已补丁集合，使所有图表重新刷新
      patchExisting();
    });
    modeObs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-mode"] });
  }

  if (typeof cleanup !== "undefined") window._themeCleanup = cleanup;
  console.log("[Swiss Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
