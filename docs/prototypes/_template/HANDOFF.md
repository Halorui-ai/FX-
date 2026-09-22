# HANDOFF：<short-title>

配套原型：同目录 `index.html`（自包含、零依赖，浏览器直接打开）。
先打开原型确认视觉与交互，再按本说明书改主文件。样板见 `kpi-card-redesign/HANDOFF.md`。

```yaml
status: draft          # draft | approved | implementing | shipped
owner_design: Trae
owner_impl: Grok Build
approved_by:
approved_at:           # YYYY-MM-DD
freeze:                # 审批后不得改的视觉：色 / 圆角 / 字号 / 布局骨架
must_not_change:       # 口径、S 小卡、结案率水球、特保 WF9897 等
impl_touch:            # CARD_DEFS / buildKpiProps / style/ …
```

> 实现 Agent：`status` 不是 `approved` （或 `implementing`）就不要改主文件里对应卡片。

---

## 1. 背景与目标

- 改什么卡 / 新什么卡：
- 谁用、在哪种尺寸下看：
- 本次不改什么：

---

## 2. 设计 Token

从原型 `:root` 抄出。能复用现行主题变量就复用，不要另起一套色。

| Token | 值 | 用途 |
|---|---|---|
| | | |

---

## 3. 布局与分档（若有 S/M/L）

当前网格是 24 列 × 行高 48px（D-23）。KPI 换档条件见 ARCHITECTURE §4；不要按旧 12 列写坐标。

| 档 | 条件 | 卡内 |
|---|---|---|
| S | | |
| M | | |
| L | | |

---

## 4. 数据字段

原型里的数字只是演示。实现时写对应的 `computeStats()` / `buildKpiProps` 字段名，禁止写死。

| UI 文案 | 字段 | 口径级别（单 / 记录） |
|---|---|---|
| | | |

---

## 5. 交互

- 点击 / 下钻 / Tab 是否弹层：
- 拖拽缩放是否仍走现有 gridstack：

---

## 6. 验收（file://）

- [ ] 打开主文件，载入示例数据，控制台无报错
- [ ] 目标卡按需从 S 拖到 M、再到 L，模板切换正确
- [ ] 下钻仍进现有二级页；Tab 不误弹详情
- [ ] 若动过口径：拖入 `物品放行监控_生成_100k.xlsx`，特保仍只认 `WF9897`
