# Agent 准则

你好，Agent。开始任何修改前读完本文件。规则只维护在这里；`AGENTS.md` / `CLAUDE.md` 只是指针。

## 开工顺序

1. 读 [README.md](README.md) 顶部：确认当前版本与主文件。
2. 按任务再读：
   - 改统计 / 口径 / 新 KPI → [CONTEXT.md](CONTEXT.md)
   - 改解析、性能、布局、主题机制，或加卡片/主题/视图 → [ARCHITECTURE.md](ARCHITECTURE.md)
3. 改口径、解析路径、主题机制、工作目录之前，先搜 [DECISIONS.md](DECISIONS.md)。
4. 不确定 → 停，不要另开目录「先试」。

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

## 收工检查

- 主文件 `<title>` / 页脚版本与 README 顶部一致。
- 改了口径或机制：同一回合追加 DECISIONS 一条，并回写 CONTEXT 或 ARCHITECTURE 的**现行**段落。
- 加卡片 / 主题 / 视图：走 ARCHITECTURE 末章，不要新开平行 HTML。
- 控制台零错误（至少演示数据走通）。

## 推荐、不强制

本机 `file://` 双击交付是正式用法。GitHub PR 鼓励，但不卡死本机流程。
