/* ==========================================================================
   Claymorphism 粘土拟态 — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.5.html
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-clay-charts.js"></script>

   原理：
   1. 注册名为 "clay" 的 ECharts 主题（响应 data-mode 自动切换 Light/Dark 配色）
   2. 拦截 echarts.init，自动套用该主题
   3. 拦截 setOption，将硬编码的旧配色替换为粘土拟态配色
   4. 监听 data-mode 属性变化，切换配色后重新补丁所有图表
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  // —— 粘土拟态配色表 ——
  // Light 调色板
  var C_LIGHT = {
    palette: ["#e8590c","#f76707","#2f9e44","#e03131","#f08c00","#9c36b5","#0c8599","#d6336c"],
    txt:     "#3d2c1e",
    txt2:    "rgba(61,44,30,0.55)",
    line:    "rgba(61,44,30,0.10)",
    split:   "rgba(61,44,30,0.05)",
    surface: "#fef9f0",
    tipBg:   "rgba(255,245,230,0.92)",
    tipBd:   "rgba(255,180,100,0.30)",
  };
  // Dark 调色板
  var C_DARK = {
    palette: ["#ff8c42","#ffa94d","#51cf66","#ff6b6b","#fcc419","#cc5de8","#22b8cf","#f06595"],
    txt:     "#fde8d0",
    txt2:    "rgba(253,232,208,0.55)",
    line:    "rgba(253,232,208,0.12)",
    split:   "rgba(253,232,208,0.06)",
    surface: "#261a14",
    tipBg:   "rgba(38,26,20,0.92)",
    tipBd:   "rgba(255,180,100,0.20)",
  };

  // —— 旧色 → 新色 映射表（Light）——
  var COLOR_MAP_LIGHT = {
    "#0071e3": "#e8590c",
    "#2997ff": "#f76707",
    "#34c759": "#2f9e44",
    "#ff3b30": "#e03131",
    "#ff9f0a": "#f08c00",
    "#5e5ce6": "#9c36b5",
    "#00b8d4": "#0c8599",
    "#1a7f37": "#2f9e44",
    "#c0392b": "#e03131",
    "#9a6200": "#d9480f",
    "#4240c8": "#9c36b5",
    "#0a5fb8": "#0c8599",
  };
  // —— 旧色 → 新色 映射表（Dark）——
  var COLOR_MAP_DARK = {
    "#0071e3": "#ff8c42",
    "#2997ff": "#ffa94d",
    "#34c759": "#51cf66",
    "#ff3b30": "#ff6b6b",
    "#ff9f0a": "#fcc419",
    "#5e5ce6": "#cc5de8",
    "#00b8d4": "#22b8cf",
    "#1a7f37": "#51cf66",
    "#c0392b": "#ff6b6b",
    "#9a6200": "#fcc419",
    "#4240c8": "#cc5de8",
    "#0a5fb8": "#22b8cf",
  };
  // —— rgba 前缀映射（Light）——
  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,":   "rgba(232,89,12,",
    "rgba(41,151,255,":  "rgba(247,103,7,",
    "rgba(52,199,89,":   "rgba(47,158,68,",
    "rgba(255,59,48,":   "rgba(224,49,49,",
    "rgba(255,159,10,":  "rgba(240,140,0,",
    "rgba(94,92,230,":   "rgba(156,54,181,",
    "rgba(0,184,212,":   "rgba(12,133,153,",
  };
  // —— rgba 前缀映射（Dark）——
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,":   "rgba(255,140,66,",
    "rgba(41,151,255,":  "rgba(255,169,77,",
    "rgba(52,199,89,":   "rgba(81,207,102,",
    "rgba(255,59,48,":   "rgba(255,107,107,",
    "rgba(255,159,10,":  "rgba(252,196,25,",
    "rgba(94,92,230,":   "rgba(204,93,232,",
    "rgba(0,184,212,":   "rgba(34,184,207,",
  };

  // —— 获取当前模式 ——
  function currentMode() {
    return document.documentElement.getAttribute("data-mode") === "dark" ? "dark" : "light";
  }
  function palette() { return currentMode() === "dark" ? C_DARK.palette : C_LIGHT.palette; }
  function colors() { return currentMode() === "dark" ? C_DARK : C_LIGHT; }
  function buildColorMap() {
    var mode = currentMode();
    var base = mode === "dark" ? COLOR_MAP_DARK : COLOR_MAP_LIGHT;
    var pal = mode === "dark" ? C_DARK.palette : C_LIGHT.palette;
    var other = mode === "dark" ? C_LIGHT.palette : C_DARK.palette;
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
    echarts.registerTheme("clay", {
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
        borderWidth: 2,
        textStyle: { color: c.txt, fontSize: 13 },
        extraCssText: "box-shadow:4px 4px 12px rgba(232,89,12,0.12), -3px -3px 10px rgba(255,255,255,0.50);border-radius:16px;",
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
        itemStyle: { borderRadius: [10, 10, 0, 0] },
      },
      pie: {
        itemStyle: { borderWidth: 3, borderColor: c.surface, borderRadius: 10 },
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

  // —— 拦截 echarts.init：自动套用 clay 主题 ——
  if (!window._echartsOrigInit) window._echartsOrigInit = echarts.init;
  var _origInit = window._echartsOrigInit;
  if (window._themeCleanup) { try { window._themeCleanup(); } catch(e){} window._themeCleanup = null; }
  echarts.init = function (dom, theme, opts) {
    var chart = _origInit.call(this, dom, theme || "clay", opts);
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
  console.log("[Clay Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
