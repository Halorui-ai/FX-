# 设计原型沙盒

这里**不是**看板交付物。现行产品仍是根目录 `dashboard-release-monitor-v5.6.html`（以 README 顶部为准）。

设计 Agent（通常是 Trae）只在本目录产出可点的静态原型和说明书。用户把 HANDOFF 标成 `approved` 之后，实现 Agent（通常是 Grok Build）才能改主文件。规则见 [AGENT.md](../../AGENT.md)；决策见 D-24、D-25。

## 目录

```text
docs/prototypes/
  README.md                 ← 本文件
  _template/HANDOFF.md      ← 新任务先拷这份
  <slug>/                   ← 短横线英文名，例如 gate-stuck-card
    index.html              ← 自包含原型，浏览器直接打开
    HANDOFF.md              ← 实现说明书（必含 status）
```

已交付的 KPI 中卡/大卡样板仍在仓库根 `kpi-card-redesign/`（D-22），不再搬。**以后新原型只进本目录**，不要再在根上新开一个目录，也不要去 `液态玻璃看板Qoder`。

## 流程

开工闸门仍是 HANDOFF 的 `approved`。下面 Git 步骤是推荐，详见 AGENT「推荐卡片流程」。

1. （推荐）开 Issue；Trae 在 `design/<slug>` 上拷 `_template/HANDOFF.md` 到 `<slug>/HANDOFF.md`，`status: draft`。
2. 写自包含 `index.html`（禁止 CDN，禁止复制主 HTML），开 PR 指向 `main`。
3. 用户在浏览器里点原型；通过后把 HANDOFF 改成 `status: approved` 并填 freeze，合并设计 PR。可选打 `ready-for-build`。
4. Grok 从 `main` 开 `feat/<slug>`，只读 `approved` 的 HANDOFF，按 ARCHITECTURE §7.3 改主文件；数字走 `buildKpiProps` / `computeStats()`，禁止写死原型里的演示值。开 PR。
5. 用户 `file://` 验收主文件后合并；HANDOFF 改 `shipped`；关 Issue。

## 禁止

- 把本目录当成另一份可发布看板。
- 未 `approved` 就改 `dashboard-release-monitor-*.html`、`CONFIG`、`computeStats`、`buildKpiProps`。
- 用 Issue 标签替代 HANDOFF 状态。
- 在仓库根或 Qoder 目录再开平行原型目录。
- 向本仓库提交 `.trae-html-share-packages/`、`.uploads/`。
