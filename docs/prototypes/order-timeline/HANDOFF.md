# HANDOFF：单据全生命周期时间线（订单追踪抽屉）

配套原型：同目录 `index.html`（自包含、零依赖，浏览器直接打开；顶部按钮可切换 5 种典型单据状态，右上角可切深浅色）。
先在浏览器打开原型确认视觉与信息层级，再按本说明书改主文件。

```yaml
status: draft          # draft | approved | implementing | shipped
owner_design: DSH（本次由实现侧代笔原型，待用户审核）
owner_impl: Grok Build
approved_by:
approved_at:           # YYYY-MM-DD
freeze:                # 审批后不得改：时间轴三态圆点 / 段耗时胶囊 / 最长卡点红色高亮 / 摘要 chips 顺序
must_not_change:       # 口径不动（CONTEXT §3 的超时与特保定义）；不改 CARD_DEFS 任何现有卡；不改 buildKpiProps；不碰结算率水球
impl_touch:            # dashboard-release-monitor-v5.6.html：#detailOverlay 内新增容器 + CSS + openTrace/renderTrace；ARCHITECTURE §3/§6
```

> 实现 Agent：`status` 不是 `approved`（或 `implementing`）就不要改主文件。

---

## 1. 背景与目标

现行看板能回答"有多少单超时"，但回答不了**"这一单为什么卡住"**——要回答就得回放行系统翻原始记录。

本功能：任意单号一键展开**全链路时间线**——申请 → 放行（各门岗）→ 接收，每段标注耗时，并自动指出**最长卡点**。

| 项 | 内容 |
|---|---|
| 谁用 | 安保 / 物流管理员；追单、回复现场询问、定位责任环节 |
| 在哪看 | 复用现有二级详情抽屉 `#detailOverlay`（不新开弹层、不改抽屉骨架） |
| 本次不做 | 不做新卡片、不改任何 KPI 口径、不做全局搜索（后续可加） |

**与现有卡片的关系**：`alert_transit` / `alert_receive` / `gdms_unclosed` / `table_detail` 的单号从"纯文本"变为"可点入口"。

---

## 2. 设计 Token

直接复用主文件既有 CSS 变量，**不要另起一套色**（这样 9 套主题与深浅色自动适配）：

| Token | 值（默认主题） | 用途 |
|---|---|---|
| `--accent` | `#0071e3` | 申请节点、进行中主色 |
| `--ok` | `#34c759` | 正常 / 已接收 |
| `--warn` | `#ff9f0a` | 放行超时（含在途超时） |
| `--bad` | `#ff3b30` | 接收超时 / 未接收 / 最长卡点 |
| `--purple` | `#5e5ce6` | 特级安保单（WF9897） |
| `--txt` `--txt2` `--txt3` | 主 / 次 / 弱文本 | 节点标题 / 元信息 / 未开始时间 |
| `--line` `--track` | 分隔线 / 浅底 | 时间轴竖线、胶囊底色 |

原型 `:root` 里另有 `--card` `--card-strong` `--shadow` 仅用于原型外壳演示，实现时用主文件现有卡片面即可。

- 圆角：抽屉内面板 `12px`，胶囊 / 徽章 `999px`，圆点 `50%`
- 字号：节点标题 `13.5`、元信息 `12`、时间 `12.5`（等宽 `tabular-nums`）、徽章 `11.5`、chips 键 `11` / 值 `15`
- 单号与时间使用等宽字体（`Consolas / SF Mono / Menlo`）
- 动效：节点与段耗时依次淡入（`≤ 180ms`，间隔 `40ms`），尊重 `prefers-reduced-motion`

---

## 3. 布局（抽屉内新容器，无 S/M/L 分档）

抽屉现有结构（`#detailOverlay > #detailPanel > #detailPanelBody`）保持不变，**新增一个同级容器**：

```html
<div id="detailPanelBody">
  <div class="detailChips" id="detailChips"></div>
  <div id="detailDims" style="display:none"></div>
  <div id="detailChartBox"><div id="detailChart"></div></div>
  <div id="detailCatFilters"></div>
  <div id="detailTraceBox" style="display:none"></div>   <!-- ★ 新增：追踪模式内容 -->
  <div id="detailTableBox">…</div>
</div>
```

进入追踪模式时：`#detailTraceBox` 显示，`#detailChartBox` / `#detailCatFilters` / `#detailTableBox` / `#detailDims` 隐藏；退出时全部还原。

内部三段（自上而下）：

```
① 摘要 chips      4 格：记录数 / 已完成节点 / 总耗时 / 当前状态
② 身份行          类型徽章 + 单号(等宽) + 申请部门 + 物品分类 + 申请人 + 右侧状态徽章
③ 时间轴          节点行（时间 | 轴 | 内容）与段耗时行交替
④ 记录明细        该单所有记录的小表（记录级，标题写明「记录」）
```

**时间轴结构**（关键视觉，`grid-template-columns: 62px 26px 1fr`）：

```
 ● 08:15  │  申请        [正常]
 │        │  ⏱ 42 分钟
 ● 08:57  │  放行        [超时]      ← 节点：实心圆点 + 徽章
 │        │  ⏱ 6 小时 18 分  🔴 最长卡点
 ○ --:--  │  接收        [进行中]    ← 未完成：空心圆点 + 灰色时间
```

- **节点三态**：实心（已完成，按语义着色）／空心橙（进行中，未完成但有等待）／空心灰（未开始）
- **段耗时行**：位于两个节点之间，胶囊样式；**最长卡点**整段标红 + 「🔴 最长卡点」标签（仅当该单 ≥2 段时才评）
- 竖线：`2px`，`--line`；最长卡点段用 `--bad` 渐变加重
- 多记录单据：所有放行节点按时间排序插在申请与接收之间，节点标题注明「第 N 笔放行」

---

## 4. 数据字段

> 原型里的时间与数字**全是演示值**。实现时一律从 `orders` / `rows` 取，**不新增 `computeStats()` 字段、不新增口径**——时间线是纯展示层。

### 4.1 字段映射

| UI 文案 | 字段 | 级别 |
|---|---|---|
| 放行单号 | `orders[no].单号`（=「放行单号」原值） | 单 |
| 类型徽章 | `orders[no].特保` → 特级安保单 / 普通单 | 单 |
| 记录数 | `orders[no].记录数` | 单 |
| 申请部门 | `orders[no].申请部门` | 单 |
| 物品分类 | `orders[no].物品分类`（一单一种，勿 split） | 单 |
| 申请人 | 该单 `rows` 里 `申请人` 首个非空 | 记录 |
| 申请节点时间 | 该单所有 `rows` 的 `_申请日期` **取最早** | 记录 |
| 放行节点时间 | 每条记录的 `_放行日期`（`null` → 未放行） | 记录 |
| 放行门岗 / 人 | 该记录 `实际放行门岗` / `放行人` | 记录 |
| 接收节点时间 | 该单 `_接收日期`（取最早非空；全空 → 未接收） | 记录 |
| 接收人 / 部门 | 该记录 `接收人` / `接收人部门` | 记录 |
| 段耗时 | 相邻节点时间差；**未完成段 = `dayjs() − 上一节点时间`**（显示「已等待」） | — |
| 最长卡点 | 所有段耗时取最大值所在段 | — |
| 记录明细表 | 复用 `detailCols()` 的列集思路，或 `stripPrivate()` 后全字段 | 记录 |

### 4.2 状态徽章判定（订单级，按优先级取第一个命中）

| 优先级 | 条件 | 徽章 | 色 |
|---|---|---|---|
| 1 | `o.在途超时` | 在途超时 | `bad` |
| 2 | `o.超时未接收` | 超时未接收 | `bad` |
| 3 | `o.放行超时 && o.已到达` | 到达超时 | `warn` |
| 4 | `o.放行异常` | 放行异常 | `bad` |
| 5 | `o.已接收` | 已接收 | `ok` |
| 6 | 其余 | 在途 | `mute` |

> 口径依据 CONTEXT §3：「在途超时」与「到达超时」互斥且之和 = 放行超时单数；「超时未接收」⊂ 接收超时。**本表只做徽章文案选择，不重算任何统计。**

### 4.3 时间格式化

- 节点时间：`MM-DD HH:mm`（同日可省略日期，显示 `HH:mm`）
- 段耗时：`< 60 分钟` → 「N 分钟」；`≥ 1 小时` → 「x 小时 y 分」
- 未完成节点的等待时长前缀「已等待」

---

## 5. 交互

### 5.1 入口（4 处）

| 入口 | 改法 |
|---|---|
| 主看板明细表 `#detailTable`（`table_detail` 卡） | 单号列加 `cellClick` → `openTrace(单号)` |
| 二级详情明细表 `#detailTable2` | 同上 |
| 告警卡 / 未结案卡预览列表（`analysisTransitHTML` / `analysisReceiveHTML` / `gdms_unclosed`） | 单号包成 `<span class="orderLink" data-order="…">`，容器上做**事件委托**；点击需 `stopPropagation()`（避免触发卡片自身的 `detailKey` 下钻） |
| 单号样式 | `.orderLink`：虚线下划线 + `cursor:pointer` + hover 变 `--accent` |

### 5.2 抽屉状态（★ 易踩坑）

- `openTrace(no)` 复用 `#detailOverlay`，与 `openDetail(key)` **共用** `detailPanelOpening` / `detailDrawTimer` / `detailResizeTimer` / `detailDisposeTimer`；进入前必须按 `openDetail` 的做法**清掉未触发的定时器**（Issue #7·#5 修的是同一类问题，别回退）。
- 追踪模式无图表：调 `renderDetailChart(null)` 隐藏图表区即可；`detailResizeTimer` 里的 `if (detailChartInst) resize()` 在无实例时天然跳过。
- 进入追踪模式前**销毁** `#detailTable2` 的 Tabulator 实例（`detailTableInst.destroy()`），避免隐藏容器里残留实例。
- `closeDetail()` 时恢复各容器 `display` 与 `traceMode = false`，保证下次打开普通详情正常。
- Esc / 点遮罩 / ✕ 关闭行为与现有详情一致。

### 5.3 安全与规范

- 所有拼进 `innerHTML` 的文本（单号、部门、门岗、人名、物品名）**必须先 `escapeHtml()`**（D-29）。
- 颜色只用 CSS 变量（9 套主题 + 深浅色自动适配）；**不要写死十六进制**。
- 不改 `rows` / `orders`（单向数据流）。

---

## 6. 验收（file://）

- [ ] 打开主文件 → 载入示例数据 → 控制台无报错
- [ ] 明细表点单号 → 抽屉出现时间线；**再点另一个单号**能正确切换（不残留上一个单的内容）
- [ ] 告警卡（在途超时 / 超时未接收）点单号 → 打开时间线且**不误弹**该卡的详情页
- [ ] 五类单据各验一次：正常已接收 / 到达超时 / 在途超时（未放行） / 超时未接收 / 特保多记录
- [ ] 未完成节点显示「已等待 …（进行中）」，且不是假时间
- [ ] 最长卡点仅在该单 ≥2 段时出现，且与各段耗时比对正确
- [ ] 切换主题（至少 Terminal / 新拟态 / 瑞士极简）与深浅色：时间线颜色跟随、无写死色穿帮
- [ ] 追踪后关闭抽屉 → 再打开任一 KPI 详情：图表与表格正常（定时器未串）
- [ ] 拖入 `物品放行监控_生成_100k.xlsx`：点单号仍能打开（大数据量下不卡死）
