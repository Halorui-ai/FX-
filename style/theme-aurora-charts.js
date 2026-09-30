/* ==========================================================================
   Aurora 极光玻璃 — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.6.html
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-aurora-charts.js"></script>

   原理：
   1. 注册名为 "aurora" 的 ECharts 主题（响应 data-mode 自动切换 Light/Dark 配色）
   2. 拦截 echarts.init，自动套用该主题
   3. 拦截 setOption，将硬编码的旧配色替换为极光紫青配色
   4. 监听 data-mode 属性变化，切换配色后重新补丁所有图表
   5. 当主题被切换（script 标签移除）时自动停止活动，避免跨主题干扰
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  var THEME = "aurora";
  var FONT = '-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Microsoft YaHei","Segoe UI",sans-serif';

  // —— 配色表 ——
  var C_LIGHT = {
    palette: ["#7c5cff","#22d3ee","#10b981","#f59e0b","#f43f5e","#8b5cf6","#ec4899","#14b8a6"],
    txt: "#16121f", txt2: "rgba(22,18,31,0.55)",
    line: "rgba(22,18,31,0.12)", split: "rgba(22,18,31,0.06)",
    surface: "#ffffff", tipBg: "rgba(255,255,255,0.85)", tipBd: "rgba(139,92,246,0.30)",
  };
  var C_DARK = {
    palette: ["#a78bfa","#67e8f9","#34d399","#fbbf24","#fb7185","#a78bfa","#f472b6","#2dd4bf"],
    txt: "#eceaf4", txt2: "rgba(236,234,244,0.55)",
    line: "rgba(236,234,244,0.14)", split: "rgba(236,234,244,0.06)",
    surface: "#0e0e16", tipBg: "rgba(14,14,22,0.90)", tipBd: "rgba(167,139,250,0.30)",
  };

  // —— 旧色 → 新色（基础映射，按模式）——
  var COLOR_MAP_LIGHT = {
    "#0071e3": "#7c5cff", "#2997ff": "#22d3ee", "#34c759": "#10b981", "#ff3b30": "#f43f5e",
    "#ff9f0a": "#f59e0b", "#5e5ce6": "#8b5cf6", "#00b8d4": "#14b8a6", "#1a7f37": "#10b981",
    "#c0392b": "#f43f5e", "#9a6200": "#f59e0b", "#4240c8": "#8b5cf6", "#0a5fb8": "#14b8a6",
  };
  var COLOR_MAP_DARK = {
    "#0071e3": "#a78bfa", "#2997ff": "#67e8f9", "#34c759": "#34d399", "#ff3b30": "#fb7185",
    "#ff9f0a": "#fbbf24", "#5e5ce6": "#a78bfa", "#00b8d4": "#2dd4bf", "#1a7f37": "#34d399",
    "#c0392b": "#fb7185", "#9a6200": "#fbbf24", "#4240c8": "#f472b6", "#0a5fb8": "#2dd4bf",
  };
  // —— rgba 前缀映射（按模式）——
  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,":  "rgba(124,92,255,",
    "rgba(41,151,255,": "rgba(34,211,238,",
    "rgba(52,199,89,":  "rgba(16,185,129,",
    "rgba(255,59,48,":  "rgba(244,63,94,",
    "rgba(255,159,10,": "rgba(245,158,11,",
    "rgba(94,92,230,":  "rgba(139,92,246,",
    "rgba(0,184,212,":  "rgba(20,184,166,",
  };
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,":  "rgba(167,139,250,",
    "rgba(41,151,255,": "rgba(103,232,249,",
    "rgba(52,199,89,":  "rgba(52,211,153,",
    "rgba(255,59,48,":  "rgba(251,113,133,",
    "rgba(255,159,10,": "rgba(251,191,36,",
    "rgba(94,92,230,":  "rgba(167,139,250,",
    "rgba(0,184,212,":  "rgba(45,212,191,",
  };

  // —— 获取当前模式 ——
  function currentMode() {
    return document.documentElement.getAttribute("data-mode") === "dark" ? "dark" : "light";
  }
  function colors() { return currentMode() === "dark" ? C_DARK : C_LIGHT; }
  function rgbaMap() { return currentMode() === "dark" ? RGBA_MAP_DARK : RGBA_MAP_LIGHT; }

  // 合并：基础映射 + 跨模式调色板互转 + 当前调色板幂等
  function buildColorMap() {
    var mode = currentMode();
    var base = mode === "dark" ? COLOR_MAP_DARK : COLOR_MAP_LIGHT;
    var pal = mode === "dark" ? C_DARK.palette : C_LIGHT.palette;
    var other = mode === "dark" ? C_LIGHT.palette : C_DARK.palette;
    var m = {};
    for (var k in base) { if (base.hasOwnProperty(k)) m[k.toLowerCase()] = base[k]; }
    for (var i = 0; i < other.length; i++) { m[other[i].toLowerCase()] = pal[i % pal.length]; }
    for (var j = 0; j < pal.length; j++) { m[pal[j].toLowerCase()] = pal[j]; }
    return m;
  }
  var COLOR_MAP = buildColorMap();

  // —— 注册 ECharts 主题 ——
  function registerTheme() {
    var c = colors();
    echarts.registerTheme(THEME, {
      color: c.palette,
      backgroundColor: "transparent",
      textStyle: { fontFamily: FONT, color: c.txt },
      title: {
        textStyle: { color: c.txt, fontWeight: 600, fontFamily: FONT },
        subtextStyle: { color: c.txt2, fontFamily: FONT },
      },
      legend: { textStyle: { color: c.txt2, fontFamily: FONT } },
      tooltip: {
        backgroundColor: c.tipBg,
        borderColor: c.tipBd,
        borderWidth: 1,
        textStyle: { color: c.txt, fontFamily: FONT, fontSize: 13 },
        extraCssText: "border-radius:12px;backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 8px 28px rgba(139,92,246,0.22);",
      },
      categoryAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontFamily: FONT, fontSize: 12 },
        splitLine: { show: false },
        splitArea: { show: false },
      },
      valueAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontFamily: FONT, fontSize: 12 },
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
      bar: { itemStyle: { borderRadius: [8, 8, 0, 0] } },
      pie: { itemStyle: { borderWidth: 3, borderColor: c.surface, borderRadius: 10 } },
      radar: {
        axisName: { color: c.txt2 },
        splitLine: { lineStyle: { color: c.split } },
        axisLine: { lineStyle: { color: c.line } },
      },
    });
  }
  registerTheme();

  // —— 拦截 setOption：替换硬编码颜色 ——
  function replaceColors(obj) {
    if (!obj || typeof obj !== "object") return obj;
    if (Array.isArray(obj)) { obj.forEach(replaceColors); return obj; }
    var cm = COLOR_MAP, rm = rgbaMap();
    for (var key in obj) {
      if (!obj.hasOwnProperty(key)) continue;
      var val = obj[key];
      if (typeof val === "string") {
        var lower = val.toLowerCase();
        if (cm[lower]) { obj[key] = cm[lower]; continue; }
        for (var p in rm) {
          if (rm.hasOwnProperty(p) && val.indexOf(p) === 0) { obj[key] = val.replace(p, rm[p]); break; }
        }
      } else if (typeof val === "object") {
        replaceColors(val);
      }
    }
    return obj;
  }

  // —— 拦截 echarts.init：自动套用 aurora 主题 ——
  if (!window._echartsOrigInit) window._echartsOrigInit = echarts.init;
  var _origInit = window._echartsOrigInit;
  if (window._themeCleanup) { try { window._themeCleanup(); } catch(e){} window._themeCleanup = null; }
  echarts.init = function (dom, theme, opts) {
    var chart = _origInit.call(this, dom, theme || THEME, opts);
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

  // —— 自清理：主题被切换时（script 标签被移除）停止活动 ——
  var myScript = (typeof document !== "undefined" && document.currentScript) ? document.currentScript : null;
  function removed() { return myScript && !myScript.parentNode; }
  var iv, obs, modeObs;
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

  // 定期补丁（5s 内检测 20 次，覆盖异步渲染的图表）
  var n = 0;
  iv = setInterval(function () {
    if (removed()) { cleanup(); return; }
    patchExisting();
    if (++n >= 20) clearInterval(iv);
  }, 250);

  // DOM 变化监听（30s）
  if (typeof MutationObserver !== "undefined") {
    obs = new MutationObserver(function () { if (removed()) { cleanup(); return; } patchExisting(); });
    obs.observe(document.body || document.documentElement, { childList: true, subtree: true });
    setTimeout(function () { try { obs.disconnect(); } catch (e) {} }, 30000);

    // 监听 data-mode 属性变化 → 重新注册主题 + 重建映射 + 重新补丁
    modeObs = new MutationObserver(function () {
      if (removed()) { cleanup(); return; }
      registerTheme();
      COLOR_MAP = buildColorMap();
      patched = new WeakSet();
      patchExisting();
    });
    modeObs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-mode"] });
  }

  if (typeof cleanup !== "undefined") window._themeCleanup = cleanup;
  console.log("[Aurora Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
