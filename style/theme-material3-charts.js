/* ==========================================================================
   Material Design 3 — ECharts 图表主题适配
   已废弃作为现行导入方式。v5.6 请用 theme-material-charts.js + THEME_REGISTRY。
   本文件仅保留给 docs/archive/versions/dashboard-release-monitor-v5.5.html。
   ========================================================================== */
(function () {
  "use strict";
  if (typeof echarts === "undefined") return;

  // —— Material 3 配色表 ——
  var M3 = {
    blue:    "#4285F4",
    blueDark:"#3367D6",
    red:     "#EA4335",
    yellow:  "#FBBC05",
    green:   "#34A853",
    purple:  "#5856D6",
    cyan:    "#4285F4",   // Material 3 不用青色，统一归蓝
    pink:    "#AF52DE",
    orange:  "#FF9500",
    teal:    "#00BCD4",
    txt:     "#0e1115",
    txt2:    "rgba(0,0,0,0.55)",
    line:    "rgba(0,0,0,0.14)",
    split:   "rgba(0,0,0,0.06)",
    surface: "#ffffff",
    surfaceV:"#f9f9fa",
  };

  // 图表序列调色板（替换原 PALETTE）
  var M3_PALETTE = [
    M3.blue, M3.green, M3.yellow, M3.red,
    M3.purple, M3.cyan, M3.pink, M3.teal, M3.orange, "#0043AD"
  ];

  // 旧色 → 新色 映射表（用于 setOption 拦截替换）
  var COLOR_MAP = {
    "#0071e3": M3.blue,
    "#2997ff": M3.blueDark,
    "#34c759": M3.green,
    "#ff3b30": M3.red,
    "#ff9f0a": M3.yellow,
    "#5e5ce6": M3.purple,
    "#00b8d4": M3.cyan,
    "#ff2d92": M3.pink,
    "#30b0c7": M3.teal,
    "#af52de": M3.pink,
    "#ff9500": M3.orange,
  };

  // rgba 变体映射（处理渐变中的透明度色）
  var RGBA_MAP = {
    "rgba(0,113,227,": "rgba(66,133,244,",
    "rgba(52,199,89,": "rgba(52,168,83,",
    "rgba(255,59,48,": "rgba(234,67,53,",
    "rgba(255,159,10,": "rgba(251,188,5,",
    "rgba(94,92,230,": "rgba(88,86,214,",
    "rgba(0,184,212,": "rgba(66,133,244,",
  };

  // —— 注册 ECharts 主题 ——
  echarts.registerTheme("material3", {
    color: M3_PALETTE,
    backgroundColor: "transparent",
    textStyle: {
      fontFamily: '"Google Sans","Product Sans","Roboto",-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif',
      color: M3.txt,
    },
    title: {
      textStyle: { color: M3.txt, fontWeight: 500 },
      subtextStyle: { color: M3.txt2 },
    },
    legend: {
      textStyle: { color: M3.txt2 },
    },
    tooltip: {
      backgroundColor: M3.surface,
      borderColor: "#ebebeb",
      borderWidth: 1,
      textStyle: { color: M3.txt },
      extraCssText: "box-shadow:0 4px 12px rgba(0,0,0,0.08);border-radius:8px;",
    },
    categoryAxis: {
      axisLine: { lineStyle: { color: M3.line } },
      axisTick: { lineStyle: { color: M3.line } },
      axisLabel: { color: M3.txt2 },
      splitLine: { show: false },
      splitArea: { show: false },
    },
    valueAxis: {
      axisLine: { lineStyle: { color: M3.line } },
      axisTick: { lineStyle: { color: M3.line } },
      axisLabel: { color: M3.txt2 },
      splitLine: { lineStyle: { color: M3.split } },
      splitArea: { show: false },
    },
    logAxis: {
      axisLine: { lineStyle: { color: M3.line } },
      axisLabel: { color: M3.txt2 },
      splitLine: { lineStyle: { color: M3.split } },
    },
    line: {
      itemStyle: { borderWidth: 2 },
      lineStyle: { width: 3 },
      symbolSize: 6,
      symbol: "circle",
      smooth: true,
    },
    bar: {
      itemStyle: { borderRadius: [4, 4, 0, 0] },
    },
    pie: {
      itemStyle: { borderWidth: 2, borderColor: M3.surface, borderRadius: 4 },
    },
  });

  // —— 拦截 echarts.init：自动套用 material3 主题 ——
  var _origInit = echarts.init;
  echarts.init = function (dom, theme, opts) {
    return _origInit.call(this, dom, theme || "material3", opts);
  };

  // —— 拦截 setOption：替换硬编码颜色 ——
  function replaceColors(obj) {
    if (!obj || typeof obj !== "object") return obj;
    if (Array.isArray(obj)) {
      obj.forEach(replaceColors);
      return obj;
    }
    for (var key in obj) {
      if (!obj.hasOwnProperty(key)) continue;
      var val = obj[key];
      if (typeof val === "string") {
        var lower = val.toLowerCase();
        // 精确匹配
        if (COLOR_MAP[lower]) {
          obj[key] = COLOR_MAP[lower];
          continue;
        }
        // rgba 前缀匹配
        var replaced = false;
        for (var oldPrefix in RGBA_MAP) {
          if (val.indexOf(oldPrefix) === 0) {
            obj[key] = val.replace(oldPrefix, RGBA_MAP[oldPrefix]);
            replaced = true;
            break;
          }
        }
      } else if (typeof val === "object") {
        replaceColors(val);
      }
    }
    return obj;
  }

  var _proto = echarts.Model ? null : null; // placeholder
  // 在所有已创建实例上拦截 setOption
  // 由于无法直接修改原型，使用 MutationObserver 监听图表容器
  // 更可靠的方式：包装 echarts.init 返回的实例
  var _origInit2 = _origInit; // 保持原始引用
  echarts.init = function (dom, theme, opts) {
    var chart = _origInit2.call(this, dom, theme || "material3", opts);
    var _origSetOption = chart.setOption.bind(chart);
    chart.setOption = function (option, opts2) {
      replaceColors(option);
      return _origSetOption(option, opts2);
    };
    return chart;
  };

  // —— 对已存在的图表实例也做补丁（页面加载后可能已有图表）——
  // 使用定期检查的方式，在 5 秒内持续补丁新出现的图表
  var patchedCharts = new WeakSet();
  function patchExistingCharts() {
    // echarts 实例存储在 dom 的 __echarts_instance__ 上
    var containers = document.querySelectorAll("[_echarts_instance_]");
    containers.forEach(function (dom) {
      var chart = echarts.getInstanceByDom(dom);
      if (chart && !patchedCharts.has(chart)) {
        patchedCharts.add(chart);
        var _origSetOption = chart.setOption.bind(chart);
        chart.setOption = function (option, opts2) {
          replaceColors(option);
          return _origSetOption(option, opts2);
        };
        // 触发一次刷新以应用新颜色
        var currentOption = chart.getOption();
        if (currentOption) {
          replaceColors(currentOption);
          _origSetOption(currentOption, { notMerge: false, lazyUpdate: true });
        }
      }
    });
  }

  // 定期检查（覆盖异步渲染的图表）
  var checkCount = 0;
  var maxChecks = 20; // 5 秒内检查 20 次
  var interval = setInterval(function () {
    patchExistingCharts();
    checkCount++;
    if (checkCount >= maxChecks) clearInterval(interval);
  }, 250);

  // 也监听 DOM 变化
  if (typeof MutationObserver !== "undefined") {
    var observer = new MutationObserver(function () {
      patchExistingCharts();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    // 30 秒后停止监听（避免长期性能开销）
    setTimeout(function () { observer.disconnect(); }, 30000);
  }

  console.log("[Material 3 Theme] ECharts 主题已注入，图表配色已自动适配。");
})();
