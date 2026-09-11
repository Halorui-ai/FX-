# Agent 准则

你好，Agent。开始任何修改前读完本文件。规则只维护在这里；`AGENTS.md` / `CLAUDE.md` 只是指针。

## 开工顺序

1. 读 [README.md](README.md) 顶部：确认当前版本与主文件。
2. 读 [CHANGELOG.md](CHANGELOG.md) **「进行中」** 与最近一日：接着没做完的，不要当已经完成。
3. 按任务再读：
   - 改统计 / 口径 / 新 KPI → [CONTEXT.md](CONTEXT.md)
   - 改解析、性能、布局、主题、顶栏壳，或加卡片/主题/视图 → [ARCHITECTURE.md](ARCHITECTURE.md)
4. 改口径、解析路径、主题机制、工作目录、壳层方案之前，先搜 [DECISIONS.md](DECISIONS.md)。
5. 不确定 → 停，不要另开目录「先试」。

## 硬禁令

- **唯一工作树**：只在本仓库改。禁止在 `液态玻璃看板Qoder` 或任何新副本里平行改业务。
- **唯一主文件**：以 README 顶部为准（现为根目录 `dashboard-release-monitor-v5.6.html`）。不要把 `docs/archive/` 里的旧 HTML 当成现行交付物。
- **禁止 CDN**。新依赖下载到 `./lib/`，相对路径引用。
- **禁止再复制一份 HTML 当新皮肤**（不要再做 `v5.x-themes.html` / 把主题烤进单文件）。新主题走 `style/` + `THEME_REGISTRY`，见 ARCHITECTURE 末章。
- **版本号不得复用不同含义**（已有事故：两边的「v5.2」各指一件事）。
- **统计数字默认订单级**（按放行单号聚合）。记录级必须在 UI 上写明「记录」。
- **特保只认** `放行单号` 前缀 `WF9897`。禁止用 WF8888 或物品类型关键词。
- **一单仅一种物品分类**。禁止对分类 `split("/")`。
- 渲染层不得改 `rows` / `orders`（单向数据流）。
- 不要把现行口径公式复制进 DECISIONS；那边只记结论与禁令。
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

## 推荐、不强制

本机 `file://` 双击交付是正式用法。GitHub PR 鼓励，但不卡死本机流程。PR **不能**代替上表的文档同步。
