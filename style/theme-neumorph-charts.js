/* ==========================================================================
   Neumorphism 新拟态 — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.5.html
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-neumorph-charts.js"></script>

   原理：
   1. 注册名为 "neumorph" 的 ECharts 主题（响应 data-mode 自动切换 Light/Dark 配色）
   2. 拦截 echarts.init，自动套用该主题
   3. 拦截 setOption，将硬编码的旧配色替换为新拟态配色
   4. 监听 data-mode 属性变化，切换配色后重新补丁所有图表
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  // —— 新拟态配色表 ——
  // Light 调色板
  var N_LIGHT = {
    palette: ["#6c63ff","#8b83ff","#2ecc71","#e74c3c","#f39c12","#9b59b6","#1abc9c","#3498db"],
    txt:     "#333333",
    txt2:    "rgba(51,51,51,0.50)",
    line:    "rgba(51,51,51,0.10)",
    split:   "rgba(51,51,51,0.05)",
    surface: "#e0e5ec",
    tipBg:   "rgba(224,229,236,0.92)",
    tipBd:   "rgba(51,51,51,0.10)",
  };
  // Dark 调色板
  var N_DARK = {
    palette: ["#8b83ff","#a89bff","#2ecc71","#e74c3c","#f39c12","#bb86fc","#4fd8eb","#5dade2"],
    txt:     "#c8ccd4",
    txt2:    "rgba(200,204,212,0.55)",
    line:    "rgba(200,204,212,0.12)",
    split:   "rgba(200,204,212,0.06)",
    surface: "#282c34",
    tipBg:   "rgba(40,44,52,0.92)",
    tipBd:   "rgba(200,204,212,0.15)",
  };

  // —— 旧色 → 新色 映射表（Light）——
  var COLOR_MAP_LIGHT = {
    "#0071e3": "#6c63ff",
    "#2997ff": "#8b83ff",
    "#34c759": "#2ecc71",
    "#ff3b30": "#e74c3c",
    "#ff9f0a": "#f39c12",
    "#5e5ce6": "#9b59b6",
    "#00b8d4": "#1abc9c",
    "#1a7f37": "#27ae60",
    "#c0392b": "#c0392b",
    "#9a6200": "#d68910",
    "#4240c8": "#7d3c98",
    "#0a5fb8": "#2471a3",
  };
  // —— 旧色 → 新色 映射表（Dark）——
  var COLOR_MAP_DARK = {
    "#0071e3": "#8b83ff",
    "#2997ff": "#a89bff",
    "#34c759": "#2ecc71",
    "#ff3b30": "#e74c3c",
    "#ff9f0a": "#f39c12",
    "#5e5ce6": "#bb86fc",
    "#00b8d4": "#4fd8eb",
    "#1a7f37": "#2ecc71",
    "#c0392b": "#e74c3c",
    "#9a6200": "#f39c12",
    "#4240c8": "#bb86fc",
    "#0a5fb8": "#5dade2",
  };
  // —— rgba 前缀映射（Light）——
  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,":   "rgba(108,99,255,",
    "rgba(41,151,255,":  "rgba(139,131,255,",
    "rgba(52,199,89,":   "rgba(46,204,113,",
    "rgba(255,59,48,":   "rgba(231,76,60,",
    "rgba(255,159,10,":  "rgba(243,156,18,",
    "rgba(94,92,230,":   "rgba(155,89,182,",
    "rgba(0,184,212,":   "rgba(26,188,156,",
  };
  // —— rgba 前缀映射（Dark）——
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,":   "rgba(139,131,255,",
    "rgba(41,151,255,":  "rgba(168,155,255,",
    "rgba(52,199,89,":   "rgba(46,204,113,",
    "rgba(255,59,48,":   "rgba(231,76,60,",
    "rgba(255,159,10,":  "rgba(243,156,18,",
    "rgba(94,92,230,":   "rgba(187,134,252,",
    "rgba(0,184,212,":   "rgba(79,216,235,",
  };

  // —— 获取当前模式 ——
  function currentMode() {
    return document.documentElement.getAttribute("data-mode") === "dark" ? "dark" : "light";
  }
  function palette() { return currentMode() === "dark" ? N_DARK.palette : N_LIGHT.palette; }
  function colors() { return currentMode() === "dark" ? N_DARK : N_LIGHT; }
  function buildColorMap() {
    var mode = currentMode();
    var base = mode === "dark" ? COLOR_MAP_DARK : COLOR_MAP_LIGHT;
    var pal = mode === "dark" ? N_DARK.palette : N_LIGHT.palette;
    var other = mode === "dark" ? N_LIGHT.palette : N_DARK.palette;
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
    echarts.registerTheme("neumorph", {
      color: c.palette,
      backgroundColor: "transparent",
      textStyle: {
        fontFamily: '-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei","Segoe UI",sans-serif',
        color: c.txt,
      },
      title: {
        textStyle: { color: c.txt, fontWeight: 600, fontSize: 15 },
        subtextStyle: { color: c.txt2 },
      },
      legend: { textStyle: { color: c.txt2, fontSize: 12 } },
      tooltip: {
        backgroundColor: c.tipBg,
        borderColor: c.tipBd,
        borderWidth: 1,
        textStyle: { color: c.txt, fontSize: 13 },
        extraCssText: "box-shadow:6px 6px 16px rgba(0,0,0,0.10), -4px -4px 12px rgba(255,255,255,0.60);border-radius:16px;",
      },
      categoryAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontSize: 12 },
        splitLine: { show: false },
        splitArea: { show: false },
      },
      valueAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontSize: 12 },
        splitLine: { lineStyle: { color: c.split, type: "dashed" } },
        splitArea: { show: false },
      },
      logAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2 },
        splitLine: { lineStyle: { color: c.split } },
      },
      line: {
        itemStyle: { borderWidth: 2 },
        lineStyle: { width: 3 },
        symbolSize: 7,
        symbol: "circle",
        smooth: true,
      },
      bar: {
        itemStyle: { borderRadius: [8, 8, 0, 0] },
      },
      pie: {
        itemStyle: { borderWidth: 3, borderColor: c.surface, borderRadius: 8 },
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

  // —— 拦截 echarts.init：自动套用 neumorph 主题 ——
  if (!window._echartsOrigInit) window._echartsOrigInit = echarts.init;
  var _origInit = window._echartsOrigInit;
  if (window._themeCleanup) { try { window._themeCleanup(); } catch(e){} window._themeCleanup = null; }
  echarts.init = function (dom, theme, opts) {
    var chart = _origInit.call(this, dom, theme || "neumorph", opts);
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
  console.log("[Neumorph Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
