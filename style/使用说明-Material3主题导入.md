# Material Design 3 主题导入说明

## 你得到了什么文件

| 文件 | 作用 |
|------|------|
| `theme-material3.css` | 覆盖所有 CSS 样式（卡片、按钮、顶栏、表格、详情面板等） |
| `theme-material3-charts.js` | 自动将 ECharts 图表配色替换为 Material 3 配色 |

这两个文件**不会修改你的原有代码**，只是在上面叠加一层样式覆盖。

---

## 导入步骤（3 步完成）

### 第 1 步：确认文件位置

确保 `theme-material3.css` 和 `theme-material3-charts.js` 与 `dashboard-release-monitor-v4.html` 在**同一目录**下。

```
你的项目目录/
├── dashboard-release-monitor-v4.html   ← 你的看板
├── theme-material3.css                 ← 主题样式（新增）
├── theme-material3-charts.js           ← 图表配色（新增）
└── lib/                                ← 现有依赖库
```

### 第 2 步：在 HTML 中引入主题 CSS

打开 `dashboard-release-monitor-v4.html`，找到 `<head>` 里的 `</style>` 标签（约第 355 行），在它**下面**加一行：

```html
<link rel="stylesheet" href="./theme-material3.css">
```

修改后应该是这样：

```html
</style>
<link rel="stylesheet" href="./theme-material3.css">   <!-- 新增这一行 -->
</head>
```

### 第 3 步：在 HTML 中引入图表配色 JS

找到 `</body>` 标签（文件末尾附近），在它**上面**加一行：

```html
<script src="./theme-material3-charts.js"></script>
```

修改后应该是这样：

```html
<script src="./theme-material3-charts.js"></script>   <!-- 新增这一行 -->
</body>
```

---

## 完成！效果说明

完成以上 3 步后，打开你的看板，所有界面元素会自动变成 Material Design 3 风格：

- **配色**：Apple 蓝 → Google 蓝 (#4285F4)，全部状态色切换为 Google 四色体系
- **卡片**：毛玻璃半透明 → Material 纯白卡片 + 8px 圆角 + elevation 阴影
- **按钮**：胶囊形 → Material 8px 圆角矩形
- **字体**：SF Pro → Google Sans / Roboto 风格，标题字重 700 → 500 (Medium)
- **表格**：透明玻璃 → Material Data Table（浅灰表头 + 悬浮高亮）
- **图表**：ECharts 所有配色自动替换为 Material 3 调色板
- **动态背景**：液态玻璃画布自动隐藏，改为纯白背景

---

## 如何切换回原风格

只需**注释掉或删除**你添加的那两行即可：

```html
<!-- <link rel="stylesheet" href="./theme-material3.css"> -->
<!-- <script src="./theme-material3-charts.js"></script> -->
```

原风格完整保留，不受任何影响。

---

## 在 Qoder 中操作

1. 在 Qoder 中打开你的项目
2. 将 `theme-material3.css` 和 `theme-material3-charts.js` 拖入项目根目录（与 HTML 同级）
3. 打开 `dashboard-release-monitor-v4.html`
4. 在 `</style>` 下方添加 CSS 引用（第 2 步）
5. 在 `</body>` 上方添加 JS 引用（第 3 步）
6. 保存并预览

---

## 常见问题

**Q: 图表颜色没变？**
A: 确保 `theme-material3-charts.js` 在所有 ECharts 脚本之后加载。它会在 5 秒内自动检测并更新所有图表实例的颜色。

**Q: 想微调某个颜色？**
A: 编辑 `theme-material3.css` 顶部的 `:root` 变量即可全局生效。例如把 `--accent:#4285f4` 改成你想要的蓝色。

**Q: 想同时保留多个风格可切换？**
A: 可以做多套主题文件（theme-apple.css / theme-dark-tech.css 等），通过 JS 动态切换 `<link>` 的 href 即可实现一键换肤。
