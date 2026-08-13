---
name: "modal-image-viewer"
description: "为 HTML 文档中的 Mermaid 流程图 / ECharts 图表 / SVG 图形实现统一的模态图片查看器（放大、缩放、平移、切换）并提供交付前校验脚本。当用户需要在 HTML 中集成/修复图片模态查看器、或要求文档图片具备查看按钮、或校验图片序号/文档结构时调用。"
---

# 模态图片查看器设计 Skill

> **版本**: v1.04
> **用途**: 为 HTML 文档中的 Mermaid 流程图 / ECharts 图表 / SVG 图形提供统一的模态查看器设计规范，可在任意 HTML 项目中集成。
> **实现方式**: 本 skill 采用"指令 + 模板 + 校验脚本"三段式结构。`SKILL.md` 只描述规则与约束；可复用代码见 `templates/`；交付前校验见 `scripts/`；版本变更历史见 `CHANGELOG.md`。

---

## 1. 设计目标

在技术文档中，内嵌的 SVG 图表通常尺寸有限，用户需要点击"查看"按钮在模态窗口中放大浏览。设计需解决以下核心问题：

- **图片自适应视口**：不同图表的宽高比差异大，需等比缩放至视口可用空间
- **白色背景紧凑包裹**：白色背景仅包围图片本身 + padding，不撑满整个视口
- **深色遮罩遮挡底层**：避免底层文档白色背景透出
- **缩放/平移/切换**：支持鼠标拖拽平移、滚轮缩放、多图左右切换
- **ECharts 交互保留**：模态中 ECharts 图表保留 tooltip/hover 交互
- **Mermaid 无交互**：模态中 Mermaid 流程图设 pointer-events:none，仅支持缩放/平移

---

## 2. 资源索引

本 skill 的资产按"模板 / 脚本"两类分门别类：

| 分类 | 文件 | 用途 |
|------|------|------|
| 文档 | `SKILL.md` | 指令与规范正文（本文件） |
| 文档 | `CHANGELOG.md` | 版本变更历史 |
| 模板 | `templates/modal-window.html` | 模态窗口 HTML 结构（遮罩层、工具栏、图片舞台） |
| 模板 | `templates/figure.html` | 图表 figure 结构（ECharts / Mermaid 两种） |
| 模板 | `templates/modal.css` | 全部模态样式 |
| 模板 | `templates/modal.js` | 全部模态脚本（渲染、缩放、平移、导航） |
| 脚本 | `scripts/check-structure.sh` | 校验文档结构一致性（TOC、版本号、HTML 结构） |
| 脚本 | `scripts/check-figure-numbers.sh` | 校验图片序号连续性 + modalTitle 一致性 |
| 脚本 | `scripts/check-view-buttons.sh` | 校验查看按钮单一来源 |
| 脚本 | `scripts/check-modal-viewer.sh` | 综合校验（全部规则，可选 `charts.js`） |

---

## 3. 集成实现

集成分成三层：**HTML 结构**（骨架）、**CSS 规范**（样式）、**JavaScript 规范**（交互）。三层分别对应 `templates/` 下的三个文件。

### 3.1 HTML 结构

#### 3.1.1 模态窗口

模板文件：`templates/modal-window.html`。核心结构说明：

| 元素 | 作用 | 关键属性 |
|------|------|---------|
| `.img-modal` | 全屏遮罩层 | `position: fixed; 100vw x 100vh; z-index: 9999` |
| `.img-modal-content` | 内容容器 | `100vw x 100vh; position: relative` |
| `.img-modal-toolbar` | 统一顶部工具栏 | `position: absolute; top: 12px; flex; z-index: 2` |
| `.img-modal-body` | 图片居中容器 | `flex; overflow: auto; 100% x 100%` |
| `.img-stage` | 白色背景包裹器 | `inline-flex; margin: auto; padding: 20px; background: #fff` |

#### 3.1.2 图表 figure 与查看按钮

模板文件：`templates/figure.html`，包含 ECharts（`figure.chart-figure`）与 Mermaid（`figure.diagram`）两种 figure 结构。

每个 `figure` 必须有且仅有一个"查看"按钮，且只能通过一种机制添加（单一来源原则）：

| 规则 | 要求 | 禁止 |
|------|------|------|
| R1 | 仅使用静态 HTML 按钮或动态 JS 之一 | 同时使用两种机制 |
| R2 | 使用静态 `<button class="zoom-btn">` | 动态 createElement + appendChild |
| R3 | 统一使用 CSS 类样式 | 内联 style 样式 |
| R4 | 添加按钮前先检查是否已有按钮 | 盲目追加新按钮 |

标准按钮结构见 `templates/figure.html`：`figure` 内 `<div class="fig-bar">` 中放置 `<figcaption>` 与 `<button class="zoom-btn" onclick="openImageModal('fig-xxx')">查看</button>`。

### 3.2 CSS 规范

完整样式模板见 `templates/modal.css`。以下是必须遵守的关键规则：

- **遮罩层必须有深色背景**：`.img-modal` 设 `background: rgba(0,0,0,0.55)`。常见错误：用 `transparent` 会导致底层文档白色背景透出，视觉上"空白过大"。
- **图片区域用 inline-flex shrink-wrap + margin:auto 居中**：`.img-stage` 用 `display: inline-flex`（禁止 `width/height: 100%`），居中用 `margin: auto` 而非 `align-items/justify-content: center`。`.img-modal-body` 用 `overflow: auto` 而非 `hidden`，否则缩放后溢出内容被裁剪；flex 居中时溢出滚动条在部分浏览器不生效。
- **SVG/图片仅约束上限**：`.img-stage svg, .img-stage img` 只设 `max-width: 90vw; max-height: 85vh`，不要设 `width/height: auto`（会覆盖 JS 设置的显式宽高）。
- **figure 使用分离的 overflow 策略**：`figure.chart-figure` 必须配 `overflow: hidden`（配对 border-radius）；`figure.diagram` 禁止 `overflow: hidden`（会裁剪 Mermaid SVG 交互与滚动）。
- **统一顶部工具栏**：`.img-modal-toolbar` 绝对定位于顶部居中，导航/缩放/关闭按钮与分隔符样式见 `templates/modal.css`。

### 3.3 JavaScript 规范

完整脚本见 `templates/modal.js`。以下是必须遵守的规则与设计要点：

#### 3.3.1 渲染策略 — 按类型区分

- `modalState` 对象管理当前索引、图表列表、缩放与平移状态。
- `openImageModal(figureId)` 通过 figure ID 打开模态，`collectFigures()` 建立 `figure.chart-figure, figure.diagram` 的导航索引，`showModalContent()` 按类型渲染：
  - **Mermaid**：克隆 SVG，`removeAttribute('width/height/style')` 后按 `viewBox` 等比缩放到视口的 90% x 85%，并设 `pointer-events:none`。
  - **ECharts**：用 `echarts.getInstanceByDom()` 取原始 option，再用 `echarts.init()` 在新容器重新初始化（保留 tooltip/hover 交互），而非克隆 SVG。渲染前先 `dispose()` 旧实例并 `innerHTML = ''`。
  - 渲染后按索引更新 `navPrev`/`navNext` 的 disabled 状态；ECharts 图表不应用缩放/平移，设 `stage.style.transform = 'none'`。

#### 3.3.2 SVG ID 去重

克隆 SVG 后必须调用 `deduplicateSvgId()`：通过 XMLSerializer 序列化 -> 全局替换旧 ID -> DOMParser 解析回 DOM，避免克隆体与源 SVG 出现重复 ID 导致样式和 marker 引用失效。

#### 3.3.3 关闭、导航、缩放、平移

`navImage`、`closeImageModal`、`modalResizeHandler`、`modalKeyHandler`、`zoomImage`、`resetZoom`、`applyTransform` 及拖拽/滚轮绑定逻辑均在 `templates/modal.js` 中。要点：

- `zoomImage`/`resetZoom`/`mousedown` 中检查 `stage._modalChart` 并提前返回，ECharts 模态不应用缩放/平移。
- `modalKeyHandler` 支持 ESC 关闭、左右箭头切换、`+`/`-` 缩放。
- 滚轮缩放监听挂载在 `.img-modal` 上，`{ passive: false }` 以阻止默认滚动。

---

## 4. ECharts 特殊交互规则

ECharts 图表在"页面内"和"模态中"各有特殊要求，与普通 SVG/Mermaid 不同，单独成节：

### 4.1 页面内 — 初始化前清除预渲染内容

宿主项目的 `charts.js` 中，`initAll()` 初始化每个图表前必须先清除容器内预渲染内容：`el.innerHTML = ''`。

> **根因**：构建时预渲染的 SVG 含 `_echarts_instance_` 属性，`echarts.init()` 创建的新实例生成的交互式 SVG 被旧 SVG 遮挡，鼠标事件被拦截。

### 4.2 页面内 — tooltip 配置

ECharts `tooltip` 必须设 `appendToBody: true`，绕过父容器 `overflow:hidden` 裁剪。

> **约束**：`figure.chart-figure` 设 `overflow:hidden`（配对 border-radius），tooltip 弹出层会被裁剪。`appendToBody: true` 将 tooltip 渲染到 `document.body`，绕过父容器限制。**禁止为释放 tooltip 而移除父容器的 overflow:hidden**。

### 4.3 模态中 — 用 init() 而非 SVG 克隆

模态中 ECharts 必须用 `echarts.init()` 重新初始化，保留完整 JS 事件处理器（tooltip/hover）。`cloneNode(true)` 仅复制 SVG DOM 结构，不复制事件处理器，克隆体是静态的。

### 4.4 模态中 — 禁用缩放/平移

ECharts 图表在模态中不应用缩放/平移 transform（`applyTransform` 干扰 ECharts 内部事件坐标计算），设 `stage.style.transform = 'none'`。在 `zoomImage`/`resetZoom`/`mousedown` 中检查 `stage._modalChart` 并提前返回。

---

## 5. 交付前校验

交付前必须执行校验脚本并通过，遵循"文档三同步原则"。

### 5.1 文档三同步原则

任何内容变更后，以下三处必须同步更新：

1. **正文内容** -> 新增/修改章节后，正文中必须实际插入对应 HTML
2. **侧边栏目录** -> 新增章节锚点后，侧边栏 `<nav>` 中必须添加对应 `<a>` 条目
3. **版本号** -> 侧边栏、页脚、Badge 三处版本号必须一致

### 5.2 校验脚本

所有校验脚本位于 `scripts/` 目录，交付前执行：

```bash
chmod +x scripts/*.sh
# 文档结构一致性（TOC、版本号、HTML 结构）
./scripts/check-structure.sh <file.html>
# 图片序号连续性 + modalTitle 一致性
./scripts/check-figure-numbers.sh <file.html>
# 查看按钮数量（单一来源）
./scripts/check-view-buttons.sh <file.html>
# 综合校验（所有规则，可选 charts.js）
./scripts/check-modal-viewer.sh <file.html> [charts.js]
```

### 5.3 集成检查清单

| # | 检查项 | 要求 | 常见错误 |
|---|--------|------|---------|
| 1 | 遮罩层背景 | `background: rgba(0,0,0,0.55)` | `transparent` 导致底层白色透出 |
| 2 | 图片容器 display | `display: inline-flex` | `flex` + `width:100%` 导致撑满视口 |
| 3 | 容器无固定宽高 | 不设 `width/height: 100%` | 白色背景填满整个视口 |
| 4 | modal-body overflow | `overflow: auto` | `hidden` 裁剪缩放后溢出内容 |
| 5 | img-stage 居中方式 | `margin: auto` | flex 居中时溢出滚动条不生效 |
| 6 | SVG 清除原始属性 | `removeAttribute('width/height/style')` | 原始内联样式覆盖 CSS |
| 7 | SVG 按 viewBox 缩放 | JS 计算 `Math.min(maxW/vbW, maxH/vbH)` | 无显式宽高时浏览器默认 300x150 |
| 8 | SVG max-width/max-height | CSS 设 `90vw / 85vh` | 无约束时超大图溢出视口 |
| 9 | SVG ID 去重 | 克隆后调用 `deduplicateSvgId()` | 重复 ID 导致 CSS 样式和 marker 引用失效 |
| 10 | ECharts 模态渲染 | 用 `echarts.init()` 而非 SVG 克隆 | SVG 克隆丢失 JS 事件处理器 |
| 11 | ECharts 初始化前清除 | `el.innerHTML = ''` | 预渲染 SVG 拦截鼠标事件 |
| 12 | ECharts tooltip | `appendToBody: true` | overflow:hidden 裁剪 tooltip |
| 13 | Mermaid 交互策略 | `pointer-events: none` | Mermaid SVG 拦截模态拖拽事件 |
| 14 | figure.chart-figure | `overflow: hidden`（配对 border-radius） | 移除后子元素溢出导致布局错乱 |
| 15 | figure.diagram | 无 `overflow: hidden` | 裁剪 Mermaid SVG 交互和滚动 |
| 16 | border-radius 配对 | 任何 border-radius 容器须配 overflow:hidden | 子元素溢出圆角边界 |
| 17 | 关闭交互 | 点击空白 / ESC / X 按钮 | 无法关闭模态 |
| 18 | 图片切换 | 按钮 + 方向键，首尾 disabled | 无多图导航 |
| 19 | 工具栏统一 | 导航/缩放/关闭整合为顶部工具栏 | 分散定位导致 z-index 冲突 |
| 20 | ECharts 模态 dispose | 关闭模态时 `chart.dispose()` | 内存泄漏 |
| 21 | ECharts 模态 resize | 窗口 resize 时 `chart.resize()` | 图表不随窗口变化 |
| 22 | ECharts 模态不缩放 | `stage.style.transform = 'none'` | transform 干扰 ECharts 交互 |
| 23 | ECharts 模态禁用缩放/平移 | `zoomImage`/`resetZoom`/`mousedown` 中检查 `stage._modalChart` | 键盘 +/- 或拖拽干扰 ECharts |
| 24 | 图片序号连续性 | figcaption 序号从 1 开始按文档出现顺序 1-N 连续递增，modalTitle 为有效图号 | 新增图表时未更新已有图表序号 |

---

## 6. 常见陷阱

陷阱按问题域分为四类：**布局与样式**、**SVG 渲染**、**ECharts 交互**、**文档结构**。每条以"现象 -> 根因 -> 解决"描述。

### 6.1 布局与样式

| # | 现象 | 根因 | 解决 |
|---|------|------|------|
| 1 | 模态打开后图片周围有大量"白色"区域 | 遮罩层透明，底层文档白色背景透出 | 遮罩层设 `background: rgba(0,0,0,0.55)` |
| 2 | 白色背景占满整个屏幕，窄图周围大量空白 | `display:flex` + `width:100%` 使容器撑满 | 改用 `display:inline-flex`，移除 `width/height:100%` |
| 3 | CSS 修复正确但图片仍被限制在原始尺寸 | `cloneNode(true)` 携带了原始 SVG 的 `style`（含 `max-width`） | 克隆后 `clone.removeAttribute('style')` |
| 4 | 清除所有属性后图片变得极小 | SVG 无显式宽高时浏览器默认 300x150px，忽略 `viewBox` | 从 `viewBox` 解析自然尺寸，等比缩放后显式设置 `width/height` |
| 5 | 用 `style.width='100%'` 替代 viewBox 后图片仍极小 | inline-flex 父容器宽度由内容决定，`100%` 陷入"100% of 300px"死循环 | 必须用 viewBox 等比缩放，而非 CSS 百分比 |
| 6 | JS 正确设置 width/height 但图片仍异常 | CSS `width/height: auto` 优先级高于 HTML 属性，覆盖 JS 设置 | CSS 仅用 `max-width/max-height` 约束上限，不设 `width/height: auto` |
| 7 | figure 移除 overflow:hidden 后布局错乱，恢复后又裁剪 tooltip | border-radius 容器须配对 overflow:hidden，但会裁剪 tooltip 弹出层 | 保持 overflow:hidden，用 `tooltip.appendToBody:true`；禁止移除 overflow:hidden |

### 6.2 SVG 渲染

| # | 现象 | 根因 | 解决 |
|---|------|------|------|
| 8 | ECharts 生成的 SVG 清除宽高后只显示左上角局部 | ECharts SVG 用显式 width/height 而非 viewBox，清除后默认 300x150px | 移除宽高前保存原始尺寸，无 viewBox 时用原始宽高构造 `viewBox`（见 `templates/modal.js` Fallback 分支） |
| 9 | 模态中 Mermaid 流程图节点无填充、边线消失、箭头不显示 | Mermaid SVG 根元素 `<style>` 与 `<marker>` 三处共用同一 id，克隆后 ID 重复，CSS 仅匹配首个元素 | 克隆后调用 `deduplicateSvgId()`（序列化 -> 全局替换旧 ID -> 解析回 DOM） |

### 6.3 ECharts 交互

| # | 现象 | 根因 | 解决 |
|---|------|------|------|
| 10 | ECharts 图表在模态中无法 hover 显示 tooltip | `cloneNode(true)` 不复制 JS 事件处理器，SVG 克隆体是静态的 | 模态中用 `echarts.getInstanceByDom()` 取 option，再 `echarts.init()` 重新初始化；关闭时 `chart.dispose()` |
| 11 | ECharts 图表在页面内无法 hover，但模态中正常 | 构建时容器内嵌预渲染 SVG（含残留 `_echarts_instance_`），遮挡新实例鼠标事件 | `charts.js` 的 `initAll()` 初始化前 `el.innerHTML = ''` |
| 12 | ECharts 图表在模态中交互异常，tooltip 位置偏移 | 对 ECharts 容器应用 `transform: scale()` 干扰内部事件坐标计算 | 模态中 ECharts 不应用缩放/平移，设 `stage.style.transform='none'` |

### 6.4 文档结构

| # | 现象 | 根因 | 解决 |
|---|------|------|------|
| 13 | 修改图片查看器代码后页面所有 JS 功能失效 | `<script>` 内使用 HTML 实体编码（`&lt;=` 替代 `<=`），导致 `SyntaxError`，整个 `<script>` 块不执行 | `<script>` 标签内永远使用原始字符 |
| 14 | 页面所有 JS 功能失效，控制台无错误 | 正文文本含未转义 `<style>` 标签，HTML 解析器将其当作 style 元素 | 正文中的 `<style>` 转义为 `&lt;style&gt;` |
| 15 | 多张图片 figcaption 序号与文档实际顺序不一致 | 新增图表时复制模板但未同步更新 figcaption 序号，也未对既有图表重新编号 | 序号按文档出现顺序从 1 连续递增，新增后对所有图表重新编号，figcaption 与 modalTitle 保持一致（见 `scripts/check-figure-numbers.sh`） |

---

## 7. 最佳实践

1. **导航按钮位于标题栏内**：将导航/缩放/关闭按钮整合为统一顶部工具栏，避免分散定位的 z-index 冲突。
2. **通过 figure ID 打开模态**：`openImageModal('fig-xxx')` 传入 figure 的 id，内部用 `getElementById` 定位，再用 `collectFigures()` 建立导航索引。
3. **点击空白关闭用 `event.target` 检测**：`.img-modal-content` 的 `onclick` 中检查 `event.target === this`，无需 `stopPropagation`。
4. **SVG 克隆后必须去重 ID**：在 `removeAttribute` 之后、`viewBox` 缩放之前调用 `deduplicateSvgId()`。
5. **ECharts 模态用 init() 而非 SVG 克隆**：保留完整 JS 事件处理器（tooltip/hover）。
6. **ECharts 初始化前清除容器**：`el.innerHTML = ''` 清除预渲染 SVG 残留。
7. **ECharts tooltip 用 appendToBody**：绕过 overflow:hidden 裁剪。
8. **Mermaid SVG 设 pointer-events:none**：避免拦截模态拖拽事件。
9. **border-radius 配对 overflow:hidden**：防止子元素溢出圆角边界。
10. **关闭模态时 dispose ECharts 实例**：避免内存泄漏。
11. **ECharts 模态禁用缩放/平移**：`zoomImage`、`resetZoom`、`mousedown` 中检查 `stage._modalChart` 并提前返回。
12. **图片序号从 1 开始连续递增**：新增图表后必须对所有既有图表重新编号（图 1-N），序号从 1 开始按文档出现顺序连续递增，并同步更新 figcaption 与模态标题 `#modalTitle` 中的序号，交付前用 `scripts/check-figure-numbers.sh` 校验。

---

## 8. 版本历史

版本变更历史已独立到 `CHANGELOG.md`。当前版本 v1.04，完整历史见该文件。