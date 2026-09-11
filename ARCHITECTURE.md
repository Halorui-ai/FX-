# 架构（现行结构 + 如何扩展）

改解析、性能、布局、主题机制，或加卡片 / 主题 / 视图时读本文。口径见 [CONTEXT.md](CONTEXT.md)。已否决的方案见 [DECISIONS.md](DECISIONS.md)。

---

## 1. 总览

单向数据流，全部在浏览器主线程（无后端、无构建、无网络）：

```
用户文件 (.xls/.xlsx/.csv)
  → 解析层     FileReader → XLSX.read 或 PapaParse
               findHeaderRow() 前 20 行定位表头
               firstNonEmptySheet() 跳过空表/汇总页
  → 标准化层   normalizeRow() 分块（5000 行）映射字段、打 _特保/_已到达/_超时
  → 计算层     computeOrders() 按放行单号聚合
               computeStats() 汇总（结果缓存 _statsCache）
  → 渲染层     CARD_DEFS + gridstack + ECharts / Tabulator / countUp
```

渲染层不得修改 `rows` / `orders`。

### 解析线程

| 项 | 现行 |
|----|------|
| 主路径 | 主线程分块（`XLSX.read` + `sheetToRowsChunked`，块间让出 UI） |
| Web Worker | 代码保留，**默认禁用**（`window.__workerDisabled = true`） |
| 原因 | file:// 下 blob Worker 无法 `importScripts` 外部 `xlsx`；内联库方案已回退（D-10） |
| CSV | PapaParse，无需 Worker（10 万行约 1.7s，xlsx 约 20s） |

---

## 2. 技术栈（全部 `./lib/`，禁止 CDN）

原生 JS（ES2020，无框架）。ECharts 5 + liquidFill、SheetJS、PapaParse、dayjs、lodash、countUp、Tabulator、Toastify、html2canvas、FileSaver、gridstack 6。Vue / Sortable 仅预研或归档 v4 使用。

---

## 3. 主文件分区

现行交付物：`dashboard-release-monitor-v5.6.html`（单文件）。

| 区块 | 内容 |
|------|------|
| `<style>` | 默认液态玻璃 + 深色 `[data-mode="dark"]` |
| `<body>` | 顶栏（状态 + 右侧功能抽屉）/ 上传 / 卡片网格 / 卡片库 / 二级详情 |
| `CONFIG` | 字段映射、特保前缀、超时标记、性能阈值（**改业务规则只动这里**） |
| 解析 | `handleFile` / `findHeaderRow` / `firstNonEmptySheet` / `sheetToRowsChunked` |
| Worker（保留未启用） | `PARSER_WORKER_SRC` / `parseViaWorker` |
| 标准化 | `processData` / `normalizeRow` / `mapColumns` |
| 计算 | `computeOrders` / `computeStats` |
| 卡片 | `CARD_DEFS` / `optionBuilders` / `BUILTIN_LAYOUTS` |
| 详情 | `KPI_DETAIL` / `openDetail` |
| 主题 | `THEME_REGISTRY` / `probeThemes` / `applyTheme` / `toggleDarkMode` / `setDrawerOpen` |
| 视图插件 | `VIEW_REGISTRY` / `loadViewPlugins` |
| 演示 | `makeDemoOrder` / `liveTick`（新开单 / 推进门岗 / 到达 / 接收） |
| 背景 | `animBg` / PERF 降级 |

### PERF

读 `deviceMemory` / `hardwareConcurrency`：内存 ≤4GB 或核心 ≤2 → `lite`。手动选择存 `localStorage.perfMode`，优先于自动。lite：静态背景、去毛玻璃、图表 DPR=1、演示降频。切换就地生效，不要 `location.reload()`（file:// 会触发安全警告）。

≥ `CONFIG.大数据量阈值`（30000 行）关 ECharts 动画、Tabulator 虚拟滚动、背景降频。

---

## 4. 布局

gridstack 12 列，行高约 95px。卡片尺寸在 `CARD_DEFS` 用 `w/h/minW/maxW/minH/maxH`。编辑模式才允许拖头 / 缩放 / 删除。`syncLayoutFromGrid()` 从 DOM `gs-*` 回写 `workingLayout`。

内置视图：默认 / 管理层 / 一线 / 运维 / GDMS超时管控。自定义布局存 `localStorage.dashLayouts`，与数据无关。

### 顶栏壳（v5.6）

默认**只显示状态**，不铺一排按钮（D-18）。

| 区域 | 内容 |
|------|------|
| 左 `.tb-identity` | 标题、说明、状态芯片（画质 / 文件信息 / LIVE），芯片同一行同一高度 |
| 右 `#btnDrawer` | 仅圆形箭头；默认收起。点开后箭头旋转，`#toolDrawer` 用 `grid-template-rows: 0fr→1fr` + `cubic-bezier(0.22, 1, 0.36, 1)` 展开 |
| 抽屉内 `.tb-drawer-toolbar` | 深浅色滑块、流畅模式滑块、主题下拉、视图下拉，与暂停刷新 / 导出 / 编辑布局**同一行** |
| 编辑态 | `#editBar` 仍在抽屉内，仅编辑模式显示 |

深浅色 / 性能是 iOS 式 `role="switch"`（`#swDark` / `#swPerf`），打开 = 深色、打开 = 流畅（lite）。标题与顶栏 `#perfTag` 同步。`Esc` 关抽屉。

`#btnDrawer` **不要写死黑底**。空闲态必须跟当前主题的普通按钮走（`html[data-theme=x] button.tb-drawer-btn` 写在各 `style/theme-*.css` 末尾）；悬停略提亮；仅 `aria-expanded="true"` 才用强调色填充。只留图标，不要加「功能」文字。不要改成常驻左侧栏。

---

## 5. 主题与视图插件

主文件内置「默认」液态玻璃。外部主题、外部视图都是可选文件夹；缺失时自动降级，分享单 HTML 仍能用。

**file:// 不能枚举目录**，所以用注册表 + 动态 `<link>`/`<script>` 探测（onload 存在，onerror 跳过）。

### 主题

- 登记：`THEME_REGISTRY`（`id` 下拉名、`theme` = `data-theme` 值、`css` 必填、`js` 可选）
- 探测：只判断 css 是否存在；探测标签带 `data-probe`，完成后移除。**探测阶段不加载图表 JS**（多层拦截 `echarts.init` 会卡死，D-13）
- 探测 5 秒超时保护
- 应用：`html[data-theme]` + `html[data-mode]`；切走时清理旧 link/script、`_themeCleanup`、恢复 `echarts.init`
- 记忆：`localStorage.dashTheme` / `dashMode`
- 现行已注册：Terminal、Aurora、新粗野、液态玻璃、Material3、Fluent、新拟态、粘土、瑞士极简（文件在 `style/`）
- 另有一份 `style/theme-material3.*`：**仅给归档** `docs/archive/versions/dashboard-release-monitor-v5.5.html` 探测用。现行 v5.6 注册的是 `theme-material.*`。不要按这两个文件头部注释（仍写「与 v4.html 同目录硬链」）去导入。

图表配色脚本约定：拦截 `echarts.init` / `setOption`，监听 `data-mode`，被移除时停止，并提供 `_themeCleanup`。

### 视图

- 登记：`VIEW_REGISTRY`
- 文件内：`window.VIEW_PLUGIN = { id, name, layout: [{id,x,y,w,h}, ...] }`
- 编辑栏「导出视图文件」可生成，放入 `views/` 并登记即可分享

---

## 6. 关键运行约束

- `file://` 必须可用；禁止引入必须 HTTP 的能力（除非保留 file:// 兑底）。
- 大 xlsx 的硬瓶颈是 `XLSX.read` 同步阻塞；产品侧引导转存 CSV。
- 派生字段 `_` 前缀，导出前 `stripPrivate()` 剥离。
- 新图表动画走 `withAnim()` / `animOpt()`，大数据与 lite 自动降级。

常见排障（现象 → 先查）：缺必需列 → 别名或表头未识别；解析失败 → 空 Sheet 是否仍被误当成第一张（现行应已跳过）；主题进门就不是默认 → `localStorage.dashTheme` 或探测未标 `data-probe`；卡顿 → 打开右侧功能抽屉，打开「流畅模式」开关。

---

## 7. 如何扩展（原 EXTENSIONS）

本节可随代码改写。口径默认见 CONTEXT；相关禁令见 DECISIONS。

### 7.1 新表头别名 / 必需列

只改主文件顶部 `CONFIG.字段映射`（别名只增不删）、`CONFIG.必需字段`。订单上要带出的新属性在 `computeOrders()` 取首个非空或按规则聚合。

### 7.2 新统计口径

在 `_computeStatsRaw()` 增加字段（自动进缓存）。改口径前搜 DECISIONS；默认订单级。需要详情下钻时在 `KPI_DETAIL` 加 key，卡片设 `detailKey`。

### 7.3 新卡片

往 `CARD_DEFS` 登记即可出现在卡片库，无需改 `renderDashboard`。

```js
CARD_DEFS.my_newCard = {
  id: "my_newCard",
  title: "新指标名称",
  icon: "📈",
  cat: "分布分析",          // KPI指标 / 分布分析 / 趋势分析 / 异常监控 / 明细数据 / GDMS超时管控
  w: 6, h: 3,
  minW: 3, maxW: 12, minH: 2, maxH: 6,
  detailKey: "xxx",          // 可选，对应 KPI_DETAIL
  render(body, ctx) {        // ctx = { S, rows, orders }
    body.innerHTML = '<div class="chart"></div>';
    cardChart("my_newCard", body.firstChild).setOption(optionBuilders.myOption(ctx.S), true);
  },
  update(body, ctx) {        // 演示模式轻量刷新；缺省则重跑 render
    if (liveCharts.my_newCard) liveCharts.my_newCard.setOption(optionBuilders.myOption(ctx.S));
  }
};
```

图表用 `cardChart(id, el)`（纳入 `liveCharts` 生命周期）。KPI 用 `countUp.CountUp` 存 `counters.*`。容器用 `.chart`（宽高 100%）。希望出现在某预设里，往 `BUILTIN_LAYOUTS` 对应数组加 `{id,x,y,w,h}`。

### 7.4 新主题

1. 新增 `style/theme-<key>.css`：选择器 `[data-theme="<key>"][data-mode="light"|"dark"]`，覆盖 CSS 变量。
2. 可选 `style/theme-<key>-charts.js`：按现有 aurora 等脚本的拦截 / 清理约定。
3. 在 `THEME_REGISTRY` **追加一行**（`id`、`theme`、`css`、`js`）。
4. 不要把主题 CSS 内联进主 HTML，不要再复制一份 `dashboard-release-monitor-v5.x-themes.html`。
5. 在该主题 css **末尾**覆盖 `html[data-theme="<key>"] button.tb-drawer-btn` 的空闲 / 悬停 / 展开三态，使圆形箭头跟本主题按钮一致，禁止再写死黑底。

### 7.5 新视图

在看板里排好布局 → 保存或导出。文件格式：

```js
window.VIEW_PLUGIN = {
  id: "myview",
  name: "我的视图",
  layout: [
    { id: "kpi_overview", x: 0, y: 0, w: 2, h: 2 }
  ]
};
```

放入 `views/`，在 `VIEW_REGISTRY` 追加 `{ id, file }`。`file://` 不会自动扫描未登记文件。

### 7.6 演示数据

改业务规则时同步 `makeDemoOrder()`（以及如需测试文件则用 `gen_monitor_data_v3.py`）：分类整单固定、超时标记打末笔、特保前缀 WF9897。
