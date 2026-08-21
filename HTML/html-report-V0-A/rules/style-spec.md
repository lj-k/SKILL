# 样式规范（style-spec，html-report-V0-A）

> 所有样式集中在 `templates/_shared/css/report.css`，由 CSS 变量（token）统一驱动，便于全局调整。
> 本文件是"规定"，`report.css` 是其实现。新增样式请先改本文件的 token，再在 css 中引用。

---

## 1. 颜色令牌（低饱和度原则）

| Token | 值 | 用途 | 对应规则 |
|-------|-----|------|----------|
| `--bg` | `#ffffff` | 文档底色（白/无色） | 3.3 |
| `--fg` | `#1f2937` | 正文文字 | — |
| `--muted` | `#6b7280` | 次要文字/说明 | — |
| `--accent` | `#3b6cb7` | 强调/链接/激活态（低饱和蓝）；**h1 竖条** | 3.2 |
| `--accent-weak` | `#eef2ff` | 激活态浅底/表头底 | — |
| `--border` | `#e5e7eb` | 边框/分隔 | — |
| `--code-bg` | `#f6f8fa` | 代码块底 | 3.1 |
| `--shape-fill` | `#f6f8fa` | 含文字图形节点底（低饱和） | 0.1 |
| `--shape-fill2` | `#fef9c3` | 高亮图形节点底（低饱和黄） | 0.1 |
| `--shape-stroke` | `#6b7280` | 图形描边/连线 | 0.3/0.4 |

### Callout 五态（低饱和底 + 彩色左边框）——颜色语义严格约束（见 constraints 3.17）
| 类 | 左边框 | 背景 | 语义 | 适用场景 |
|----|--------|------|------|----------|
| `.callout` | `--muted` | `#f9fafb` | 默认 | 普通补充说明 |
| `.callout.note` | `--accent` | `--accent-weak` | 说明 | 定义、背景、上下文、引用来源（使用最频繁） |
| `.callout.tip` | `#10b981` | `#ecfdf5` | 正向/建议 | 技巧、推荐做法、最佳实践、优化建议 |
| `.callout.warning` | `#f59e0b` | `#fffbeb` | 注意/局限 | 潜在风险、局限、易错点、需要警惕处 |
| `.callout.danger` | `#ef4444` | `#fef2f2` | 风险/禁止 | 错误、禁止项、严重风险、必须避免项 |

> 禁止：语义乱用（如用 danger 表达普通提示）；自定义其它边框色/花哨底色；同一块内叠用多态。

### 模态查看器
> 模态样式**来自 `modal-image-viewer-skill` 的 `modal.css`**（本 skill 随附适配副本），`report.css` 在其后加载并施加约束覆盖。

| 元素 | 属性（本 skill 约束） | 对应规则 |
|------|------|----------|
| `.img-modal` | `background: transparent !important`（覆盖 modal-image-viewer-skill 的 `rgba(0,0,0,.55)` 深色遮罩） | 1.2 |
| `.img-stage` | `background:#fff; padding:20px; border-radius:4px` | 1.4 |
| `.img-stage svg` | **不设 max-width/max-height**（仅 `90vw/85vh` 上限由 modal.css 控） | 1.3 |
| `.img-modal-toolbar` | `position:absolute; top:12px; background:rgba(255,255,255,.9)` 半透明浮于图片上方 | 1.7 |

---

## 2. 字体

- **系统默认字体栈**（3.5，不引入外部字体）：
  ```
  -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
  Arial, "PingFang SC", "Microsoft YaHei", sans-serif
  ```
- 代码块/表格/Mermaid 同用上述栈，保证中英文混排一致。
- 字号基准 `15px`，行高 `1.7`；标题 `h1 22px / h2 19px / h3 16px / h4 14px`。

---

## 3. 布局令牌

| Token | 值 | 用途 | 对应规则 |
|-------|-----|------|----------|
| `--sidebar-w` | `300px` | 侧边栏宽 | 2.5 |
| `#sidebar` | `position:fixed; width:var(--sidebar-w); height:100vh; overflow-y:auto` | 固定侧栏 | 2.5 |
| `#main` | `margin-left:var(--sidebar-w); overflow-x:hidden; width:100%` | 正文不被遮 | 2.5 |
| `html,body` | `overflow-x:hidden` | 防横向溢出 | 2.5 |
| `table` | `table-layout:fixed; width:100%` | 表格不撑破 | 2.5 |

---

## 4. 间距与圆角

- 章节间距 `.section{margin:18px 0}`；卡片/图/表 `border-radius:4–6px`。
- 图形区白底 `padding:20px`（1.4）。
- 折叠箭头 `.fold-marker{width:14px}` 旋转表示状态。

---

## 5. 图形（Mermaid）样式约定

- 节点：`fill:var(--shape-fill); stroke:var(--shape-stroke)`；高亮类 `.plan` → `fill:var(--shape-fill2)`。
- 连线直角：`diagrams.js` 设 `flowchart.curve='stepBefore'`（0.4）。
- 边标签：`|信号/功能说明|` 形式，白底 `.edgeLabel{background:#fff}`（0.4 文字注释）。
- 箭头端点：Mermaid 原生吸附节点边界（0.3）；非 Mermaid 手工 SVG 须手动对齐框体边沿。

---

## 6. 响应式断点

- `@media (max-width:768px)`：隐藏 `#sidebar`，`#main{margin-left:0}`，显示 `.mobile-toc-fab` + `.mobile-toc-panel`（2.7）。
- 模态查看器全屏 `100vw×100vh`，不受断点影响（1.3）。
