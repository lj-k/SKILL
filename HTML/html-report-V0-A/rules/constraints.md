# 约束清单（html-report-V0-A）

> 本文件汇总所有约束，按"绘图 / 模态查看器 / 目录 / 正文 / 校验 / 版本号 / 文件结构"分类。
> 每条含编号（与用户原始要求一致）+ 规则 + 禁止项 + 落地方式。`SKILL.md` 为速览，本文件为权威。

## 定位（官方 skill 优先，本文件为其补充/约束）

本 skill 是**官方 html/image 类 skill 的补充与约束层**，不重复造轮子：

- **模态图片查看器 / 图形查看**：调用 **`modal-image-viewer-skill`**（按名字，AI 自行定位）。本 skill 随附其适配副本（`_shared/js/modal.js`、`_shared/css/modal.css`）以保证开箱即用，并施加以下约束覆盖。
- **契约覆盖（类同 1.2）**：`modal-image-viewer-skill` 的权威 `modal.js` 假设渲染后的 Mermaid SVG 位于 `.mermaid` 内；本 skill 的 `diagrams.js` 把 SVG 注入 `.mermaid-wrap`（隐藏 `<pre>` 的同级兄弟）。此 DOM 位置差异属本 skill 的**契约覆盖**，故 `modal.js` 用兜底选择器 `.mermaid-wrap > svg || .mermaid svg || svg` 兼容（见 1.9）；编辑任一侧时须保持该契约一致，否则模态"不显示图片"（见 html-frontend-checker 已知陷阱 SVG-not-shown-in-modal）。
- **HTML 前端校验**：调用 **`html-frontend-checker-skill`**（按名字）做 80+ 项检查；本 skill 的 `validate.py` 作为轻量交付前校验并行使用。
- **本 skill 独有贡献**：动态目录/折叠/引用悬停、版本单一来源、文件结构约定、样式令牌规范、脚手架与校验脚本。

> ⚠️ 约束与官方 skill 冲突时，以本文件编号为**准**（例如 1.2 要求透明背景，覆盖 `modal-image-viewer-skill` 默认的深色遮罩）。

---

## 0. 绘图要求

| # | 规则 | 禁止 | 落地 |
|---|------|------|------|
| 0.1 | 含文字的图形应使用**低饱和度底色**，不影响阅读 | 高饱和/刺眼底色 | `report.css` `--shape-fill:#f6f8fa`；Mermaid `themeVariables.primaryColor` |
| 0.2 | 绘制框图后，应当对框图的**连线、箭头进行复查**，避免显示与意图不一致或错误 | 不复核即交付 | 人工复核 + `tests/` 用例；callout warning 提示 |
| 0.3 | 箭头端点须在**可见框体边沿**，禁空白区孤点 / 共享空白 hub；**箭头应与所连框体的边线垂直**（垂直指向边界，避免斜切或悬空） | 箭头落在空白 / 斜穿边线 / 悬空 | Mermaid 原生吸附节点边界；非 Mermaid 手工图须让箭头正交（垂直）指向框体边线，交付前复查（0.2） |
| 0.4 | 架构框图的连线应使用**直角连线**，不遮蔽图形，连线上应具有**文字注释**解释信号/功能 | 斜线/曲线无注释 | `diagrams.js` `flowchart.curve='stepBefore'`；边标签用 `|文本|` |
| 0.5 | 每个 `<figure>` 的 **id 必须全局唯一**，命名带章节前缀（如 `fig-<章>-<序号>`），禁止跨章节复用 id | 重复 id | `validate.py` 4.4 检测；命名约定 `fig-N-M` |

---

## 1. 图片模态查看器

| # | 规则 | 禁止 | 落地 |
|---|------|------|------|
| 1.1 | 框图/图片应当具备**查看按钮**，点击进入模态查看器拖拽和缩放 | 无查看入口 | `diagrams.js` 自动注入 `.zoom-btn`；或手写 `onclick="openImageModal('fig-x')"` |
| 1.2 | 模态窗口背景使用 **transparent（完全透明）**，禁止任何有色遮罩遮挡正文阅读 | `rgba(0,0,0,.5)` 等遮罩 | `.img-modal{background:transparent !important}`（在 report.css 覆盖 `modal-image-viewer-skill` 默认的 `rgba(0,0,0,.55)`） |
| 1.3 | 全屏无限制显示，**不得设置 max-width/max-height** 限制缩放时的显示范围 | 对 `.img-stage svg` 设 max 上限 | `report.css` 仅设 `padding`，不限制尺寸 |
| 1.4 | 图形区域设置**白色背景**（`background:#fff; padding:20px; border-radius:4px`） | 透明/异色图形区 | `.img-stage` 样式 |
| 1.5 | 关闭：点击模态**空白区域（非 SVG 区域）**可关闭；提供 ✕ 按钮；支持 **ESC** | 仅按钮可关 | `modal.js` `modal.addEventListener click` + keydown Escape |
| 1.6 | 缩放：提供 **+/-/重置** 按钮，支持**鼠标拖拽平移**和**滚轮缩放** | 仅一种缩放方式 | `modal.js` 按钮 + wheel + drag |
| 1.7 | 图片标题：header 和 controls 使用 **absolute 定位浮于图片上方，半透明背景** | 固定顶栏遮挡 | `.img-modal-header{position:absolute;background:rgba(255,255,255,.7)}` |
| 1.8 | 切换：提供左右切换按钮（‹/›），在 header 标题后、关闭 X 左侧；收集页面所有 `figure.diagram`，点击查看时计算索引；**首尾自动 disabled** | 无切换/未禁用首尾 | `modal.js` `collect()` + `bPrev/bNext.disabled` |
| 1.9 | 点击查看后应当**完整显示整个图片**，一维刚好铺满，另一维在视口内，**优先使用 SVG 真实内容尺寸** | CSS 默认尺寸干扰 | `modal.js` 用 `viewBox` 计算等比缩放；**模态 SVG 源位于 `.mermaid-wrap > svg`**（diagrams.js 将渲染 SVG 作为隐藏 `<pre>` 的同级兄弟注入，不在 `.mermaid` 内），查找须 `.mermaid-wrap > svg \|\| .mermaid svg \|\| svg` 兜底 |
| 1.10 | `openImageModal('X')` 的实参 X 必须与唯一 `id="X"` 一一对应；SVG 克隆的 `deduplicateSvgId` 与 figure 级 id 约束是**两套独立检查**，不可互相替代 | 实参与 id 不对应 | `validate.py` 4.4（figure 级）+ `modal.js` `deduplicateSvgId`（SVG 内部） |

---

## 2. 目录要求

| # | 规则 | 禁止 | 落地 |
|---|------|------|------|
| 2.1 | 必须同时具备 **ToC 和可隐藏的侧边目录**；更新文档时同步更新；交付前复核 | 仅一种目录 | `toc.js` 生成 `#toc-list`(侧边) + `.mobile-toc-panel`(移动) |
| 2.2 | 侧边目录无需标题折叠，每个标题**独占一行**，超长标题**截断显示省略号** | 标题换行/溢出 | `.toc-link{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}` |
| 2.3 | 侧边目录应当支持**滚动高亮（scroll-spy）**，激活项后自动滚动侧边栏使其位于可视区中央 | 高亮不随动 | `toc.js` `onScroll` + `centerActive` |
| 2.4 | 侧边目录内部无需标题折叠 | 内部再折叠 | — |
| 2.5 | 固定/吸顶左侧边栏时，避免遮挡正文：正文 `margin-left`（=侧栏宽） + `overflow-x:hidden`；`html,body` 同设 `overflow-x:hidden`；**表格 `table-layout:fixed`** | 正文被遮/表格溢出 | `report.css` 布局规则 |
| 2.6 | 目录高亮应考虑**正文折叠造成的位置漂移** | 折叠后高亮错位 | `collapse.js` 折叠后 `setTimeout(__tocRefresh,320)` |
| 2.7 | 窄屏时侧边目录收缩为**下方目录**：仅显示**目录按钮（FAB）**，点击才展开底部面板；面板展开后**固定视口底**（`position:fixed;bottom:0`，非页面底部）；**宽屏（>768px）移动端目录必须强制隐藏** | 窄屏直接显示目录（未先显按钮）/ 面板在页面底随滚动 / 宽窗残留底部目录 | 落地（JS 权威优先于 CSS）：`toc.js` `openMobilePanel/CloseMobilePanel` 用内联 `display:flex/none` 控制面板显隐、`syncMobileToc()` 按 `innerWidth` 窄屏显 FAB/宽屏隐藏（resize+初始化各调用一次）；面板 `position:fixed;left/right:0;bottom:0` 由 JS 强制定位；`report.html` 结构 FAB 置于 `.fab-stack` 内、面板独立于其后；`report.css` 仅提供外观（`.mobile-toc-panel{display:none}` 兜底 + `.open{transform:translateY(0)}` 滑入、`height:25vh`、`border-top:2px accent`、`border-radius:12px 12px 0 0`） |
| 2.8 | 目录应收纳**所有级别标题**，并可设置**固定显示级别 / 滚动到显示级别** | 漏级/不可调 | `toc.js` `level-fixed`/`level-scroll` 下拉 + 可见性规则 |

---

## 3. 正文要求

| # | 规则 | 禁止 | 落地 |
|---|------|------|------|
| 3.1 | 插入的代码必须**默认折叠**；折叠容器**结构统一**：`report.html` 模板用 `<pre class="code-block code-collapsed">`（`collapse.js` 驱动）；若采用 `<details class="code-block"><summary>…` 结构（成熟实现），二者择一、不得混用 | 裸 `<pre><code>` 无折叠容器 / 两种结构混用 | `report.html` 用 `pre.code-block.code-collapsed`；`report-b.html` 用 `details.code-block`（自带默认折叠）；新代码块必须套用对应容器 |
| 3.2 | 各级标题必须**支持折叠本层级内容**；所有 **1/2/3 级标题应具有编号** | 标题不可折叠/无编号 | `collapse.js` + `toc.js` 自动注入 `.sec-num` |
| 3.2a | **文档主标题（doc-title）不是章节标题**：应使用 `<div class="doc-title">` 而非 `<h1>`，避免被 `toc.js` 自动编号、混入章节序号（如被误编为"1"） | 用 `<h1>` 当文档标题导致与第一章抢编号 | `report.html` 的 `.doc-title` 用 div；章节用 `.section > h1` |
| 3.3 | 若无特别要求，应使用**白色或无色**作为文档底色 | 深色/花底 | `report.css` `--bg:#fff` |
| 3.4 | 文内参考文献引用（`[1]`、作者、文档内跳转）应支持**鼠标悬停弹出浮动窗口**预览目标 | 无预览 | `toc.js` `initLinkTooltip` |
| 3.5 | 使用**系统默认字体**，非用户要求不要引入其他字体 | 引入外部字体 | `report.css` `--font` 系统栈 |
| 3.6 | 显示标签字面文本时必须使用 **HTML 实体转义** | 裸写 `<style>` 等 | 写作时转义 `&lt;style&gt;` |
| 3.7 | 正文宽度随视口变化，**不设最大宽度上限** | `max-width` 限制 | `report.css` `#main{width:100%}` |
| 3.8 | 插入新章节/子节时，`old_str` 不得包含目标位置之后的**总结性/收尾性块**；新内容必须插入在收尾块之前，并同步更新总结块 | 把内容插进收尾块内 | 编辑纪律（见 tests 用例） |
| 3.9 | 插入新段落/章节时，应检索插入位置上下文，确保正确、逻辑通顺、顺序正常 | 盲目插入 | 编辑纪律 |
| 3.10 | 针对用户问题，应**同时检索本地文档、代码和网络**给出更准确答案 | 仅凭记忆 | 工作流要求 |
| 3.11 | 复核发现的问题，**禁止直接在正文中指出上一版本错误**；修复后以**特别说明**形式强调错误点和正确点 | 正文内指责旧版 | 写作纪律 |
| 3.12 | 写入之前，应确认写入内容和目标文件符合要求和目的 | 未确认即写 | 工作流要求 |
| 3.13 | （同 3.11 重申）禁止正文内指出旧版错误，以特别说明强调正确点 | — | 写作纪律 |
| 3.14 | 结论必须由**清晰推理或参考代码/文档**得出 | 无依据断言 | 写作纪律 |
| 3.15 | 按钮/控件样式须**独立于容器通用样式**：如 `.fab-stack button`（0,1,1）会覆盖 `.mobile-level-btn`（0,1,0）的背景/尺寸 → 白底白字不可见。容器内专用控件用**更高优先级选择器**（如 `#mobile-level-btns .mobile-level-btn`，1,1,0） | 通用按钮选择器覆盖专用控件样式 | `report.css` `#mobile-level-btns .mobile-level-btn`；复用成熟实现的优先级写法 |
| 3.16 | **标题编号风格只能二选一**：数字点式（`1.`、`1.1`）与中文章式（`第一章`、`第1章`）**不得混用**；全文档统一一种（默认数字点式，由 `toc.js` 自动编号 `.sec-num`，正文标题本身不手写编号前缀） | 同一文档 `1.` 与 `第一章` 并存 | 正文 `<hN>` 内不写编号前缀，交给 `toc.js` 自动编号；或全用中文章式并关闭自动编号，二选一 |
| 3.17 | **Callout 颜色语义必须遵守**（低饱和底 + 彩色左边框）：`note`=说明/定义/上下文（蓝）；`tip`=技巧/推荐/最佳实践（绿）；`warning`=注意/局限/易错（橙）；`danger`=错误/禁止/严重风险（红）；默认=普通提示（灰） | 语义乱用（如 danger 表达普通提示）/ 自定义花哨底色 / 同一块叠用多态 | `report.css` `.callout` 五态；选型见 style-spec「Callout 五态」 |
| 3.18 | **不同级别标题用不同竖条样式区分**（border-left 粗细+颜色）：h1=accent 6px；h2=accent2 4px；h3=muted 3px；h4=border 2px；各带左内边距 | 一二级标题竖条相同难以区分 | `report.css` `.section > hN` 竖条规则；`--accent2:#7c3aed` token |

---

## 4. 校验

| # | 规则 | 命令/方法 | 期望 |
|---|------|-----------|------|
| 4.1 | 每个章节 `<div>` 开闭严格配对 | `grep -oP '<div\b' f\|wc -l` 与 `grep -oP '</div>' f\|wc -l` 比对 | 相等 |
| 4.2 | 截断行检测 | `grep -P '</\w+\s*$' file.html` | **0 行** |
| 4.3 | 标签平衡校验，无残留/错误 | `scripts/validate.py` 的 `TagChecker` 栈式解析 | 无错配 |
| 4.4 | 重复 id 检测（必空输出） | `grep -oP 'id="fig-[^"]*"' f\|sort\|uniq -d`（figure 级）；全文档 id 唯一 | 空 |
| 4.5 | 目录收纳所有级别标题 | `validate.py` 统计 `#main` 标题含 id 比例 | 全部有 id（缺失则 toc.js 自动补并告警） |

> 统一入口：`python3 scripts/validate.py <目录或html>`，退出码 0=全过。

---

## 5. 版本号要求

- 版本号从 **0.01 递增到 0.99**；非用户要求情况下，**禁止变更大版本或加其它后缀**（如 v1.0 / v0.20-rc）。
- 对 html 代码/文件的任何修改**应当递增版本号**。
- **正文中仅设置一处版本号变量**（`_shared/js/config.js` 的 `window.REPORT_VERSION`），避免多处版本导致漏改；侧边栏与 meta 由注入脚本读取填充。
- `CHANGELOG.md` 与 `DEV_DOC.md` 的版本号应与 HTML 一致；`CHANGELOG` 也应有版本号且与 HTML 一致。
- HTML 正文**不保存变更记录**（变更历史只在 CHANGELOG）。

---

## 6. 文件结构要求

- 为报告创建**同名父文件夹**，包含：
  - `共享文件夹`（如 `_shared/`：js 脚本、css）
  - `html 报告正文`（`<name>.html`）
  - `CHANGELOG.md`
  - `DEV_DOC.md`
- `CHANGELOG.md`：每次更新文档必须同步更新；HTML 正文不保存变更记录；CHANGELOG 应有版本号且与 HTML 一致。
- `DEV_DOC.md`：应包含**每次对话的用户要求、答复**；含 html 开发目的、组织架构、大纲等；其余按需添加。
- **交付形态（内置脚本要求）**：**生成/交付报告时，应将交互脚本（toc/collapse/modal/diagrams/版本注入）与全部样式**内联进 HTML（`<style>` + `<script>` 直接写在 `<head>`/`</body>` 前），**禁止外链 `_shared/`**。原因：报告单文件化后可独立分发/长期存档，不依赖外部文件树。落地：
  - 参照 `report-b.html`（当前即内联形态）或把 `_shared/js/*.js` 与 `_shared/css/*.css` 内容合并进 `<name>.html`；
  - 版本号来源仍为 config.js 的 `REPORT_VERSION`，合并时将该变量值写入内联脚本并在正文标记一处；
  - `_shared/` 保留为**开发态**资源，交付前合并，**不要求**随报告分发。

---

## 7. 模板复用与维护约束（防"重写而非应用"）

> 本 skill 的 Bug1/Bug2 根因：创建 skill（v0.02）时 AI **按规则散文重新实现**了 modal.js / 移动端目录，而非**直接复用**经多版打磨的模板实现，导致 DOM 契约/隐藏机制偏离，约束与校验未能覆盖。

| # | 规则 | 禁止 | 落地 |
|---|------|------|------|
| 7.1 | 集成 / 生成报告时，**优先直接复用经核实的参考实现**（如 参考实现 的模态查看器、移动端目录），模板文件即权威实现 | 凭规则散文**重新实现**等价逻辑 | 调用 `scaffold.py` 直接复制 `_shared/`；非必要不重写 |
| 7.2 | 维护 / 增强模板时，须**逐条 diff 对照**现有实现再改，且**附修改理由** | 整段重写、静默替换、凭记忆补全 | 编辑纪律；diff 旧/新片段后再改 |
| 7.3 | 规则以**可验证的显式契约**表达（含具体选择器 / 属性 / z-index），而非仅描述行为 | 仅写"应可折叠""应透明"等模糊要求 | 1.9 / 2.7 已列具体选择器与值；新增规则须同此粒度 |
| 7.4 | 交付前**必须运行事后检查**：本 skill `validate.py` + 外部 `html-frontend-checker-skill`（SVG-not-shown-in-modal 等已知陷阱） | 仅人工目测 | 交付流程闸门（见 4.6/4.7/4.8） |

> **是否会"用本 skill 也发生"**：① **应用 skill（scaffold）时不会**——直接复制模板，无重写，bug 不会出现；② **风险在 skill 创建 / 模板维护时**——若后续让 AI "优化模板"而重写，可能再次偏离。故 7.1/7.2 同时约束"创建"与"维护"两阶段。
