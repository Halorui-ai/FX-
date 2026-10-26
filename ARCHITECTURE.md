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

### 数据缓存（IndexedDB，v5.6 起）

解析是整条链路最贵的一步（10 万行 xlsx 约 20s），故把 `rows` 留在本机，下次直接恢复（约 1~2s）：

| 项 | 现行 |
|----|------|
| 存储 | IndexedDB `dashCacheData`（`meta` + `rows` 两个 store），**只保留最近一份**（`metaKey: "latest"`） |
| 分块 | 每 2000 行一条记录（`CACHE.chunk`），写入时逐块让出主线程 |
| 序列化 | **`_申请日期/_放行日期/_接收日期` 必须转时间戳**（结构化克隆会丢 dayjs 原型，直接存会让恢复后 `.format()` 报错），读取时用 `dayjs(ts)` 重建 |
| 元数据 | `fileName / savedAt / rowCount / schema / colOf`；`schema` 与 `CACHE.ver` 不符即作废 |
| 写入时机 | `processData()` 渲染完成后异步执行；**演示数据（`demoMode`）不写** |
| 恢复 | `cacheRestore()` 重建 rows + `currentFileName` + `currentColOf`，并按 `_rowId` 最大值复位 `_rowSeq`（防与演示新增行撞 ID），然后 `renderAll()` |
| 开关 | 默认开启，功能抽屉「💾 数据缓存」可关（`localStorage.dashCacheOff`）；关闭时同时清除已留存数据 |
| 降级 | 启动探活 `indexedDB.open()`；不可用/被禁用 → 隐藏恢复入口与开关行，看板功能不受影响 |
| 失败自愈 | 写入配额超限、缓存行数与元数据不符 → 清缓存 + 提示，不污染当前 `rows` |

### 解析线程

| 项 | 现行 |
|----|------|
| 主路径 | 主线程分块（`XLSX.read` + `sheetToRowsChunked`，块间让出 UI） |
| Web Worker | 代码保留，**默认禁用**（`window.__workerDisabled = true`） |
| 原因 | file:// 下 blob Worker 无法 `importScripts` 外部 `xlsx`；内联库方案已回退（D-10） |
| xlsx 取址 | `decode_range` 行号 0 起，拼单元格地址时 +1（或用 `encode_cell`）；主线程与 Worker 一致 |
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
| 数据缓存 | `CACHE` / `cacheSave` / `cacheRestore` / `cacheClear` / `renderCacheRestore`（IndexedDB，只留最近一份） |
| 计算 | `computeOrders` / `computeStats` |
| 卡片 | `CARD_DEFS` / `optionBuilders` / `BUILTIN_LAYOUTS` |
| 详情 | `KPI_DETAIL` / `openDetail` |
| 单据追踪 | `openTrace` / `renderTrace` / `renderTraceAxis` / `renderTraceTable` / `traceNodes` / `traceState`（纵向时间轴；与详情共用 `#detailOverlay`，靠 `.trace-mode` 切换宽度与容器） |
| 主题 | `THEME_REGISTRY` / `probeThemes` / `applyTheme` / `toggleDarkMode` / `setDrawerOpen` |
| 视图插件 | `VIEW_REGISTRY` / `loadViewPlugins` |
| 演示 | `makeDemoOrder` / `liveTick`（新开单 / 推进门岗 / 到达 / 接收） |
| 背景 | `animBg` / PERF 降级 |

### PERF

读 `deviceMemory` / `hardwareConcurrency`：内存 ≤4GB 或核心 ≤2 → `lite`。手动选择存 `localStorage.perfMode`，优先于自动。lite：静态背景、去毛玻璃、图表 DPR=1、演示降频。切换就地生效，不要 `location.reload()`（file:// 会触发安全警告）。

≥ `CONFIG.大数据量阈值`（30000 行）关 ECharts 动画、Tabulator 虚拟滚动、背景降频。

---

## 4. 布局

gridstack **24 列**，行高 **48px**（`GRID_COLS` / `GRID_CELL_H`）。相对旧 12 列 × 95px：横向、竖向步进都细一倍。卡片尺寸在 `CARD_DEFS` 用 `w/h/minW/maxW/minH/maxH`（默认 KPI 为 `4×4`，视觉约等于旧 `2×2`）。编辑模式才允许拖头 / 缩放 / 删除。`syncLayoutFromGrid()` 从 DOM `gs-*` 回写 `workingLayout`。

**列制迁移只做一次，之后只认标记（D-30）**：旧 12 列布局的 `x/y/w/h` ×2 由 `ensureLayoutV24` 完成，只在两个入口调用——`loadLayoutState()` 按 `localStorage.dashLayouts.gridCols` 标记迁移 `custom`；`loadViewPlugins()` 按插件 `cols` 标记迁移外部视图。`getLayoutByName()` 只复制返回，**不得**再按 `x+w ≤ 12` 推断列制（24 列制下半宽 / 左半边布局的右边界本就 ≤ 12，再乘一次即被放大）。

四张业务 KPI（总数 / 特保 / 在途超时 / 超时未接收）按网格 `w×h` 分档。拖拽缩放时按当前格数即时换模板，并用虚线框出下一档要占的格子范围（锚在卡片左上角），松手后虚线消失。数据一律 `buildKpiProps(id, computeStats())`，禁止写死演示数字。结案率 `kpi_rate`：S 仍为 liquid 水球；M/L 按 `docs/prototypes/completion-rate-card/HANDOFF.md`（水球+三指标 / 三栏+Tab），字段来自 `computeStats` 扩展与 `buildKpiProps('kpi_rate')`。

| 档 | 条件（24 列） | 卡片内 |
|----|------|--------|
| S compact | 高 ≤4（默认 `4×4`；很宽但只有 4 行仍是小卡） | 现状：标题区 + 单个核心数字（不动） |
| M cozy | `h≥5` | HANDOFF 中卡：主数字+单位+副说明、右侧微图形（双环/进度环/堆叠条/告警章）、底 3 指标或 CTA。矮中卡图形随栏高缩小 |
| L expanded | `w≥10` 且 `h≥6` | HANDOFF 大卡：左指标条、中维度环图（Tab 切换）、右最新 4 条记录。环图与主数字随栏缩放；滚动只在右栏记录区。点空白/「全部 N 条」打开现有二级详情 |

点 `.kpi-seg` 不打开详情。规格见 `kpi-card-redesign/HANDOFF.md`。

结案率 `kpi_rate` 同档位阈值；S=liquid 水球（默认常为 8×4 仍 compact）；M=左水球（随栏高缩放）+右三指标+底注；L=水球图例|进度条|待关注列表，三栏按比例变宽，Tab「总览/特保/非特保」在标题右侧。四张业务大卡中栏为引导线大环，图例横排。编辑态四角角标内收，对齐卡片 16px 圆角。大卡右栏滚动条用 `--sb-size` / `--sb-radius` / `--sb-thumb`，随主题变。

内置视图：默认 / 管理层 / 一线 / 运维 / GDMS超时管控。自定义布局存 `localStorage.dashLayouts`，与数据无关。卡 A/B（`chart_gate_stuck` / `chart_gate_load`）已放入默认、一线、运维、GDMS，不在管理层精简视图里。KPI 自适应档位见上一小节。

### 状态色语义（D-33）

**放行类超时一律红，接收类超时一律黄** —— 全看板统一。新增卡片 / 图表 / 告警一律按此选色：

| 状态 | 色 | 说明 |
|------|-----|------|
| 在途超时 / 到达超时 / 放行超时 / 放行异常 | `--bad` 红 | 放行类；**在途超时最严重** |
| 超时未接收 / 已接收但接收超时 | `--warn` 黄 | 接收类 |
| 正常 / 已接收 | `--ok` 绿 | — |
| 特级安保单（WF9897） | `--cat-purple` 紫 | — |

- 落点：`kpi_transit` / `kpi_receive` 的 `tone` 与卡片 `color`、结案率大卡「到达超时」、`chart_status` 两扇区、`gdmsDuration` 时长分桶（红系四级）、两个超时下钻的 chips 与柱图、`alert_transit` / `alert_receive` 的标签与计数。
- 泛称「总超时」（放行 ∪ 接收）保持中性橙；特保分类与图表分类调色板（`PALETTE`）不受本表约束。
- 接收类时长分桶：`<1h #ffd166` / `1–4h #ff9f0a` / `>4h #e0820a`。
- **主题无关**：9 套主题只定义 `--bad` / `--warn` 的**色值**，语义在主文件 → 换主题自动跟随；不要把状态语义写进主题 CSS。

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
- 另有一份 `style/theme-material3.*`：**仅给归档** `docs/archive/versions/dashboard-release-monitor-v5.5.html` 探测用。现行 v5.6 注册的是 `theme-material.*`。这两个文件头已写明只留给该归档页，不要登记进现行 `THEME_REGISTRY`。

图表配色脚本约定：拦截 `echarts.init` / `setOption`，监听 `data-mode`，被移除时停止，并提供 `_themeCleanup`。

### 视图

- 登记：`VIEW_REGISTRY`
- 文件内：`window.VIEW_PLUGIN = { id, name, cols: 24, layout: [{id,x,y,w,h}, ...] }`；`cols: 24` 是列制标记，缺省时按旧 12 列推断（见 §4、D-30）
- 编辑栏「导出视图文件」可生成，放入 `views/` 并登记即可分享

---

## 6. 关键运行约束

- `file://` 必须可用；禁止引入必须 HTTP 的能力（除非保留 file:// 兑底）。
- **追踪模式与常规详情共用一个抽屉**（D-34）：`openTrace()` 给 `#detailPanel` 加 `.trace-mode`（宽度收窄 `min(95vw,920px)`）、隐藏图表与常规明细表、显示 `#detailTraceBox`；`closeDetail()` 必须移除该类并复位容器。两者**必须共用**同一套 `detailPanelOpening` / `detailDrawTimer` / `detailResizeTimer` / `detailDisposeTimer`——各写一套会回退 Issue #7·#5 的定时器修复。
- 追踪为**纯展示层**：只读 `orders[单号]` 与 `rows.filter(放行单号)`，禁止新增 `computeStats` 字段；单号入口用 `.orderLink` + 全局委托（点击须 `stopPropagation()`，否则会连带触发卡片自身的 `detailKey` 下钻）。状态徽章用 `o.在途超时` / `o.放行超时 && o.已到达` / `o.超时未接收` / `o.已接收 && o.接收超时` 等布尔字段，禁止用源字段 `接收状态` 原文。
- 大 xlsx 的硬瓶颈是 `XLSX.read` 同步阻塞；产品侧引导转存 CSV，本机重复打开走 IndexedDB 缓存恢复。
- **IndexedDB 只存"最近一份数据"**，不得用它承载业务状态；业务状态仍走 `localStorage`。现有键：`dashLayouts`（视图）、`dashTheme`（主题）、`dashMode`（深浅色）、`perfMode`（性能档）、`dashCacheOff`（数据缓存开关）。file:// 下这些存储由**所有本地 HTML 共享**，故键名与 DB 名都带项目前缀，改动需谨慎。
- 缓存写入必须分块让出主线程，且**任何失败都要自愈**（清缓存 + 不污染当前 `rows`）；探活失败时相关入口整块隐藏。
- 派生字段 `_` 前缀，导出前 `stripPrivate()` 剥离。
- 新图表动画走 `withAnim()` / `animOpt()`，大数据与 lite 自动降级。
- 拼进 `innerHTML`（含 tooltip formatter 返回的 HTML）的单元格文本与文件名必须先经 `escapeHtml`。

常见排障（现象 → 先查）：缺必需列 → 别名或表头未识别；解析失败 → 空 Sheet 是否仍被误当成第一张（现行应已跳过）；主题进门就不是默认 → `localStorage.dashTheme` 或探测未标 `data-probe`；**视图比保存时宽一倍 → 该布局/插件缺 `cols: 24`，被当成旧 12 列 ×2（D-30）**；**没有「恢复上次数据」按钮 → IndexedDB 被禁用/被关掉开关，或上一份数据写入失败**；不想在本机留数据 → 抽屉「🗑 清除缓存」或关掉「💾 数据缓存」；卡顿 → 打开右侧功能抽屉，打开「流畅模式」开关。

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
  w: 12, h: 6,
  minW: 6, maxW: 24, minH: 4, maxH: 12,
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

四张业务 KPI 的 **M/L 模板**不要另起一套口径：改字段只动 `buildKpiProps`；改视觉对照 `kpi-card-redesign/HANDOFF.md` 与 `index.html`。`kpiAdaptive: true` 的卡在 `resizestop` 换档。

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
  cols: 24,                 // ★ 列制标记，见下
  layout: [
    { id: "kpi_overview", x: 0, y: 0, w: 4, h: 4 }
  ]
};
```

放入 `views/`，在 `VIEW_REGISTRY` 追加 `{ id, file }`。`file://` 不会自动扫描未登记文件。

`cols: 24` 必须写：缺省时看板按 v5.5 旧文件处理，若布局 `x+w ≤ 12` 会整体 ×2 —— 于是"只排左半边"的新布局会被放大一倍（D-30）。编辑栏「📤 导出视图文件」生成的插件已自带该字段。

### 7.6 演示数据

改业务规则时同步 `makeDemoOrder()`（以及如需测试文件则用 `gen_monitor_data_v3.py`）：分类整单固定、超时标记打末笔、特保前缀 WF9897。
