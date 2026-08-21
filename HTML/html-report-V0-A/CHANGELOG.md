# 更新日志（html-report-V0-A skill）

## 版本 v0.16

### v0.16 - 2026-08-21

- 版本升级: v0.15 → v0.16
- **修复：回到顶部与底部目录按钮仍大小不一致**：上一版虽加了统一规则 `.fab-stack button`（40px），但目录 FAB 的独立规则 `.mobile-toc-fab,#mobile-toc-fab`（specificity 1,0,0 **高于**统一规则 0,1,1）仍设 `width:44px;height:44px;font-size:18px`，层叠后 FAB 44px、回到顶部 40px，一大一小。修复：删除 FAB 独立尺寸/外观/字号，仅保留 `display` 控制（默认 none + 窄屏 flex），尺寸/背景/圆角/边框/字号（16px）全部继承统一按钮规则；统一规则字号 15px→16px。现在目录 FAB 与回到顶部**同尺寸 40px、同外观、同字号 16px**；移动端级别按钮单独 26px 小圆（有意的层级区分）。
- **校验**：模板 `scaffold.py`+`validate.py` ALL PASS（div 75/75）；确认 CSS 中无残留 44px 声明。

## 版本 v0.15

### v0.15 - 2026-08-21

- 版本升级: v0.14 → v0.15
- **二级标题竖条改浅蓝**：`.section > h2` 竖条 `var(--accent2)`（紫）→ `#60a5fa`（浅蓝），与一级标题（accent 深蓝）明显区分（3.18 落地值更新）。
- **回到顶部按钮边缘粗糙（修复）+ FAB 系样式统一**：根因按钮边框/内边距/行高未归一，浏览器默认样式残留致边缘参差。修复：`.fab-stack button,.mobile-level-btn` 统一为 accent 实心圆（`border:1px solid var(--accent); background:var(--accent); color:#fff; border-radius:50%; line-height:1; padding:0; box-shadow` + hover 微浮起）；`.mobile-level-btn` 覆盖为 26px 小圆；删除旧重复规则。
- **目录分级字号递减（从 H4 开始）**：`.toc-item[data-level="4"] .toc-link` 11.5px、`[data-level="5"/"6"]` 10.5px，弱化颜色（`--muted`），active 复原白字。
- **关键词样式 `mark.key`**：`background:none; color:var(--accent); font-weight:600`（正文重点词不着底高亮，对齐成熟实现）。
- **report.html 新增 sec1-3「预置样式速览」**：演示已规定 class——`mark.key` 关键词、五态 callout（默认/note/tip/warning/danger）、标题竖条分级、目录分级字号递减。
- **校验**：`node --check` 全部 JS 通过；模板 `scaffold.py`+`validate.py` ALL PASS（div 75/75、标题 25、4.8/4.9 通过、版本一致）。

## 版本 v0.14

### v0.14 - 2026-08-21

- 版本升级: v0.13 → v0.14
- **修复：回到顶部按钮与目录 FAB 重叠**：根因 `.mobile-toc-fab` 自带 `position:fixed;bottom:24px;right:24px`，而它又位于 `.fab-stack`（fixed + flex column）内 → 脱离流与 `#back-to-top` 重叠。修复：FAB 去掉 fixed 定位，回到 `.fab-stack` 流内排列（与成熟实现一致），与回到顶部/级别按钮纵向等距。
- **标题竖条分级（约束 3.18）**：h1=accent 6px 蓝粗 / h2=accent2 4px 紫 / h3=muted 3px 灰 / h4=border 2px 灰细，各带左内边距；`:root` 新增 `--accent2:#7c3aed` token（style-spec 同步）。
- **Callout 颜色语义约束（约束 3.17）**：note=说明/上下文（蓝）；tip=技巧/推荐（绿）；warning=注意/局限（橙）；danger=错误/禁止（红）；默认=普通提示（灰）。style-spec「Callout 五态」表补适用场景与禁止项（禁语义乱用/自定义花哨底色/叠用多态）。
- **校验**：`node --check` 全部 JS 通过；模板 `scaffold.py`+`validate.py` ALL PASS（div 64/64、4.6/4.7/4.8/4.9 通过、版本一致）。

## 版本 v0.13

### v0.13 - 2026-08-21

- 版本升级: v0.12 → v0.13
- **模板移植成熟实现 4 个优点（report 模板）**：
  1. **目录可见性精细规则（例1/例2/例3）**：`toc.js isVisible` 移植——固定骨架（≤fixedLevel）、活动路径（≤scrollLevel）、路径节点直接子节点展开（父级≥fixedLevel 且自身≤scrollLevel）；滚动级别 ≤ 固定级别时不生效。
  2. **引用悬停改事件委托**：`initLinkTooltip` 用 `document` 级 `mouseover/mousemove/mouseout` 委托（跳过 `.toc-link`），兼容动态目录/折叠生成链接。
  3. **回到顶部滚动显隐**：`#back-to-top` 由 `initBackToTop` 控制 `.visible`（scrollY>300 显示）；`report.css` 加 `#back-to-top{display:none}` + `.visible` 样式。
  4. **移动端面板目录少时高度自适应**：`openMobilePanel` 按 `mobile-toc-list` 项数设 `height = items*1.7+4 vh`（下限 10 / 上限 25，≤1/3 视口）。
- **report-b 脚本替换为模板脚本（共享 `templates/_shared/`）**：删除 V1A 内联 `<style>` 与全部内联 JS（mermaid 直角 DOM 手术/自研 modal/initCollapse/initToc 等，残留=0），改引 `_shared/css/{modal,report}.css` + `_shared/js/{config,toc,collapse,modal,diagrams}.js`；正文重构为 `.section`+`.section-content` 嵌套契约；代码块改 `pre[data-title]`；目录容器改 `<nav id="toc-list" class="toc-root">` / `#mobile-toc-list`；删 V1A 静态 `#link-tooltip`（模板 JS 动态创建）；补 `#version-sidebar`/`#version-meta` 注入点；doc-title 措辞统一。
- **修复 CSS id/class 契约不匹配（深层隐患）**：模板 `report.html` 的移动端目录用 **id**（`#mobile-toc-fab/#mobile-toc-panel/#mobile-toc-body`），而 `report.css` 原只写 **class** 选择器（`.mobile-toc-*`），导致面板视觉样式从未生效（样式全靠 toc.js 内联兜底）。修复：选择器改为同时匹配 class 与 id（`.mobile-toc-fab,#mobile-toc-fab` 等），媒体查询同步。
- **validate.py 4.8 正则兼容** `.mobile-toc-panel[^\{]*\{`（支持 `.#` 组合选择器）。
- **校验**：`node --check` 全部 JS 通过；模板 `scaffold.py`+`validate.py` ALL PASS（div 64/64、标题 20、4.6/4.7/4.8/4.9 通过、版本一致）；`report-b.html` 4.1–4.9 全 PASS（div 38/38、截断 0、标签平衡、id 唯一、资源存在、旧脚本残留 0）；report-b VER FAIL 为预期（模板非独立工程，共享 `_shared`，config.js 版本单一来源已生效）。

## 版本 v0.12

### v0.12 - 2026-08-21

- 版本升级: v0.11 → v0.12
- **模板：目录重复显示标题序号（修复）**：根因 `buildTree()` 的 `n.title = h.textContent`，折叠触发 `__tocRefresh` 再次建树时，标题内已注入 `.sec-num` span，`n.title` 带序号文本 → 目录条目变 `n.number + " " + title` 重复。修复：建树时剔除标题内 `.sec-num` span 文本。
- **模板：底部目录高度限制（新增）**：`.mobile-toc-panel` 加 `max-height:33vh`（不超过视口 1/3），`toc.js openMobilePanel` 内联 `maxHeight='33vh'` JS 权威兜底；`height:25vh` 保留（≤1/3）。
- **report-b：正文标题折叠失效（修复）**：根因成熟实现的折叠脚本（`initCollapse`）要求标题的 `nextElementSibling` 为 `.section-content` 容器，而复制生成时正文是裸 `<h1><p>` 平铺结构，无该容器 → 点击不折叠。修复：将 report-b 通用正文重写为**嵌套 `.section-content` 结构**（`h1+div.section-content > h2+div.section-content > h3+div.section-content`，与成熟实现折叠契约一致），含表格/代码块/figure。
- **校验**：`node --check` 全部 JS 通过；模板 `scaffold.py`+`validate.py` ALL PASS（div 64/64、标题 20、4.6/4.7/4.8/4.9 通过、版本一致）；`report-b.html` div 35/35、截断 0、section-content 6、4.9 通过。

## 版本 v0.11

### v0.11 - 2026-08-21

- 版本升级: v0.10 → v0.11
- **模板（report.html）四项改进**：
  1. **侧栏级别切换改为按钮 + 下拉菜单（同行）**：对齐成熟实现 `.toc-controls > .toc-ctrl > .toc-btn + .toc-menu` 结构；菜单项带**标题数量统计**（`Hn (count)`，`buildTree` 统计 `levelCount`，`fillMenu(menu,key)` 渲染，V1A 风格）。
  2. **代码块标题**：`pre[data-title]` 由 `collapse.js` 生成 `.code-title` 标题栏（示例 sec1-2-1 已带 `data-title="示例代码：唯一版本号来源（config.js）"`）；`report.css` 新增 `.code-title` 样式。
  3. **新增第 3、4 章多级标题**（h1/h2/h3，标题总数 20）供长目录 / 滚动高亮 / 折叠测试。
  4. **标题编号二选一**（约束 3.16）：模板 h1 去掉手写"第一章/第二章…"前缀，统一由 `toc.js` 自动编号，避免"1 第一章"叠加混用。
- **report-b 移动端面板高度自适应**：目录项少时自动降低面板高度（`items*1.7+4`，下限 10vh / 上限 25vh），避免大量空白。
- **约束新增/更新（constraints.md）**：
  - 0.3：箭头端点须落在可见框体边沿，且**与框体边线垂直**（垂直指向边界，禁斜切/悬空）。
  - 3.16：标题编号风格**只能二选一**（数字点式 `1.` / 中文章式 `第一章`），不得混用。
- **校验**：`node --check` 全部 JS 通过；模板 `scaffold.py`+`validate.py` ALL PASS（div 64/64、标题 20、4.6/4.7/4.8/4.9 通过、版本一致）；`report-b.html` div 29/29、截断 0、标签平衡、4.9 通过。

## 版本 v0.10

### v0.10 - 2026-08-21

- 版本升级: v0.09 → v0.10
- **修复 1（模板级别按钮无字）**：`.fab-stack button`（specificity 0,1,1）的 `background:#fff` 覆盖 `.mobile-level-btn`（0,1,0）的 `background:var(--accent)`，导致**白底白字、文字不可见**。修复：级别按钮选择器提高为 `#mobile-level-btns .mobile-level-btn`（1,1,0），并加注释警示（新增约束 3.15）。
- **修复 2（report-b 架构示意图无图）**：从成熟实现复制时保留了本地路径 `<script src="./_shared/js/mermaid.min.js">`，但模板 `_shared/js/` 下无此文件 → mermaid 库加载失败 → 图不渲染。修复：改为 CDN（`cdn.jsdelivr.net/npm/mermaid@10`，与 `report.html` 一致）。**根因是约束缺失**：无"本地资源引用必须实际存在"检查 → 新增 `validate.py 4.9`（扫描 `src/href="./…"` 并验证文件存在，防断链回归）。
- **修复 3（report-b 代码折叠不对）**：成熟实现的折叠依赖 `<details class="code-block"><summary>` 结构，而生成示例时写了裸 `<pre><code>`，无折叠容器。修复：套用 `details.code-block`。**根因是约束 3.1 不完整**——只写"默认折叠"未规定统一结构 → 3.1 补充：折叠容器结构统一（`pre.code-block.code-collapsed` 或 `details.code-block`，二者择一不混用）。
- **校验**：模板 `scaffold.py`+`validate.py` ALL PASS（含新 4.9）；`report-b.html` div 29/29、截断 0、标签平衡、id 唯一、4.9 资源存在 PASS（VER FAIL 为预期：单文件模式无 `_shared/config.js`，不适用多文件版本机制）；`node --check` 全部 JS 通过。

## 版本 v0.09

### v0.09 - 2026-08-21

- 版本升级: v0.08 → v0.09
- **Bug2 遗留两处修复（用户反馈：窄屏弹出目录透明底 / 无级别按钮）**：
  1. **透明底**：面板 `background:#fff` 之前只写在外部 `report.css`，预览时样式未加载/被覆盖则透明。修复：`toc.js` 在 `initToggles()` 与 `openMobilePanel()` 中**内联强设 `mobilePanel.style.background='#fff'`**（与 `position:fixed` 同级权威兜底，不依赖 CSS）。
  2. **无标题级别按钮**：模板重写时漏掉了成熟实现中的移动端级别按钮（`#mobile-level-btns`）。修复：`report.html` 在 `.fab-stack` 内补 `#mobile-level-btns`（固定/滚动两个圆形按钮）；`report.css` 补样式（默认隐藏、面板打开时 `.visible` 显示、`.sel` 高亮）；`toc.js` 移植成熟实现逻辑——点击循环 H1..HmaxLevel、同步侧栏下拉、`updateVisibility()` 刷新、`open/closeMobilePanel` 同步显隐。
- **新增 `templates/report-b.html`（成熟实现直接复制版）**：按用户要求，将成熟参考实现（V1A）**直接复制**、剔除领域内容（doc-title/meta/正文标题/侧栏标题/版本号全部中性化，`V1A`/`v0.20`/`C910` 残留=0）、保留全部已验证交互结构（侧栏动态目录、固定/滚动级别按钮、移动端 FAB+底部面板、模态查看器、Mermaid、link-tooltip），仅剩两章通用示例正文。供"与模板对比 / 直接套用"使用。
- **回答"为何有参考仍做不对 / 如何给提示词"**：见下节，结论已在约束 7 中成文（优先复用、禁止重写）。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` 生成模板样例 + `validate.py` 输出 ALL PASS（div 34/34、截断 0、标签平衡、id 唯一、4.6/4.7/4.8 通过、版本一致）；`report-b.html` div 29/29、截断 0、领域残留 0。

## 版本 v0.08

### v0.08 - 2026-08-21

- 版本升级: v0.07 → v0.08
- **Bug2 移动端目录对齐成熟模板（用户反馈"窄屏直接显示目录 / 不在视口底"）**：v0.07 仍依赖 CSS 媒体查询控制显隐与定位，预览容器/样式未完全生效时失效——表现为窄屏**直接显示目录**（面板 `display:none` 未生效）、且展开后**落在页面底**（panel `position:fixed` 未生效）而非视口底。本次彻底改为 **JS 权威控制**，对齐成熟模板的 `.fab-stack` + 固定视口底面板结构：
  - `report.html`：将目录 FAB（☰）移入 `.fab-stack`（与回到顶部同组），面板 `div#mobile-toc-panel` 独立其后——结构与成熟模板一致。
  - `toc.js`：新增 `openMobilePanel()/closeMobilePanel()` 用**内联 `display:flex/none`** 权威控制面板显隐（不依赖 CSS）；`initToggles()` 内联强设面板 `position:fixed;left/right:0;bottom:0`（固定视口底，即使 report.css 未加载也生效）；`syncMobileToc()` 按 `window.innerWidth` 窄屏显 FAB、宽屏隐藏 FAB 与面板（resize 与初始化各调用一次）。FAB 兼关闭按钮（✕/☰），点击目录项 / ESC 收起。
  - `report.css`：面板仅保留外观（默认 `display:none` 兜底 + `.open{transform:translateY(0)}` 滑入、`height:25vh`、accent 顶边、圆角顶）；删除会误隐藏 FAB 的 `.fab-stack{display:none}`；宽屏 `@media(min-width:769px)` 留作冗余防御。
- **约束更新（2.7）**：明确"JS 权威控制显隐与定位、面板固定视口底、窄屏仅显 FAB"，禁止依赖 CSS 媒体查询做关键行为。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` + `validate.py` 输出 ALL PASS（div 33/33、截断 0、标签平衡、id 唯一、4.6/4.7/4.8 通过、版本一致）。

## 版本 v0.07

### v0.07 - 2026-08-21

- 版本升级: v0.06 → v0.07
- **Bug1 真正修复（宽屏仍显示底部目录）**：v0.05/0.06 仅靠 CSS 媒体查询 `@media(min-width:769px)` 隐藏，仍出现"宽屏显示"——媒体查询依赖渲染视口（预览容器/样式未生效时不可靠）。本次改为**双重保证**：恢复 `toc.js` 的 `syncMobileToc()`，在初始化与每次 `resize` 时若 `window.innerWidth>768` 即对内联 `display:none`（优先级高于样式表非 `!important` 规则）强制隐藏 FAB 与面板并移除 `.open`；窄屏交还 CSS 显示。CSS 媒体查询保留为冗余防御。scaffold 产物已验证（宽屏内联 `display:none` 生效）。
- **第 2 点：清除 skill 内外部参考名**：用户指出应用本 skill 只参考 `report.html`，不应提及任何外部参考（如 V1A）。已将 `constraints.md` / `CHANGELOG.md` / `report.css` / `toc.js` / `validate.py` 中所有"V1A"引用清除，统一中性表述为"模板实现 / 参考实现"，并清理替换产生的冗余措辞。第 7 节约束（优先复用模板、禁止凭散文重写）保留。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS（div 33/33、截断 0、标签平衡、id 唯一、4.6/4.7/4.8 通过、版本一致）。

## 版本 v0.06

### v0.06 - 2026-08-21

- 版本升级: v0.05 → v0.06
- **Bug2 真正对齐 参考实现（z-index 覆盖问题）**：v0.05 改了面板默认隐藏机制，但残留一处关键差异——面板 `z-index:1004` > FAB `1003`，**展开后面板盖住 FAB**，☰/✕ 被遮、无法点击关闭，与 参考实现（面板 1001 < FAB 1003，FAB 始终浮于面板之上）"不一样"。修复：面板 `z-index` 降到 **1002**（低于 FAB 1003），展开时 ✕ 浮于面板上方可点击关闭；`toc.js` 补齐 参考实现 行为——**点击面板内链接收起** + **ESC 关闭**。scaffold 产物已验证（面板 `display:none` 默认 + `.open` 切换、FAB/面板 z-index 关系、无 header，与 参考实现 一致）。
- **Bug2.1 约束（为什么 AI 倾向重写而非应用）**：根因是 skill 创建（v0.02）时 AI 按规则**散文重新实现** modal.js / 移动端目录，而非直接复用经打磨的 参考实现 代码，导致 DOM 契约/隐藏机制偏离。约束结论：① 应用 skill（scaffold）只会复制模板、不重写，**不会发生**；② 风险在 skill 创建/模板维护阶段，若让 AI 重写则可能再现。新增 **`constraints.md` 第 7 节**：7.1 优先复用经核实实现、禁止凭散文重写；7.2 维护须逐条 diff 并附理由；7.3 规则须为可验证显式契约（具体选择器/属性/z-index）；7.4 交付前必跑 `validate.py` + `html-frontend-checker-skill` 作为闸门。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS（div 33/33、截断 0、标签平衡、id 唯一、4.6/4.7/4.8 通过、版本一致）。

## 版本 v0.05

### v0.05 - 2026-08-21

- 版本升级: v0.04 → v0.05
- **Bug2 视觉修正（对齐成熟模板实现）**：v0.04 只解决了"宽屏不出现"，但面板"样子不对"。根因：模板是 skill 创建时**AI 重写**而非复制成熟模板，引入了脆弱/偏离机制：① 面板用 `display:flex` 默认 + `transform` 隐藏（模板用 `display:none` 默认 + `.open` 切换）；② 面板带模板已删除的蓝色 header 栏；③ 无 `border-radius` 圆角顶、顶边为 1px 灰边（模板为 2px accent + 12px 圆角顶）；④ 高度 45vh（模板 25vh）；⑤ `toc.js` 用内联 `display` 黑科技控制显隐（模板纯 CSS 媒体查询 + class 切换）。本次回退对齐模板实现：
  - `report.css`：`.mobile-toc-panel{display:none}` + `.open{display:flex;transform:translateY(0)}`；`height:25vh`；`border-top:2px solid var(--accent)`；`border-radius:12px 12px 0 0`；删除 `.mobile-toc-head`；FAB 44px；新增移动端 `.toc-link` active 样式。
  - `report.html`：删除面板 header，FAB 自身兼作关闭按钮（展开显示 ✕）。
  - `toc.js`：移除 `syncMobileToc` 内联 display 黑科技，仅 FAB 切换 `.open` + ✕/☰，resize 宽屏收起（显示由 CSS 媒体查询权威控制，与 参考实现 一致）。
- **新增事后检查（validate.py 4.8）**：检测 `.mobile-toc-panel` 默认 `display:none` 且 FAB 在 `@media(max-width:768px)` 显示 `display:flex`，防止回归到 `display:flex` 默认 + transform 隐藏的脆弱机制。
- **约束更新（2.7）**：明确"面板默认 display:none、仅 .open 时 flex"的 参考实现 机制，禁止 `display:flex` 默认 + transform 隐藏。
- **回答"为何 参考实现 好、模板有 bug"**：模板在 skill 创建时被 AI 重新实现（而非复制 参考实现 经过多版打磨的代码），在模态查看器、移动端目录两处引入了与原稿不同的 DOM 契约/隐藏机制，导致约束与校验未能覆盖（Bug1 的 SVG 注入位置契约、Bug2 的面板默认隐藏机制当时均未显式成文，且 `html-frontend-checker` 的"SVG not shown in modal"未作为交付闸门运行）。结论：**约束与检查确实不足**——现已通过 1.9/2.7 成文 + validate.py 4.6/4.7/4.8 闸门补齐。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` + `validate.py` 输出 ALL PASS（div 33/33、截断 0、标签平衡、id 唯一、4.6/4.7/4.8 通过、版本一致）。

## 版本 v0.04

### v0.04 - 2026-08-21

- 版本升级: v0.03 → v0.04
- **三个 skill 约束复核（用户要求：如何更新 skill 避免此类问题）**：
  - `modal-image-viewer-skill`（v1.04）：其权威 `modal.js` 假设 Mermaid SVG 位于 `.mermaid` 内（`SKILL.md` 3.3.1）；本 skill 的 `diagrams.js` 注入到 `.mermaid-wrap`（隐藏 `<pre>` 同级兄弟）——**DOM 契约不一致**是"点击查看不显示图片"的根因；其"已知陷阱"已含 `SVG not shown in modal` 模式，是最合适的外部事后检查（应调用 `html-frontend-checker-skill`）。
  - `html-report-V0-A`（v0.03）：`constraints.md` 1.9 / 2.7 已记录两条约束，v0.03 已做模板级修复。
  - `html-frontend-checker-skill`：diagram 类已覆盖 `SVG not shown in modal` / `zoom/drag failures`，作为外部事后检查。
  - **更新策略（通用性/稳定性/可靠性优先）**：① 模板级——最可靠、解耦具体 DOM 位置（modal.js 兜底查找 / 移动端目录 JS 权威显隐）；② 规则级——文档化契约（1.9 已记）；③ 事后检查——`validate.py` 新增 4.6/4.7 防回归。三者叠加，避免"改一处破坏另一处"。
- **修复「底部目录仍宽屏出现」（Bug2，强化可靠性）**：原仅 `report.css` 宽屏 `display:none` + `toc.js` resize 收起，依赖 CSS 媒体查询与 `.open` 态，若报告副本的 `report.css` 未同步仍会残留。改为 **`toc.js` JS 权威控制**：新增 `syncMobileToc()`，初始化与每次 resize 时若 `innerWidth>768` 则对 FAB/面板设内联 `display:none` 并移除 `.open`，否则交还 CSS（窄屏显示）。即使 `report.css` 陈旧，只要 `toc.js` 生效即隐藏（宽屏内联 `display:none` 优先级高于样式表非 `!important` 规则）。`report.css` 的 `@media(min-width:769px){display:none!important}` 保留为冗余防御。
- **新增事后检查（`validate.py`）**：
  - `4.6` 跨文件契约：检测 `_shared/js/modal.js` 的 SVG 源查找含 `.mermaid-wrap` 或 `.mermaid svg` 兜底，防回归到仅查固定位置导致"模态不显示图片"。
  - `4.7` 宽屏隐藏：检测 `report.css` 含 `@media (min-width:769px)` 且含 `display:none`，防宽窗残留底部目录。
- **约束文档补充**：`constraints.md`「定位」段新增"契约覆盖"说明——`diagrams.js` 将 Mermaid SVG 注入 `.mermaid-wrap` 相对 `modal-image-viewer-skill` 的 `.mermaid` 约定是类同 1.2 的覆盖，编辑任一侧须保持契约一致。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS（div 34/34、截断 0、标签平衡、id 唯一、4.6/4.7 通过、版本一致）。

## 版本 v0.03

### v0.03 - 2026-08-21

- 版本升级: v0.02 → v0.03
- **修复「图片查看器点击查看后不显示图片」（Bug1）**：根因为 `modal.js` 的 `showModalContent` 用 `fig.querySelector('.mermaid').querySelector('svg')` 找图，但 `diagrams.js` 把 Mermaid 渲染出的 SVG 以**兄弟节点**方式注入 `.mermaid-wrap`（`<pre class="mermaid">` 被隐藏），SVG 并不在 `.mermaid` 内部，故查到 `null`、舞台空白。改为 `fig.querySelector('.mermaid-wrap > svg') || fig.querySelector('.mermaid svg') || fig.querySelector('svg')` 三级兜底查找（约束 1.9 落地：优先使用 SVG 真实内容）。ECharts 分支结构不变。
- **修复「底部目录在宽窗口出现」（Bug2）**：原仅用 `transform:translateY(100%)` 隐藏面板，窄屏打开后拉宽窗口会残留 `.open` 态覆盖正文。修复：(1) `report.css` 新增 `@media (min-width:769px)` 宽屏**强制 `display:none`**（FAB + 面板，含 `!important`）；(2) `toc.js` 新增 resize 监听，窗口 >768px 时调用 `closeMobilePanel()` 收起（规则 2.7 强化）。
- **约束补充**：`constraints.md` 在 1.9 / 2.7 处标注"模态 SVG 源位于 `.mermaid-wrap > svg`""宽屏强制隐藏移动端目录"。
- **校验**：5 个 JS `node --check` 通过；`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS（div 34/34、截断 0、标签平衡、id 唯一、版本一致）。

## 版本 v0.02

### v0.02 - 2026-08-21

- 版本升级: v0.01 → v0.02
- **定位重述（用户要求 #5）**：明确本 skill 是官方 html/image 类 skill 的**补充与约束层**——模态图片查看器与图形查看调用 **`modal-image-viewer-skill`**（按名字，AI 自行定位，不写路径），HTML 前端校验调用 **`html-frontend-checker-skill`**；本 skill 在其上补充动态目录/折叠/版本单一来源/文件结构/样式约束，并施加约束覆盖（如 1.2 透明背景）。
- **模态查看器改为调用 `modal-image-viewer-skill`（用户要求 #1）**：移除自研 `modal.js`，改用该 skill 的权威实现（`_shared/js/modal.js`、`_shared/css/modal.css` 随附适配副本，保证 scaffold 开箱即用）；`report.css` 在其后加载并覆盖：**1.2 遮罩透明**（覆盖该 skill 默认的 `rgba(0,0,0,.55)` 深色遮罩）、**1.4 白底图形区**。`SKILL.md`/`constraints.md`/`style-spec.md` 已加"定位与依赖"并标注调用方式仅给名字。
- **修复 `templates/report.html` 4 个 bug（用户报告）**：
  1. **文档主标题被误编为 H1 序号**：`通用技术报告模板` 原用 `<h1 class="doc-title">` 被 `toc.js` 自动编号"1"。改为 `<div class="doc-title">`（非标题元素），不再进入目录/编号；章节标题仍用 `.section > h1` 正常编号（新增约束 3.2a）。
  2. **移动端目录异常**：原 `.mobile-toc-panel` 固定定位/折叠/窄屏触发有误，表现为"一直在页面最下方、无法折叠、不固定占视口下方"。重写为 `position:fixed; bottom:0; transform:translateY(100%)` 默认滑出视口、`.open` 滑入、含标题栏 + ✕ 关闭按钮、点击目录项自动收起；窄屏（≤768px）才显示 FAB，宽屏隐藏（2.7）。
  3. **图形绘制应调用相关 skill（用户要求 #3）**：SVG/Mermaid 图形结构与查看器统一引用 `modal-image-viewer-skill` 的 `figure.html` 与 `openImageModal` 约定；`diagrams.js` 仅保留页面侧 Mermaid 渲染（在 modal 克隆 SVG 前完成）。
  4. **点击查看后灰底白字（bug #4）**：原自研 modal 克隆 SVG 后尺寸/背景处理不当。改用 `modal-image-viewer-skill` 的 `deduplicateSvgId` + viewBox 等比缩放 + 白底图形区，渲染正常（无灰底白字）。
- **校验**：`node --check` 全部 JS 通过；`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS（div 34/34、截断 0、标签平衡、id 唯一、版本一致）。

## 版本 v0.01

### v0.01 - 2026-08-21

- 初始版本：基于用户对话中沉淀的 HTML 报告规范（绘图/模态查看器/目录/正文/校验/版本号/文件结构），构建"指令 + 模板 + 脚本 + 规则 + 测试用例"五段式通用 skill。
- **模板 `templates/`**：
  - `report.html`：完整报告骨架，接线所有 JS/CSS，含示例章节/图形/表格/代码块/提示块，展示全部特性。
  - `_shared/css/report.css`：集中样式（低饱和色板、系统字体、固定侧栏+正文 margin、table-layout:fixed、透明模态+白底图形区、callout 四态、移动端目录）。
  - `_shared/js/config.js`：**唯一版本号来源** `window.REPORT_VERSION`（正文仅此一处版本变量）。
  - `_shared/js/toc.js`：动态目录 + scroll-spy + 固定/滚动级别 + 移动端目录 + 侧栏开关 + 引用悬停预览 + 标题自动编号；暴露 `window.__tocRefresh()`。
  - `_shared/js/collapse.js`：标题折叠（3.2）+ 代码块默认折叠（3.1），折叠后触发 `__tocRefresh`。
  - `_shared/js/modal.js`：图片模态查看器（1.1–1.10）：透明背景、白底图形区、+/-/拖拽/滚轮缩放、‹/›切换且首尾 disabled、ESC/空白/X 关闭、SVG 真实尺寸自适应、id 去重。
  - `_shared/js/diagrams.js`：Mermaid 运行时渲染 + `curve:'stepBefore'` 直角连线（0.4）+ 自动注入"查看"按钮（1.1 单一来源）。
- **脚本 `scripts/`**：
  - `scaffold.py`：生成报告工程（同名父文件夹 + `_shared/` + `<name>.html` + `CHANGELOG.md` + `DEV_DOC.md`）。
  - `validate.py`：交付前校验（4.1 div 配对 / 4.2 截断行 / 4.3 标签平衡 / 4.4 重复 id+figure 前缀 / 4.5 目录完整性 / 版本一致性），退出码 0/非0。
- **规则 `rules/`**：
  - `constraints.md`：全部约束逐条清单（0.1–0.5 / 1.1–1.10 / 2.1–2.8 / 3.1–3.14 / 4.1–4.5 / 版本号 / 文件结构）。
  - `style-spec.md`：颜色/字体/布局令牌规范（低饱和、系统字体、透明模态等）。
- **测试 `tests/testcases.md`**：A–H 八组用例（脚手架/目录/模态/绘图/正文/校验/版本/失败注入回归）。
- **自检**：`scaffold.py` 生成样例 + `validate.py` 输出 ALL PASS；5 个 JS 文件 `node --check` 全部通过。
