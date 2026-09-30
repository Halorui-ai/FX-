/* ==========================================================================
   主题 4：Apple 液态玻璃 (glass) — ECharts 图表主题适配
   适用：dashboard-release-monitor-v5.6.html（data-theme + data-mode 属性系统）
   用法：在 </body> 之前、所有业务脚本之后添加：
   <script src="./style/theme-glass-charts.js"></script>

   原理：
   1. 检测当前 data-mode（light / dark），动态选择配色
   2. 注册名为 "glass" 的 ECharts 主题（含 light / dark 两套配置）
   3. 拦截 echarts.init，自动套用主题；拦截 setOption，替换硬编码颜色
   4. 补丁已存在的图表实例（setInterval 250ms × 20 + MutationObserver 30s）
   5. 监听 data-mode 属性变化，自动刷新所有图表配色
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  // —— 当前模式检测 ——
  function currentMode() {
    var m = document.documentElement.getAttribute("data-mode")
      || (document.body && document.body.getAttribute("data-mode"));
    return m === "dark" ? "dark" : "light";
  }

  // —— Glass 配色表 ——
  var LIGHT = {
    palette: ["#0071e3", "#2997ff", "#34c759", "#ff3b30", "#ff9f0a", "#5e5ce6", "#00b8d4", "#ff2d92"],
    txt: "#1d1d1f",
    txt2: "rgba(0,0,0,0.50)",
    line: "rgba(0,0,0,0.08)",
    split: "rgba(0,0,0,0.05)",
    surface: "rgba(255,255,255,0.92)",
    border: "#d2d2d7",
    fontFamily: '-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif',
  };
  var DARK = {
    palette: ["#58a6ff", "#79c0ff", "#3fb950", "#f85149", "#d29922", "#bc8cff", "#39d2e0", "#ff7b72"],
    txt: "#e6edf3",
    txt2: "rgba(255,255,255,0.55)",
    line: "rgba(255,255,255,0.12)",
    split: "rgba(255,255,255,0.06)",
    surface: "rgba(22,27,34,0.92)",
    border: "rgba(255,255,255,0.12)",
    fontFamily: '-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Helvetica Neue","Microsoft YaHei",sans-serif',
  };

  function cfg() { return currentMode() === "dark" ? DARK : LIGHT; }

  // —— 旧色（dashboard 默认配色）→ 新色 映射表（根据 mode 动态） ——
  // 旧色源：#0071e3,#2997ff,#34c759,#ff3b30,#ff9f0a,#5e5ce6,#00b8d4,#ff2d92
  var OLD_COLORS = ["#0071e3", "#2997ff", "#34c759", "#ff3b30", "#ff9f0a", "#5e5ce6", "#00b8d4", "#ff2d92"];

  function getColorMap() {
    var mode = currentMode();
    var newColors = mode === "dark" ? DARK.palette : LIGHT.palette;
    var otherColors = mode === "dark" ? LIGHT.palette : DARK.palette;
    var map = {};
    OLD_COLORS.forEach(function (c, i) { map[c.toLowerCase()] = newColors[i].toLowerCase(); });
    // 跨模式反向映射：将另一模式的调色板颜色映射回当前模式
    otherColors.forEach(function (c, i) { map[c.toLowerCase()] = newColors[i].toLowerCase(); });
    // 当前模式调色板自身映射（幂等）
    newColors.forEach(function (c) { map[c.toLowerCase()] = c.toLowerCase(); });
    // 额外兼容色
    var extra = mode === "dark"
      ? { "#30b0c7": "#39d2e0", "#af52de": "#bc8cff", "#ff9500": "#d29922", "#ff2d55": "#ff7b72" }
      : { "#30b0c7": "#00b8d4", "#af52de": "#ff2d92", "#ff9500": "#ff9f0a", "#ff2d55": "#ff2d92" };
    for (var k in extra) map[k.toLowerCase()] = extra[k].toLowerCase();
    return map;
  }

  var RGBA_MAP_LIGHT = {
    "rgba(0,113,227,": "rgba(0,113,227,",
    "rgba(41,151,255,": "rgba(41,151,255,",
    "rgba(52,199,89,": "rgba(52,199,89,",
    "rgba(255,59,48,": "rgba(255,59,48,",
    "rgba(255,159,10,": "rgba(255,159,10,",
    "rgba(94,92,230,": "rgba(94,92,230,",
    "rgba(0,184,212,": "rgba(0,184,212,",
  };
  var RGBA_MAP_DARK = {
    "rgba(0,113,227,": "rgba(88,166,255,",
    "rgba(41,151,255,": "rgba(121,192,255,",
    "rgba(52,199,89,": "rgba(63,185,80,",
    "rgba(255,59,48,": "rgba(248,81,73,",
    "rgba(255,159,10,": "rgba(210,153,34,",
    "rgba(94,92,230,": "rgba(188,140,255,",
    "rgba(0,184,212,": "rgba(57,210,224,",
  };
  function getRgbaMap() { return currentMode() === "dark" ? RGBA_MAP_DARK : RGBA_MAP_LIGHT; }

  // —— 构建 ECharts 主题配置 ——
  function buildThemeOption(mode) {
    var c = (mode || currentMode()) === "dark" ? DARK : LIGHT;
    return {
      color: c.palette,
      backgroundColor: "transparent",
      textStyle: { fontFamily: c.fontFamily, color: c.txt },
      title: {
        textStyle: { color: c.txt, fontWeight: 600, fontSize: 15 },
        subtextStyle: { color: c.txt2 },
      },
      legend: { textStyle: { color: c.txt2, fontSize: 12 } },
      tooltip: {
        backgroundColor: c.surface,
        borderColor: c.border,
        borderWidth: 1,
        textStyle: { color: c.txt, fontSize: 13 },
        extraCssText: "box-shadow:0 8px 24px -6px rgba(0,0,0,0.12);border-radius:12px;backdrop-filter:blur(20px);",
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
      line: {
        itemStyle: { borderWidth: 2 },
        lineStyle: { width: 3 },
        symbolSize: 7,
        symbol: "circle",
        smooth: true,
      },
      bar: { itemStyle: { borderRadius: [6, 6, 0, 0] } },
      pie: { itemStyle: { borderWidth: 3, borderColor: c.surface, borderRadius: 6 } },
    };
  }

  // —— 注册主题（light + dark 两套，直接传 mode 参数，不修改 data-mode 属性） ——
  function registerThemes() {
    echarts.registerTheme("glass", buildThemeOption("light"));
    echarts.registerTheme("glass-dark", buildThemeOption("dark"));
  }
  registerThemes();

  // —— 颜色替换函数 ——
  function replaceColors(obj) {
    if (!obj || typeof obj !== "object") return obj;
    var colorMap = getColorMap();
    var rgbaMap = getRgbaMap();
    if (Array.isArray(obj)) { obj.forEach(replaceColors); return obj; }
    for (var key in obj) {
      if (!obj.hasOwnProperty(key)) continue;
      var val = obj[key];
      if (typeof val === "string") {
        var lower = val.toLowerCase();
        if (colorMap[lower]) { obj[key] = colorMap[lower]; continue; }
        for (var oldP in rgbaMap) {
          if (val.indexOf(oldP) === 0) { obj[key] = val.replace(oldP, rgbaMap[oldP]); break; }
        }
      } else if (typeof val === "object") {
        replaceColors(val);
      }
    }
    return obj;
  }

  // —— 拦截 echarts.init：自动套用 glass 主题 ——
  if (!window._echartsOrigInit) window._echartsOrigInit = echarts.init;
  var _origInit = window._echartsOrigInit;
  if (window._themeCleanup) { try { window._themeCleanup(); } catch(e){} window._themeCleanup = null; }
  echarts.init = function (dom, theme, opts) {
    var themeName = theme || (currentMode() === "dark" ? "glass-dark" : "glass");
    var chart = _origInit.call(this, dom, themeName, opts);
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
  if (typeof MutationObserver !== "undefined") {
    var obs = new MutationObserver(function () { patchExisting(); });
    obs.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { obs.disconnect(); }, 30000);
  }

  // —— 监听 data-mode 属性变化：刷新所有图表配色 ——
  function refreshAllCharts() {
    // 重新注册主题（配色随 mode 变化）
    registerThemes();
    document.querySelectorAll("[_echarts_instance_]").forEach(function (dom) {
      var chart = echarts.getInstanceByDom(dom);
      if (chart) {
        var cur = chart.getOption();
        if (cur) {
          replaceColors(cur);
          chart.setOption(cur, { notMerge: false, lazyUpdate: true });
        }
      }
    });
  }
  var _modeRefreshing = false;
  if (typeof MutationObserver !== "undefined") {
    var modeObs = new MutationObserver(function (mutations) {
      if (_modeRefreshing) return;
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].attributeName === "data-mode") {
          _modeRefreshing = true;
          try { refreshAllCharts(); } finally { _modeRefreshing = false; }
          break;
        }
      }
    });
    modeObs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-mode"] });
    if (document.body) {
      modeObs.observe(document.body, { attributes: true, attributeFilter: ["data-mode"] });
    }
  }

  if (typeof cleanup !== "undefined") window._themeCleanup = cleanup;
  console.log("[Glass Theme] ECharts 主题已注入（data-mode=" + currentMode() + "）。");
})();
