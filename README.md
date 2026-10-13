# 物品放行监控数据看板

纯前端、完全离线的 Excel 分析工具。把放行系统导出的 `.xls / .xlsx / .csv` 拖进页面，特保识别、超时判定、结案率与图表全部在浏览器本地完成，数据不出内网。

> **当前版本**：`v5.6.0`（主题插件 + 浅色/深色；顶栏功能抽屉）  
> **主文件**：`dashboard-release-monitor-v5.6.html`  
> **工作目录**：本仓库（GitHub `Halorui-ai/FX-`）。`液态玻璃看板Qoder` 为另一 agent 的视觉实验归档，**禁止在那边平行改业务**。新布局原型只写 [`docs/prototypes/`](docs/prototypes/README.md)。

---

## 怎么打开

1. 保留 `lib/` 与主 HTML 在同一目录（可选附带 `style/`、`views/`）。
2. 用 Chrome / Edge 双击主文件（`file://` 即可，无需服务器、无需联网）。
3. 拖入导出文件，或点「载入示例数据预览」。
4. 加载过一次后，下次打开上传区会多出「⏱ 恢复上次数据（文件名 · 行数 · 时间）」，免去重新解析（10 万行约 20 秒 → 约 2 秒）。数据只留在本机浏览器，可在功能抽屉「💾 数据缓存」里关闭或一键清除。

大文件建议先点「转存 CSV」再加载（约 35 倍）。老电脑点顶栏右侧圆形箭头打开功能面板，把「流畅模式」开关打开。验收门岗高压卡请加载 `物品放行监控_门岗压力演示.xlsx`（由 `gen_gate_pressure_data.py` 生成），不要用 100k 均分门岗集。

配套工具：根目录 `xls-to-csv-converter.html`（离线把 `.xls` / `.xlsx` 转为 CSV，双击打开；不是看板主文件）。

---

## 文档（先读再改）

| 文件 | 给谁 | 回答什么 |
|------|------|----------|
| [AGENT.md](AGENT.md) | 所有 AI agent | 准许 / 禁止、角色分工、开工与**提交前**检查 |
| [CHANGELOG.md](CHANGELOG.md) | 人 / 下一班 agent | **先看「进行中」**；这次和近日改了什么 |
| [CONTEXT.md](CONTEXT.md) | 改业务 / 对数字 | 记录 vs 单、口径、卡片、数据格式 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 改结构 / 加功能 | 数据流、分区、插件、顶栏壳、KPI 分档；末章如何扩展 |
| [docs/prototypes/](docs/prototypes/README.md) | 设计 Agent → 实现 Agent | 新布局原型沙盒；无 `approved` 不准改主文件 |
| [kpi-card-redesign/HANDOFF.md](kpi-card-redesign/HANDOFF.md) | 改 KPI 中卡/大卡 | 已交付视觉规格；原型 `kpi-card-redesign/index.html` |
| [DECISIONS.md](DECISIONS.md) | 改口径或机制前 | 过往决策与踩坑（只追加） |

归档（只读，索引见 [`docs/archive/README.md`](docs/archive/README.md)）：

- 拆分前的超长 README：[`docs/archive/README-项目管理文档-v5.5.md`](docs/archive/README-项目管理文档-v5.5.md)
- 旧版看板 HTML：`docs/archive/versions/`（v2～v5.5）
- 预研 / 模板 HTML：`docs/archive/research/`
- 旧 Python 脚本：`docs/archive/scripts/`（勿用它们生成特保测试数据）

---

## 冲突时谁说了算

| 问题 | 只信 |
|------|------|
| 现在用哪个 HTML | 本文顶部 |
| 数字按行还是按单、结案率怎么算 | CONTEXT.md |
| 解析路径、主题外挂还是内联 | ARCHITECTURE.md |
| 新卡片 / 主题 / 视图怎么加 | ARCHITECTURE.md 末章 |
| 新布局先写哪 | docs/prototypes/ + AGENT 角色节 |
| 开工不开工看什么 | HANDOFF 的 `status`，不是 Issue 标签 |
| 能不能另开目录改 | AGENT.md |
| 这件事以前定过没有 | DECISIONS.md |
| 上次做到哪、这次改了什么 | CHANGELOG.md |
