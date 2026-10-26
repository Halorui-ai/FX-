# Agent 准则

你好，Agent。开始任何修改前读完本文件。规则只维护在这里；`AGENTS.md` / `CLAUDE.md` 只是指针（Trae 若只自动读复数的 `AGENTS.md`，仍要再打开本文件）。

## Agent 角色分工

多个工具串行协作，不要同时改同一批主文件行。工作树只有本仓库（D-15）；设计沙盒是唯一允许的新目录例外（D-24）。

| 角色 | 默认工具 | 允许改 | 禁止改 |
|--------|----------|----------|----------|
| 设计 | Trae Design / SOLO | 仅 `docs/prototypes/<slug>/`（`index.html` + `HANDOFF.md`） | 主 HTML、`CONFIG`、`computeStats` / `buildKpiProps`、`CONTEXT` 口径、`lib/`、`style/`、`views/` |
| 审核 | 用户 | 把 HANDOFF 的 `status` 改成 `approved`，写 freeze；合并设计 PR / 实现 PR | — |
| 实现 | Grok Build | 主文件、`style/`、`views/`；按对照表改 CONTEXT / ARCHITECTURE / DECISIONS / CHANGELOG | 改已批准视觉方向；再复制一份主 HTML；`status` 不是 `approved` 时改对应卡片 |
| 测试 | 实现 Agent + 用户 | CHANGELOG、HANDOFF 验收勾 | 把 Playwright 等测试脚本当交付物入库 |

**开工闸门是文件里的 `status: approved`，不是 GitHub 标签。** 没有 `approved`，实现 Agent 必须停。Issue / 分支 / PR 是推荐渠道（D-25），不卡死 `file://` 本机流程。**合进 `main` 的闸门见 D-35**：新功能 / 行为变化 / 口径改动必须开 PR，由仓库哨兵复核后再合并；仅纯文档错别字 / 注释 / 体积数字等无行为变化的小改可直推 `main`。

**开 PR 必须写明是哪个 Agent 开的**（本机常有多个 Agent 改同一仓库，列表里要分得清）。正文第一行写 `Agent: <工具名>`，标题前加 `[工具名]`。工具名用角色表里的默认工具，例如 `Grok Build`、`Trae Design`，不要写「AI」这种笼统称呼。后续往该 PR 推提交的 Agent 若换了，在正文补一行 `后续提交: <工具名>`。

已交付样板：`kpi-card-redesign/`（D-22）。新原型只进 `docs/prototypes/`。

## 推荐卡片流程（新布局 / 改主文件）

新布局或要改主 HTML 时按这条走。没开 Issue 不算违禁；没打 `ready-for-build` 不算禁止开工。设计文件只放 `docs/prototypes/<slug>/`。

1. **（推荐）** 开 Issue，标题写清改哪张卡。可选标签 `design/trae`。
2. **Trae** 从 `main` 开 `design/<slug>`，只提交 `docs/prototypes/<slug>/`（`index.html` + `HANDOFF.md`，`status: draft`）。禁止提 `.trae-html-share-packages/`、`.uploads/`。开 PR 指向 `main`（标题 `[Trae Design] …`，正文第一行 `Agent: Trae Design`）。
3. **用户** 打开原型。通过：在该 PR 里把 HANDOFF 改成 `approved` 并填 freeze → 合并设计 PR → （可选）Issue 标签改 `ready-for-build`。
4. **Grok** `git pull origin main`，确认 HANDOFF 已是 `approved`，再开 `feat/<slug>` 改主文件，开工可把 HANDOFF 改 `implementing`，提 PR（标题 `[Grok Build] …`，正文第一行 `Agent: Grok Build`）。
5. **用户** 审 PR + 本机 `file://` 验收 → 合并 → HANDOFF 改 `shipped` → 关 Issue。

Grok 从 `design/<slug>` 读未合并原型也可以，但默认先合设计 PR，实现只基于 `main`。

## 开工顺序

1. 读 [README.md](README.md) 顶部：确认当前版本与主文件。
2. 读 [CHANGELOG.md](CHANGELOG.md) **「进行中」** 与最近一日：接着没做完的，不要当已经完成。
3. 按任务再读：
   - 改统计 / 口径 / 新 KPI → [CONTEXT.md](CONTEXT.md)
   - 改解析、性能、布局、主题、顶栏壳，或加卡片/主题/视图 → [ARCHITECTURE.md](ARCHITECTURE.md)
   - 新卡片布局 / 改 KPI 中卡大卡视觉 → [docs/prototypes/](docs/prototypes/README.md)；四张业务 KPI 的 M/L 以 [kpi-card-redesign/HANDOFF.md](kpi-card-redesign/HANDOFF.md) 为规格
4. 改口径、解析路径、主题机制、工作目录、壳层方案之前，先搜 [DECISIONS.md](DECISIONS.md)。
5. 不确定 → 停。不要另开看板副本「先试」。设计试做只能写在 `docs/prototypes/<slug>/`。

## 硬禁令

- **唯一工作树**：只在本仓库改。禁止在 `液态玻璃看板Qoder` 或任何新副本里平行改业务。
- **唯一主文件**：以 README 顶部为准（现为根目录 `dashboard-release-monitor-v5.6.html`）。不要把 `docs/archive/` 里的旧 HTML 当成现行交付物。`docs/prototypes/` 不是交付物。
- **禁止 CDN**。新依赖下载到 `./lib/`，相对路径引用。
- **禁止再复制一份 HTML 当新皮肤**（不要再做 `v5.x-themes.html` / 把主题烤进单文件）。新主题走 `style/` + `THEME_REGISTRY`，见 ARCHITECTURE 末章。
- **无 `approved` 不准改主文件对应卡**。设计阶段禁止改 `dashboard-release-monitor-*.html`。不要用 Issue 标签替代这一条。
- **版本号不得复用不同含义**（已有事故：两边的「v5.2」各指一件事）。
- **统计数字默认订单级**（按放行单号聚合）。记录级必须在 UI 上写明「记录」。
- **特保只认** `放行单号` 前缀 `WF9897`。禁止用 WF8888 或物品类型关键词。
- **一单仅一种物品分类**。禁止对分类 `split("/")`。
- 渲染层不得改 `rows` / `orders`（单向数据流）。
- 不要把现行口径公式复制进 DECISIONS；那边只记结论与禁令。
- **功能 / 行为 / 口径禁止直推 `main`（D-35）。** 这类改动必须开 PR，仓库哨兵复核后再合并；仅纯文档错别字 / 注释 / 体积数字可直推。
- **`*.pptx` 与 `docs/参赛PPT/` 本地可保留、不入库。** 已写入 `.gitignore`；不要再把任何 `.pptx` 或该目录加入版本库。
- **禁止只提交代码、不改文档。** 用户说「提交 git」或「今天先到这 / 明天继续」时，若本回合改过仓库文件，必须先按下面对照表补完文档（**至少写 CHANGELOG**），**同一笔提交里带上**，再 push。
- 用户满意收工、或没时间明天接着干，**两种都要提交**；后者必须把未做完的写进 CHANGELOG「进行中」，不要让下一班以为已经做完。

## 改了什么 → 改哪份文档

除对照表各行外：**几乎每次提交都要在 [CHANGELOG.md](CHANGELOG.md) 当日追加 1～5 条短句**（新的在上）。现行规则仍写 CONTEXT / ARCHITECTURE，原因与禁令仍只追加 DECISIONS，不要把流水账写进那三份。

| 本回合改了 | 必须更新 |
|------------|----------|
| **任何行为或界面变化**（含纯视觉） | CHANGELOG 当日条 |
| **未做完、明天继续** | CHANGELOG「进行中」：做到哪、下一步、不要动什么 |
| 主文件名 / 版本号 / `<title>` / 页脚 | README 顶部 + 主文件标识（三处一致）+ CHANGELOG |
| 统计口径、特保、超时、结案率、卡片公式 | CONTEXT **现行** + DECISIONS 一条 + CHANGELOG |
| 解析、性能、Worker、file://、数据流 | ARCHITECTURE + 必要时 DECISIONS + CHANGELOG |
| 顶栏 / 抽屉 / 开关 / 编辑态等**壳与交互** | ARCHITECTURE 现行壳 + 若否定备选则 DECISIONS + CHANGELOG |
| 主题机制、注册表、抽屉按钮三态 | ARCHITECTURE §5 / §7.4 + 各主题 css 约定 + CHANGELOG |
| 加卡片 / 主题 / 视图 | ARCHITECTURE 末章；登记表同步 + CHANGELOG |
| 新布局原型 / HANDOFF 流程 / Agent 角色 | AGENT 角色节 + `docs/prototypes/` + 必要时 DECISIONS + CHANGELOG |
| 生成器、测试用 xlsx/csv | CONTEXT 测试数据段 + CHANGELOG |
| 归档 / 移动 / 删除仓库文件 | README 归档索引 + CHANGELOG |
| `localStorage` 键、依赖 `lib/` | ARCHITECTURE + CHANGELOG |
| 工作树、归档目录、版本号含义 | README + AGENT + DECISIONS + CHANGELOG |
| 仅修错别字/注释、行为完全不变 | CHANGELOG 可写「无行为变化：…」；其它文档可不改 |

「已经满意，提交吧」和「先存盘明天再改」**都不能**跳过本表。先改文档，再 `git commit`。

## 收工检查

提交 git **之前**按顺序过完（不要先 commit 再补）：

1. CHANGELOG：当日有条；若明天继续，「进行中」不是「无」。
2. 上表其余行：本回合有改动的，对应文档已改。
3. 主文件 `<title>`、页脚、README 顶部三个版本字符串相同。
4. 点「载入示例数据预览」：卡片能出来；点顶栏右侧圆形箭头打开功能抽屉，切一次主题、点开一个 KPI 下钻；控制台无报错。（若本次只改文档、未改看板，本条可跳过。）
5. 改了解析 / 口径 / 主题机制时：用根目录 `物品放行监控_生成_100k.xlsx` 拖入加载，应能完成解析；特保须按 WF9897 识别。
6. 若本回合开了 PR：标题带 `[工具名]`，正文第一行 `Agent: <工具名>`。

## 推荐提示词（可复制）

**Trae / 设计**

> 从 `main` 开分支 `design/<slug>`。只在 `docs/prototypes/<slug>/` 写自包含 `index.html` 和 `HANDOFF.md`（先拷 `_template`，`status: draft`）。先读 AGENT.md、ARCHITECTURE §4/§7.3、CONTEXT 里相关口径。禁止改 `dashboard-release-monitor-v5.6.html`，禁止复制主文件，禁止改特保/超时公式，禁止提交 `.trae-html-share-packages/` 与 `.uploads/`。数字用演示值，但 HANDOFF 必须写出对应的 `computeStats` / `buildKpiProps` 字段名。开 PR 指向 `main`，标题 `[Trae Design] …`，正文第一行 `Agent: Trae Design`。

**Grok Build / 实现**

> `git pull origin main`。读 AGENT.md、CHANGELOG「进行中」、指定 HANDOFF。仅当 `status: approved` 才改主文件（不要只看 Issue 标签）。从 `main` 开 `feat/<slug>`。视觉按 HANDOFF，数据只走 `buildKpiProps`，禁止写死原型数字。先出计划：要动的 `CARD_DEFS` / render / update。用户确认后再改代码。收工按 AGENT 对照表改 CHANGELOG（以及需要的 ARCHITECTURE/CONTEXT/DECISIONS），开 PR：标题 `[Grok Build] …`，正文第一行 `Agent: Grok Build`。

## 推荐、不强制

本机 `file://` 双击交付是正式用法。新布局走上面的 Issue / PR。**功能 / 行为 / 口径必须开 PR，哨兵复核后合并（D-35）**；仅纯文档错别字 / 注释 / 体积数字可直推 `main`。PR **不能**代替上表的文档同步。不要用 Actions / `grok -p` 被标签自动开工。
