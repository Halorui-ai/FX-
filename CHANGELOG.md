# 改动记录

下一任 agent **先看「进行中」**，再看最近一日。  
这里记「做了什么 / 还没做完」；**现在怎么算、怎么接**仍以 CONTEXT / ARCHITECTURE 为准；**为什么、禁止再怎样**以 DECISIONS 为准。

写法：每条 1～2 句，按日追加在「进行中」下面（新的在上）。不要把公式或长步骤贴进来。

---

## 进行中

无。

<!-- 明天接着改时：把未做完的写在这里（做到哪、下一步、不要动什么）。做完后删掉或迁到当日记录。 -->

---

## 2026-09-23

- 新增 `docs/prototypes/completion-rate-card/` 原型：结案率水球图中卡(M)/大卡(L)设计，含总览/特保/非特保 Tab、三栏布局、待关注单据列表。HANDOFF 已 `approved`，S 小卡水球不变。
- 修复原型水球水位与显示百分比不匹配（按 `水位Y = 球底Y − 百分比×直径` 重算），以及大卡右栏 footer 被裁剪（`.right-column` 补 `min-height:0`）。
- 原型移除 CDN 依赖（Tailwind/Chart.js 未使用，Lucide 图标改内联 SVG），自包含零外部请求。

---

## 2026-09-22

- 无行为变化：更正同日网格说明里的「进步」为「步进」。
- D-25：新布局推荐 Issue + `design/<slug>` PR + `feat/<slug>` PR；开工闸门仍是 HANDOFF `approved`，`ready-for-build` 只是信号。小改仍可直推 `main`。
- D-24：设计只写 `docs/prototypes/<slug>/`；用户把 HANDOFF 标 `approved` 后 Grok 才改主文件。禁止再去 Qoder 目录做设计。`kpi-card-redesign/` 作已交付样板留在原处。
- AGENT 增加角色表、推荐卡片流程与两段开工提示词。

- 网格改为 24 列、行高 48px（横竖步进约细一倍）。内置布局与 `CARD_DEFS` 尺寸已 ×2；旧 `localStorage` / 12 列视图插件自动迁移。KPI：中卡 `h≥6` 或（`w≥10` 且 `h≥5`），大卡 `w≥12` 且 `h≥8`（一行可并排两张）。
- 修复 24 列卡片塌成细条：`gridstack.min.css` 只有 `.gs-12` 宽度规则，已补 `.gs-24` 并在初始化时挂上该类。

## 2026-09-12

- 按 `kpi-card-redesign/HANDOFF.md` 重写四张 KPI 的中卡/大卡：小卡保持原数字逻辑；中卡三段式（主数字 + SVG 微图形 + 底栏）；大卡三栏（指标条 + 表头 Tab + 环图引导线 + 最新记录）。数值全部来自 `buildKpiProps` / `computeStats()`。结案率仍用水球。
- 大卡对齐原型：Tab 在标题右侧；环图引导线+占比；三栏 238/290/1fr，窄卡容器查询堆叠；「全部 N 条」用过滤后条数。`tests/kpi-density-e2e.cjs` 覆盖 S→M→L、Tab 不弹层、点主数字打开详情。
- D-22：中/大卡以 HANDOFF 为规格，禁止再退回芯片横条或写死原型数字。
- `tests/` 改为本地忽略，不入库（Playwright 脚本不是离线看板交付物）。

- 新增卡 A `chart_gate_stuck`（在途滞留 By 流入门岗，订单级堆叠超时/未超时）与卡 B `chart_gate_load`（过岗负荷 By 实际放行门岗，记录级次数）。默认/一线/运维/GDMS 视图已放入。
- 新增 `gen_gate_pressure_data.py` → `物品放行监控_门岗压力演示.xlsx`（16 岗，中码头/物流门倾斜）。口径脚本验收：滞留 TOP1 中码头 106 单、TOP2 合计 74.5%；过岗 TOP 中码头 480 次。100k 仍只作解析压测。
- D-21：滞留与过货两种门岗角色不得混柱。卡 A 明确为「目的地将到未到」，不是最后盖章岗。

## 2026-09-11

- 文档中枢：README 短入口 + AGENT / CONTEXT / ARCHITECTURE / DECISIONS；旧 README 与历史 HTML/脚本进 `docs/archive/`。
- `gen_monitor_data_v3.py` 改为相对本仓库路径；删除误导性 Material3 导入说明；收工加载测试指定 `物品放行监控_生成_100k.xlsx`。打标签 `v5.6.0`。
- 顶栏改为状态芯片 + 右侧圆形箭头展开功能抽屉（缓动）；深浅色/流畅为 iOS 滑块；设置项与导出同一行。抽屉按钮空闲态跟随各主题，禁止黑底、禁止「功能」文字。
- AGENT：提交 git 前必须按改动类型同步文档（D-18 壳层、D-19 禁止先推代码）。本文件起作为每次提交的改动流水。
