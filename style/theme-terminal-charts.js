/* ==========================================================================
   Terminal 终端风格 — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.6.html
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-terminal-charts.js"></script>

   原理：
   1. 注册名为 "terminal" 的 ECharts 主题（响应 data-mode 自动切换 Light/Dark 配色）
   2. 拦截 echarts.init，自动套用该主题
   3. 拦截 setOption，将硬编码的旧配色替换为终端绿配色
   4. 监听 data-mode 属性变化，切换配色后重新补丁所有图表
   5. 当主题被切换（script 标签移除）时自动停止活动，避免跨主题干扰
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  var THEME = "terminal";
  var FONT = '"Cascadia Code","JetBrains Mono",Consolas,"Courier New",monospace';

  // —— 配色表 ——
  var C_LIGHT = {
    palette: ["#0a7d33","#0f9d4a","#b8860b","#c0392b","#6a5acd","#0a7d33","#7b00ff","#00899e"],
    txt: "#1a2e1a", txt2: "rgba(26,46,26,0.55)",
    line: "rgba(26,46,26,0.15)", split: "rgba(26,46,26,0.06)",
    surface: "#fbfbf2", tipBg: "rgba(251,251,242,0.96)", tipBd: "#9db39d",
  };
  var C_DARK = {
    palette: ["#4af78e","#6affab","#ffb000","#ff5555","#b39ddb","#4af78e","#ec4899","#14b8a6"],
    txt: "#c9dcc9", txt2: "rgba(201,220,201,0.55)",
    line: "rgba(201,220,201,0.18)", split: "rgba(201,220,201,0.08)",
    surface: "#0c140c", tipBg: "rgba(12,20,12,0.94)", tipBd: "#233223",
  };

  // —— 旧色 → 新色（基础映射，按模式）——
  var COLOR_MAP_LIGHT = {
    "#0071e3": "#0a7d33", "#2997ff": "#0f9d4a", "#34c759": "#0f9d4a", "#ff3b30": "#c0392b",
    "#ff9f0a": "#b8860b", "#5e5ce6": "#6a5acd", "#00b8d4": "#00899e", "#1a7f37": "#0a7d33",
    "#c0392b": "#c0392b", "#9a6200": "#b8860b", "#4240c8": "#7b00ff", "#0a5fb8": "#00899e",
  };
  var COLOR_MAP_DARK = {
    "#0071e3": "#4af78e", "#2997ff": "#14b8a6", "#34c759": "#6affab", "#ff3b30": "#ff5555",
    "#ff9f0a": "#ffb000", "#5e5ce6": "#b39ddb", "#00b8d4": "#14b8a6", "#1a7f37": "#4af78e",
    "#c0392b": "#ff5555", "#9a6200": "#ffb000", "#4240c8": "#ec4899", "#0a5fb8": "#14b8a6",
  };
  // —— rgba 前缀映射（按模式）——
  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,":  "rgba(10,125,51,",
    "rgba(41,151,255,": "rgba(15,157,74,",
    "rgba(52,199,89,":  "rgba(15,157,74,",
    "rgba(255,59,48,":  "rgba(192,57,43,",
    "rgba(255,159,10,": "rgba(184,134,11,",
    "rgba(94,92,230,":  "rgba(106,90,205,",
    "rgba(0,184,212,":  "rgba(0,137,158,",
  };
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,":  "rgba(74,247,142,",
    "rgba(41,151,255,": "rgba(20,184,166,",
    "rgba(52,199,89,":  "rgba(106,255,171,",
    "rgba(255,59,48,":  "rgba(255,85,85,",
    "rgba(255,159,10,": "rgba(255,176,0,",
    "rgba(94,92,230,":  "rgba(179,157,219,",
    "rgba(0,184,212,":  "rgba(20,184,166,",
  };

  // —— 获取当前模式 ——
  function currentMode() {
    return document.documentElement.getAttribute("data-mode") === "dark" ? "dark" : "light";
  }
  function colors() { return currentMode() === "dark" ? C_DARK : C_LIGHT; }
  function rgbaMap() { return currentMode() === "dark" ? RGBA_MAP_DARK : RGBA_MAP_LIGHT; }

  // 合并：基础映射 + 跨模式调色板互转 + 当前调色板幂等
  // 跨模式互转保证切换 data-mode 后，已渲染图表中残留的旧模式配色也能被重映射
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
        textStyle: { color: c.txt, fontWeight: 700, fontFamily: FONT },
        subtextStyle: { color: c.txt2, fontFamily: FONT },
      },
      legend: { textStyle: { color: c.txt2, fontFamily: FONT } },
      tooltip: {
        backgroundColor: c.tipBg,
        borderColor: c.tipBd,
        borderWidth: 1,
        textStyle: { color: c.txt, fontFamily: FONT, fontSize: 12 },
        extraCssText: "border-radius:0;box-shadow:none;",
      },
      categoryAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontFamily: FONT, fontSize: 11 },
        splitLine: { show: false },
        splitArea: { show: false },
      },
      valueAxis: {
        axisLine: { lineStyle: { color: c.line } },
        axisTick: { lineStyle: { color: c.line } },
        axisLabel: { color: c.txt2, fontFamily: FONT, fontSize: 11 },
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
        lineStyle: { width: 2 },
        symbolSize: 6,
        symbol: "circle",
        smooth: false,
      },
      bar: { itemStyle: { borderRadius: 0 } },
      pie: { itemStyle: { borderWidth: 2, borderColor: c.surface, borderRadius: 0 } },
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

  // —— 拦截 echarts.init：自动套用 terminal 主题 ——
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
  console.log("[Terminal Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
