# 模态图片查看器设计 Skill (v2.04)

> **版本**: v2.04
> **创建日期**: 2026-08-12
> **最后更新**: 2026-08-13
> **前身**: v1.11 (2026-08-12)
> **用途**: 为 HTML 文档中的 Mermaid 流程图 / ECharts 图表 / SVG 图形提供统一的模态查看器设计规范，可在任意 HTML 项目中集成。

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

## 2. HTML 结构模板

### 2.1 模态窗口（统一顶部工具栏）

```html
<!-- ============ 图片查看模态窗口 ============ -->
<div class="img-modal" id="imgModal">
  <div class="img-modal-content" onclick="if(event.target===this||event.target.classList.contains('img-modal-body'))closeImageModal()">
    <div class="img-modal-toolbar">
      <button class="img-nav-btn" id="navPrev" onclick="navImage(-1)" title="上一张">‹</button>
      <span class="img-modal-title" id="modalTitle">图片预览</span>
      <button class="img-nav-btn" id="navNext" onclick="navImage(1)" title="下一张">›</button>
      <span class="toolbar-separator"></span>
      <button onclick="zoomImage(0.2)" title="放大">+</button>
      <button onclick="zoomImage(-0.2)" title="缩小">−</button>
      <button onclick="resetZoom()" title="重置缩放">重置</button>
      <span class="toolbar-separator"></span>
      <button class="img-modal-close" onclick="closeImageModal()" title="关闭 (Esc)">✕</button>
    </div>
    <div class="img-modal-body">
      <div class="img-stage" id="imgStage" style="transform: translate(0px, 0px) scale(1);"></div>
    </div>
  </div>
</div>
```

### 2.2 结构要点

| 元素 | 作用 | 关键属性 |
|------|------|---------|
| `.img-modal` | 全屏遮罩层 | `position: fixed; 100vw x 100vh; z-index: 9999` |
| `.img-modal-content` | 内容容器 | `100vw x 100vh; position: relative` |
| `.img-modal-toolbar` | 统一顶部工具栏 | `position: absolute; top: 12px; flex; z-index: 2` |
| `.img-modal-body` | 图片居中容器 | `flex; overflow: auto; 100% x 100%` |
| `.img-stage` | 白色背景包裹器 | `inline-flex; margin: auto; padding: 20px; background: #fff` |

### 2.3 图表 figure 模板

```html
<!-- ECharts 图表 -->
<figure class="chart-figure" id="fig-throughput">
  <div class="fig-bar">
    <figcaption>图 1：标题文字</figcaption>
    <button class="zoom-btn" onclick="openImageModal('fig-throughput')">查看</button>
  </div>
  <div class="chart-canvas" id="chart-throughput"></div>
</figure>

<!-- Mermaid 流程图 -->
<figure class="diagram" id="fig-arch">
  <div class="fig-bar">
    <figcaption>图 2：架构图</figcaption>
    <button class="zoom-btn" onclick="openImageModal('fig-arch')">查看</button>
  </div>
  <div class="mermaid-wrap">
    <pre class="mermaid">graph TD; A-->B;</pre>
  </div>
</figure>
```

---

## 3. CSS 规范

### 3.1 遮罩层 — 必须有深色背景

```css
.img-modal {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.55);  /* 必须：半透明深色，遮挡底层文档 */
}
.img-modal.open { display: block; }
```

> **常见错误**：使用 `background: transparent` 会导致底层文档白色背景透出，视觉上"空白过大"。

### 3.2 内容容器

```css
.img-modal-content {
  width: 100vw;
  height: 100vh;
  position: relative;
}
```

### 3.3 图片区域 — inline-flex shrink-wrap + margin:auto 居中

```css
.img-modal-body {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: auto;  /* 必须 auto：缩放后可滚动查看完整内容 */
}
.img-stage {
  margin: auto;              /* 必须 margin:auto：flex 居中且支持溢出滚动 */
  background: #ffffff;
  padding: 20px;
  border-radius: 4px;
  cursor: grab;
  transform-origin: center center;
  transition: transform 0.15s ease;
  display: inline-flex;      /* 必须：shrink-wrap 包裹内容 */
  align-items: center;
  justify-content: center;
  /* 禁止设 width: 100% / height: 100% */
}
.img-stage.dragging { cursor: grabbing; }
.img-stage svg, .img-stage img {
  max-width: 90vw;
  max-height: 85vh;
  display: block;
}
```

> **关键**：`.img-modal-body` 使用 `overflow: auto` 而非 `overflow: hidden`。`hidden` 会裁剪缩放后溢出的内容。`.img-stage` 使用 `margin: auto` 而非 `align-items/justify-content: center`，因为 flex 居中时内容溢出滚动条不生效（浏览器兼容问题）。

### 3.4 统一顶部工具栏

```css
.img-modal-toolbar {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255,255,255,0.9);
  padding: 6px 10px;
  border-radius: 24px;
  backdrop-filter: blur(4px);
  border: 1px solid var(--rule);
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  max-width: 92vw;
}
.img-modal-toolbar .img-modal-title {
  font-size: 13px;
  color: var(--ink);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 420px;
  padding: 0 6px;
}
.img-modal-toolbar button {
  cursor: pointer;
  border: 1px solid var(--rule);
  background: #fff;
  color: var(--ink);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 14px;
  min-width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}
.img-modal-toolbar button:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.img-modal-toolbar button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.img-modal-toolbar .img-modal-close {
  border-radius: 50%;
  width: 30px;
  height: 30px;
  padding: 0;
  font-size: 15px;
}
.img-modal-toolbar .img-modal-close:hover {
  background: var(--red); color: #fff; border-color: var(--red);
}
.img-modal-toolbar .img-nav-btn {
  border-radius: 50%;
  width: 30px;
  height: 30px;
  padding: 0;
  font-size: 18px;
}
.img-modal-toolbar .toolbar-separator {
  width: 1px;
  height: 20px;
  background: var(--rule);
  margin: 0 4px;
  flex-shrink: 0;
}
```

### 3.5 图表 figure CSS — 分离规则

```css
/* ECharts 图表：border-radius 配对 overflow:hidden */
figure.chart-figure {
  margin: 20px 0;
  border: 1px solid var(--rule);
  border-radius: 8px;
  overflow: hidden;       /* 必须：配对 border-radius 裁剪子元素 */
  background: var(--bg);
}
/* Mermaid 图表：不可 overflow:hidden（需保留滚动容器） */
figure.diagram {
  margin: 20px 0;
  border: 1px solid var(--rule);
  border-radius: 8px;
  background: var(--bg);
  /* 禁止 overflow:hidden：会裁剪 Mermaid SVG 交互 */
}
.chart-canvas { width: 100%; height: 340px; padding: 12px; }
.mermaid-wrap { padding: 20px; overflow: auto; background: var(--bg); }
/* Mermaid SVG 不需要交互，禁用 pointer-events */
.mermaid-wrap svg { pointer-events: none; }
```

> **关键规则**：`figure.chart-figure` 和 `figure.diagram` 必须使用不同的 overflow 策略。ECharts 的 `chart-canvas` 尺寸固定，`overflow:hidden` 安全；Mermaid 的 `mermaid-wrap` 需要滚动，`overflow:hidden` 会裁剪内容。

---

## 4. JavaScript 规范

### 4.1 状态管理

```javascript
var modalState = {
  index: 0,
  figures: [],
  scale: 1,
  panX: 0,
  panY: 0,
  isDragging: false,
  startX: 0,
  startY: 0
};
```

### 4.2 核心：showModalContent — 按类型区分渲染策略

```javascript
function collectFigures() {
  modalState.figures = Array.prototype.slice.call(
    document.querySelectorAll('figure.chart-figure, figure.diagram')
  );
}

function openImageModal(figureId) {
  collectFigures();
  var fig = document.getElementById(figureId);
  modalState.index = modalState.figures.indexOf(fig);
  showModalContent();
  document.getElementById('imgModal').classList.add('open');
  document.addEventListener('keydown', modalKeyHandler);
  window.addEventListener('resize', modalResizeHandler);
}

function showModalContent() {
  var fig = modalState.figures[modalState.index];
  if (!fig) return;
  var caption = fig.querySelector('figcaption');
  document.getElementById('modalTitle').textContent = caption ? caption.textContent : '图片预览';

  var stage = document.getElementById('imgStage');
  // ★ 先清理旧 ECharts 实例（innerHTML 前必须 dispose）
  if (stage._modalChart) {
    stage._modalChart.dispose();
    stage._modalChart = null;
  }
  stage.innerHTML = '';

  var mermaidDiv = fig.querySelector('.mermaid');
  var chartDiv = fig.querySelector('.chart-canvas');
  var clone;

  if (mermaidDiv) {
    // ── Mermaid：克隆 SVG，设 pointer-events:none ──
    var svg = mermaidDiv.querySelector('svg');
    if (svg) {
      clone = svg.cloneNode(true);
      clone.removeAttribute('width');
      clone.removeAttribute('height');
      clone.removeAttribute('style');
      clone = deduplicateSvgId(clone);  // ★ 必须去重 ID
      var vb = clone.getAttribute('viewBox');
      if (vb) {
        var parts = vb.trim().split(/\s+/);
        if (parts.length === 4) {
          var vbW = parseFloat(parts[2]);
          var vbH = parseFloat(parts[3]);
          var maxW = window.innerWidth * 0.9;
          var maxH = window.innerHeight * 0.85;
          var scale = Math.min(maxW / vbW, maxH / vbH);
          clone.setAttribute('width', Math.round(vbW * scale));
          clone.setAttribute('height', Math.round(vbH * scale));
        }
      }
      clone.setAttribute('style', 'pointer-events: none;');
    }
  } else if (chartDiv) {
    // ── ECharts：用 echarts.init() 重新初始化，保留完整交互 ──
    if (typeof echarts !== 'undefined') {
      var ecInstance = echarts.getInstanceByDom(chartDiv);
      if (ecInstance) {
        var option = ecInstance.getOption();
        var ecContainer = document.createElement('div');
        ecContainer.style.width = Math.round(window.innerWidth * 0.9) + 'px';
        ecContainer.style.height = Math.round(window.innerHeight * 0.85) + 'px';
        ecContainer.style.background = '#ffffff';
        ecContainer.style.borderRadius = '4px';
        stage.appendChild(ecContainer);
        var modalChart = echarts.init(ecContainer, null, { renderer: 'svg' });
        modalChart.setOption(option);
        stage._modalChart = modalChart;
      }
    }
    // Fallback：ECharts 不可用时克隆 SVG
    if (!stage._modalChart) {
      var chartSvg = chartDiv.querySelector('svg');
      if (chartSvg) {
        clone = chartSvg.cloneNode(true);
        var origW = parseInt(clone.getAttribute('width'), 10);
        var origH = parseInt(clone.getAttribute('height'), 10);
        clone.removeAttribute('width');
        clone.removeAttribute('height');
        clone.removeAttribute('style');
        clone = deduplicateSvgId(clone);
        var cvb = clone.getAttribute('viewBox');
        if (!cvb && origW > 0 && origH > 0) {
          cvb = '0 0 ' + origW + ' ' + origH;
          clone.setAttribute('viewBox', cvb);
        }
        if (cvb) {
          var cparts = cvb.trim().split(/\s+/);
          if (cparts.length === 4) {
            var cvbW = parseFloat(cparts[2]);
            var cvbH = parseFloat(cparts[3]);
            var cmaxW = window.innerWidth * 0.9;
            var cmaxH = window.innerHeight * 0.85;
            var cscale = Math.min(cmaxW / cvbW, cmaxH / cvbH);
            clone.setAttribute('width', Math.round(cvbW * cscale));
            clone.setAttribute('height', Math.round(cvbH * cscale));
          }
        }
      }
    }
  }
  if (clone) {
    stage.appendChild(clone);
  }

  // 更新导航按钮状态
  document.getElementById('navPrev').disabled = (modalState.index <= 0);
  document.getElementById('navNext').disabled = (modalState.index >= modalState.figures.length - 1);

  // ★ ECharts 图表不应用缩放/平移（避免干扰交互）
  if (!stage._modalChart) {
    resetZoom();
  } else {
    modalState.scale = 1;
    modalState.panX = 0;
    modalState.panY = 0;
    stage.style.transform = 'none';
  }
}
```

### 4.3 SVG ID 去重工具函数

```javascript
var _svgIdCounter = 0;
function deduplicateSvgId(svgEl) {
  var oldId = svgEl.getAttribute('id');
  if (!oldId) return svgEl;
  _svgIdCounter++;
  var newId = oldId + '-modal-' + _svgIdCounter;
  var serializer = new XMLSerializer();
  var svgStr = serializer.serializeToString(svgEl);
  svgStr = svgStr.split(oldId).join(newId);
  var parser = new DOMParser();
  var doc = parser.parseFromString(svgStr, 'image/svg+xml');
  return document.importNode(doc.documentElement, true);
}
```

### 4.4 关闭、导航、缩放、平移

```javascript
function navImage(dir) {
  var newIndex = modalState.index + dir;
  if (newIndex < 0 || newIndex >= modalState.figures.length) return;
  modalState.index = newIndex;
  showModalContent();
}

function closeImageModal() {
  document.getElementById('imgModal').classList.remove('open');
  document.removeEventListener('keydown', modalKeyHandler);
  window.removeEventListener('resize', modalResizeHandler);
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) {
    stage._modalChart.dispose();
    stage._modalChart = null;
  }
}

function modalResizeHandler() {
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) {
    stage._modalChart.resize();
  }
}

function modalKeyHandler(e) {
  if (e.key === 'Escape') closeImageModal();
  else if (e.key === 'ArrowLeft') navImage(-1);
  else if (e.key === 'ArrowRight') navImage(1);
  else if (e.key === '+' || e.key === '=') zoomImage(0.2);
  else if (e.key === '-') zoomImage(-0.2);
}

function zoomImage(delta) {
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) return;  // ★ ECharts 图表不应用缩放（避免干扰交互）
  modalState.scale = Math.max(0.3, Math.min(5, modalState.scale + delta));
  applyTransform();
}

function resetZoom() {
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) return;  // ★ ECharts 图表不应用平移
  modalState.scale = 1;
  modalState.panX = 0;
  modalState.panY = 0;
  applyTransform();
}

function applyTransform() {
  var stage = document.getElementById('imgStage');
  stage.style.transform = 'translate(' + modalState.panX + 'px,' + modalState.panY + 'px) scale(' + modalState.scale + ')';
}

// 拖拽平移 + 滚轮缩放
(function () {
  var stage = document.getElementById('imgStage');
  stage.addEventListener('mousedown', function (e) {
    if (stage._modalChart) return;  // ★ ECharts 图表不拖拽
    modalState.isDragging = true;
    modalState.startX = e.clientX - modalState.panX;
    modalState.startY = e.clientY - modalState.panY;
    stage.classList.add('dragging');
    e.preventDefault();
  });
  document.addEventListener('mousemove', function (e) {
    if (!modalState.isDragging) return;
    modalState.panX = e.clientX - modalState.startX;
    modalState.panY = e.clientY - modalState.startY;
    applyTransform();
  });
  document.addEventListener('mouseup', function () {
    modalState.isDragging = false;
    stage.classList.remove('dragging');
  });
  var modal = document.getElementById('imgModal');
  modal.addEventListener('wheel', function (e) {
    if (!modal.classList.contains('open')) return;
    e.preventDefault();
    var delta = e.deltaY < 0 ? 0.15 : -0.15;
    zoomImage(delta);
  }, { passive: false });
})();
```

---

## 5. ECharts 页面内交互规则

### 5.1 初始化前清除预渲染内容

```javascript
// ★ charts.js initAll() 中，初始化前必须清除容器内预渲染 SVG
function initAll() {
  // 通用方案：清除所有 chart-canvas 容器内的预渲染内容
  document.querySelectorAll('.chart-canvas').forEach(function (el) {
    el.innerHTML = '';  // 清除构建时嵌入的预渲染 SVG（含残留 _echarts_instance_）
  });
  // 然后初始化各图表...
}
```

> **根因**：构建时预渲染的 SVG 含 `_echarts_instance_` 属性，`echarts.init()` 创建的新实例生成的交互式 SVG 被旧 SVG 遮挡，鼠标事件被拦截。

### 5.2 tooltip 配置

```javascript
chart.setOption({
  tooltip: {
    trigger: 'axis',
    appendToBody: true,  // 必须：绕过父容器 overflow:hidden 裁剪
    axisPointer: { type: 'shadow' }
  },
  // ...
});
```

> **根因**：`figure.chart-figure` 设 `overflow:hidden`（配对 border-radius），tooltip 弹出层会被裁剪。`appendToBody: true` 将 tooltip 渲染到 `document.body`，绕过父容器限制。**禁止为释放 tooltip 而移除父容器的 overflow:hidden**。

---

## 6. 集成检查清单

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

## 7. 常见陷阱与解决方案

### 陷阱 1：`background: transparent` -> "空白过大"

**现象**：模态打开后，图片周围有大量"白色"区域。

**根因**：遮罩层透明，底层文档的白色背景透过遮罩层显示出来。

**解决**：遮罩层设 `background: rgba(0, 0, 0, 0.55)`。

### 陷阱 2：`display: flex` + `width: 100%` -> 白色背景撑满视口

**现象**：白色背景区域占满整个屏幕，窄图周围大量空白。

**根因**：`display: flex` 使容器扩展到父元素宽度，`width: 100%` 进一步强制撑满。

**解决**：改用 `display: inline-flex`，移除 `width/height: 100%`。

### 陷阱 3：原始 SVG `style="max-width: 394px"` 被携带

**现象**：CSS 修复正确，但图片仍被限制在原始尺寸。

**根因**：`cloneNode(true)` 深拷贝了原始 SVG 的所有属性，包括 `style` 中的 `max-width`。

**解决**：克隆后 `clone.removeAttribute('style')`。

### 陷阱 4：SVG 无显式宽高 -> 浏览器默认 300x150px

**现象**：清除了所有属性后，图片变得极小。

**根因**：SVG 元素没有 `width`/`height` 属性时，浏览器按 CSS 默认值 300x150px 渲染，忽略 `viewBox`。

**解决**：从 `viewBox` 解析自然尺寸，按视口等比缩放后显式设置 `width`/`height`。

### 陷阱 5：ECharts SVG 无 viewBox -> 无法缩放

**现象**：ECharts 生成的 SVG 没有 `viewBox` 属性，清除 width/height 后只显示左上角局部。

**根因**：ECharts SVG 使用显式 width/height 而非 viewBox，清除后浏览器默认 300x150px。

**解决**：在移除宽高前保存原始尺寸，无 viewBox 时用原始宽高构造 viewBox：

```javascript
var origW = parseInt(clone.getAttribute('width'), 10);
var origH = parseInt(clone.getAttribute('height'), 10);
clone.removeAttribute('width');
clone.removeAttribute('height');
var cvb = clone.getAttribute('viewBox');
if (!cvb && origW > 0 && origH > 0) {
  cvb = '0 0 ' + origW + ' ' + origH;
  clone.setAttribute('viewBox', cvb);
}
```

### 陷阱 6：CSS `style.width = '100%'` 替代 viewBox -> 图片极小

**现象**：使用 `clone.style.width = '100%'` 代替 viewBox 缩放，图片仍然极小。

**根因**：SVG 的 width/height 移除后浏览器默认 300x150px。`width: 100%` 的参考系是父容器宽度，而父容器 `display: inline-flex` 的宽度由内容决定（即 SVG 的 300px），形成"100% of 300px = 300px"的死循环。

**解决**：必须使用 viewBox 等比缩放方案，而非 CSS 百分比。

### 陷阱 7：CSS `width:auto/height:auto` 覆盖 JS 设置的 width/height

**现象**：JS 正确设置了 SVG 的 width/height 属性，但图片仍然显示异常。

**根因**：CSS 规则 `.img-stage svg { width: auto; height: auto; }` 会覆盖 JS 通过 `setAttribute('width', ...)` 设置的 HTML 属性。CSS 属性优先级高于 HTML 属性。

**解决**：CSS 中**不要**对 `.img-stage svg` 设 `width: auto` 或 `height: auto`。仅使用 `max-width` 和 `max-height` 约束上限，让 JS 设置的显式 width/height 属性生效：

```css
/* 正确：仅约束上限 */
.img-stage svg { max-width: 90vw; max-height: 85vh; display: block; }
/* 错误：width:auto/height:auto 覆盖 JS 属性 */
/* .img-stage svg { width: auto; height: auto; } */
```

### 陷阱 8：SVG 克隆后 ID 重复 -> 样式丢失、箭头消失

**现象**：模态中的 Mermaid 流程图节点无填充色、边线消失、箭头不显示。

**根因**：Mermaid SVG 包含三处使用同一 `id` 的内容：SVG 根元素 ID、内嵌 `<style>` CSS 选择器、`<marker>` 定义和 `url(#...)` 引用。`cloneNode(true)` 后 DOM 中出现重复 ID，CSS 选择器仅匹配第一个元素，克隆体样式全部失效。

**解决**：使用 `deduplicateSvgId()` 函数（见 4.3 节），通过 XMLSerializer 序列化 -> 全局替换旧 ID -> DOMParser 解析回 DOM。

### 陷阱 9：`<script>` 标签内使用 HTML 实体编码 -> JS 语法错误

**现象**：修改图片查看器代码后，页面的所有 JavaScript 功能同时失效。

**根因**：在 `<script>` 标签内编写 JavaScript 代码时，使用了 HTML 实体编码（`&lt;=`、`&gt;=`）替代原始字符（`<=`、`>=`）。`<script>` 内是原始文本（CDATA），浏览器不解析 HTML 实体，导致 `SyntaxError`，整个 `<script>` 块不执行。

**解决**：在 `<script>` 标签内**永远使用原始字符**。

### 陷阱 10：正文文本中未转义的 `<style>` 标签 -> HTML 解析器误解析

**现象**：页面的所有 JavaScript 功能完全失效，浏览器控制台无任何错误。

**根因**：变更记录文本中包含未转义的 `<style>` 标签作为字面文本。HTML 解析器在 `<body>` 上下文中遇到 `<style>` 时，将其视为 HTML style 元素，后续所有内容被当作 CSS 文本。

**解决**：将正文文本中的 `<style>` 转义为 `&lt;style&gt;`。注意：`<script>` 标签内的 `<style>` 文本不需要转义，但会导致计数工具误报，应使用描述性文字替代。

### 陷阱 11：overflow:hidden + border-radius -> 布局错乱循环

**现象**：移除 `figure` 的 `overflow:hidden` 后子元素溢出圆角边界导致布局错乱；恢复后又裁剪 ECharts tooltip。

**根因**：`border-radius` 圆角容器必须配对 `overflow:hidden` 确保子元素被裁剪。但 `overflow:hidden` 同时裁剪 ECharts tooltip 弹出层。

**解决**：保持 `overflow:hidden`，使用 ECharts `tooltip.appendToBody: true` 将 tooltip 渲染到 `document.body`。**禁止为释放 tooltip 而移除 overflow:hidden**。

### 陷阱 12：ECharts 模态中用 SVG 克隆 -> 丢失交互

**现象**：ECharts 图表在模态中无法 hover 显示 tooltip。

**根因**：`cloneNode(true)` 仅复制 SVG DOM 结构，不复制 ECharts 的 JS 事件处理器。SVG 克隆体是静态的，无交互能力。

**解决**：模态中用 `echarts.getInstanceByDom()` 获取原始实例的 option，再用 `echarts.init()` 在新容器中重新初始化图表。关闭模态时调用 `chart.dispose()` 释放资源。

### 陷阱 13：ECharts 页面内无法交互 -> 预渲染 SVG 拦截事件

**现象**：ECharts 图表在页面内无法 hover 显示 tooltip，但在模态查看器中正常。

**根因**：构建时在 `chart-canvas` 容器内嵌了预渲染的 SVG 内容（含残留 `_echarts_instance_` 属性）。`echarts.init()` 创建的新实例生成的交互式 SVG 被旧 SVG 遮挡，鼠标事件被旧 SVG 拦截。

**解决**：`charts.js` 的 `initAll()` 中，初始化每个图表前先清除容器内预渲染内容：`el.innerHTML = '';`

### 陷阱 14：Mermaid SVG 拦截模态拖拽事件

**现象**：模态中 Mermaid 图片无法拖拽平移。

**根因**：Mermaid SVG 的节点和边线有默认的 pointer-events，拦截了 mousedown 事件，导致拖拽平移失效。

**解决**：模态中 Mermaid SVG 克隆体设 `pointer-events: none`，使鼠标事件穿透到 `.img-stage`。

### 陷阱 15：ECharts 模态中应用 transform -> 干扰交互

**现象**：ECharts 图表在模态中交互异常，tooltip 位置偏移。

**根因**：对 ECharts 容器应用 `transform: scale()` 会影响 ECharts 内部的事件坐标计算。

**解决**：ECharts 图表在模态中不应用缩放/平移 transform，设 `stage.style.transform = 'none'`。ECharts 图表通过 `ecContainer` 的显式 width/height 控制大小，不需要 CSS transform 缩放。

### 陷阱 16：图片序号错乱 -> 与文档顺序不一致

**现象**：文档中 9 张图片的 figcaption 序号（图 1-图 9）与文档实际出现顺序不一致，如第 1 张图标注为"图 5"、第 2 张图标注为"图 7"，序号乱序且重复。

**根因**：新增图表时直接复制已有 figure 模板，复制后只改了标题文字和 figure id，却**未同步更新 figcaption 中的序号**，也未对既有图表重新编号。随着多次新增，序号逐渐错乱。

**解决**：
1. 图片序号必须**按文档出现顺序连续递增**（图 1、图 2、图 3...），不能沿用复制来的旧序号。
2. 新增图表后，必须对**所有**既有图表重新编号，保证 1-N 连续无重复。
3. 序号同时出现在 figcaption 和模态工具栏标题（`#modalTitle`）中，两处必须一致。
4. 交付前用校验脚本检查序号是否连续（见 8.3 节）。

---

## 8. 文档结构一致性检查规则

### 8.1 三同步原则

任何内容变更后，以下三处必须同步更新：

1. **正文内容** -> 新增/修改章节后，正文中必须实际插入对应 HTML
2. **侧边栏目录** -> 新增章节锚点后，侧边栏 `<nav>` 中必须添加对应 `<a>` 条目
3. **版本号** -> 侧边栏、页脚、Badge 三处版本号必须一致

### 8.2 自动化检查脚本

将以下脚本保存为 `check-structure.sh`，每次交付前执行：

```bash
#!/bin/bash
# 用法: ./check-structure.sh <file.html>
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

echo "========================================="
echo "文档结构一致性检查"
echo "文件: $FILE"
echo "========================================="

# 1. TOC <-> 正文锚点
grep -oP 'href="#(sec-[^"]+)"' "$FILE" | sort > /tmp/_toc.txt
grep -oP 'id="(sec-[^"]+)"' "$FILE" | sort > /tmp/_body.txt
echo ""
echo "[1] TOC <-> 正文锚点一致性"
TOC_ONLY=$(comm -23 /tmp/_toc.txt /tmp/_body.txt)
BODY_ONLY=$(comm -13 /tmp/_toc.txt /tmp/_body.txt)
if [ -n "$TOC_ONLY" ]; then echo "  TOC 有但正文无:"; echo "$TOC_ONLY"; fi
if [ -n "$BODY_ONLY" ]; then echo "  正文有但 TOC 无:"; echo "$BODY_ONLY"; fi
if [ -z "$TOC_ONLY" ] && [ -z "$BODY_ONLY" ]; then echo "  OK 全部一致"; fi

# 2. 版本号
echo ""
echo "[2] 版本号一致性"
grep -n '版本 [0-9]\.[0-9][0-9]*' "$FILE"
echo "Badge 版本: $(grep -oP 'badge"[^>]*>v\K[0-9]+\.[0-9]+' "$FILE")"

# 3. HTML 结构
echo ""
echo "[3] HTML 结构完整性"
DIV_OPEN=$(grep -oP '<div\b' "$FILE" | wc -l)
DIV_CLOSE=$(grep -oP '</div>' "$FILE" | wc -l)
echo "  div 开: $DIV_OPEN  关: $DIV_CLOSE"
if [ "$DIV_OPEN" -eq "$DIV_CLOSE" ]; then echo "  OK div 平衡"; else echo "  WARN 不平衡 (差 $((DIV_OPEN - DIV_CLOSE)))"; fi
UNCLOSED=$(grep -Pn '</\w+\s*$' "$FILE" | wc -l)
if [ "$UNCLOSED" -eq 0 ]; then echo "  OK 无未闭合标签"; else echo "  WARN 存在 $UNCLOSED 个未闭合标签"; fi

echo ""
echo "========================================="
echo "检查完成"
echo "========================================="
```

### 8.3 图片序号连续性检查脚本

将以下脚本保存为 `check-figure-numbers.sh`，每次交付前执行：

```bash
#!/bin/bash
# 用法: ./check-figure-numbers.sh <file.html>
# 检查 figcaption 中的图片序号是否按文档出现顺序连续递增（1,2,3...N），
# 并校验模态标题 #modalTitle 的序号是否为有效图号。
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

echo "========================================="
echo "图片序号连续性检查"
echo "文件: $FILE"
echo "========================================="

# 提取 figcaption 中的序号（按文档出现顺序）
NUMS=$(grep -oP 'figcaption>图 \K\d+' "$FILE")
echo "文档中图片序号顺序: $NUMS"

FAIL=0

# 1) 检查是否 1,2,3...N 连续递增
IDX=1
for n in $NUMS; do
  if [ "$n" -ne "$IDX" ]; then
    echo "  FAIL: 第 $IDX 张图序号为 $n（应为 $IDX，须从 1 开始递增）"
    FAIL=1
  fi
  IDX=$((IDX + 1))
done

# 2) 检查是否有重复
DUP=$(echo "$NUMS" | tr ' ' '\n' | sort -n | uniq -d)
if [ -n "$DUP" ]; then
  echo "  FAIL: 存在重复序号: $DUP"
  FAIL=1
fi

# 3) 检查 figure 数量与序号数量是否一致
FIG_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
NUM_COUNT=$(echo "$NUMS" | wc -w)
if [ "$FIG_COUNT" -ne "$NUM_COUNT" ]; then
  echo "  FAIL: figure 数($FIG_COUNT) 与序号数($NUM_COUNT) 不一致"
  FAIL=1
fi

# 4) 校验模态标题 #modalTitle 序号为有效图号（1..N 且与某个 figcaption 一致）
echo ""
echo "[模态标题一致性]"
NUM_MAX=$((IDX - 1))
MT_COUNT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE" | wc -l)
if [ "$MT_COUNT" -ne 1 ]; then
  echo "  FAIL: modalTitle 数量为 $MT_COUNT（应为 1）"
  FAIL=1
else
  MT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE")
  echo "  modalTitle 序号: $MT"
  if [ "$MT" -lt 1 ] || [ "$MT" -gt "$NUM_MAX" ]; then
    echo "  FAIL: modalTitle 序号 $MT 超出有效范围 1..$NUM_MAX"
    FAIL=1
  else
    if ! echo "$NUMS" | tr ' ' '\n' | grep -qx "$MT"; then
      echo "  FAIL: modalTitle 序号 $MT 与任一 figcaption 序号不一致"
      FAIL=1
    else
      echo "  OK: modalTitle 序号 $MT 与 figcaption 一致"
    fi
  fi
fi

echo ""
echo "========================================="
if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED: 图片序号从 1 连续递增且无重复，modalTitle 一致"
else
  echo "SOME CHECKS FAILED: 请按文档顺序从 1 重新编号"
fi
echo "========================================="
exit "$FAIL"
```

> **规则**：图片序号必须从 1 开始按文档出现顺序连续递增（1, 2, 3...N）。新增图表后必须对所有既有图表重新编号，并同步更新 figcaption 与模态标题 `#modalTitle` 中的序号。交付前用 `check-figure-numbers.sh` 校验。

---

## 9. 查看按钮管理规则

### 9.1 单一来源原则

每个 `figure` 必须有且仅有一个"查看"按钮，且只能通过一种机制添加：

| 规则 | 要求 | 禁止 |
|------|------|------|
| R1 | 仅使用静态 HTML 按钮或动态 JS 之一 | 同时使用两种机制 |
| R2 | 使用静态 `<button class="zoom-btn">` | 动态 createElement + appendChild |
| R3 | 统一使用 CSS 类样式 | 内联 style 样式 |
| R4 | 添加按钮前先检查是否已有按钮 | 盲目追加新按钮 |

### 9.2 标准按钮 HTML

```html
<figure class="chart-figure" id="fig-xxx">
  <div class="fig-bar">
    <figcaption>图 N：标题</figcaption>
    <button class="zoom-btn" onclick="openImageModal('fig-xxx')">查看</button>
  </div>
  <div class="chart-canvas" id="chart-xxx"></div>
</figure>
```

### 9.3 按钮检查脚本

```bash
#!/bin/bash
# 用法: ./check-view-buttons.sh <file.html>
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

FIGURE_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
VIEW_BTN_COUNT=$(grep -oP 'class="zoom-btn"' "$FILE" | wc -l)
INLINE_BTN_COUNT=$(grep -oP '<button\s+style="[^"]*">查看</button>' "$FILE" | wc -l)
DYNAMIC_JS=$(grep -c 'appendChild.*btn\|createElement.*button.*查看' "$FILE")

echo "Figures: $FIGURE_COUNT, zoom-btn: $VIEW_BTN_COUNT, inline: $INLINE_BTN_COUNT, dynamic JS: $DYNAMIC_JS"
if [ "$VIEW_BTN_COUNT" -eq "$FIGURE_COUNT" ] && [ "$INLINE_BTN_COUNT" -eq 0 ] && [ "$DYNAMIC_JS" -eq 0 ]; then
  echo "OK: 每图恰好 1 个按钮"
else
  echo "FAIL: 按钮数量不一致或存在禁用模式"
fi
```

---

## 10. 综合校验脚本

以下脚本整合了所有校验规则，交付前必须执行：

```bash
#!/bin/bash
# 用法: ./check-modal-viewer.sh <file.html> [charts.js]
# 综合校验模态图片查看器的所有规则
FILE="${1:?用法: $0 <file.html> [charts.js]}"
CHARTS_JS="${2:-}"

echo "========================================="
echo "模态图片查看器综合校验"
echo "文件: $FILE"
echo "========================================="
FAIL=0

# === 1. div 标签平衡 ===
DIV_OPEN=$(grep -oP '<div\b' "$FILE" | wc -l)
DIV_CLOSE=$(grep -oP '</div>' "$FILE" | wc -l)
if [ "$DIV_OPEN" -eq "$DIV_CLOSE" ]; then
  echo "[1] div 平衡: OK ($DIV_OPEN = $DIV_CLOSE)"
else
  echo "[1] div 平衡: FAIL ($DIV_OPEN != $DIV_CLOSE)"; FAIL=1
fi

# === 2. 未闭合标签 ===
UNCLOSED=$(grep -Pn '</\w+\s*$' "$FILE" | wc -l)
if [ "$UNCLOSED" -eq 0 ]; then
  echo "[2] 未闭合标签: OK (0)"
else
  echo "[2] 未闭合标签: FAIL ($UNCLOSED)"; FAIL=1
fi

# === 3. script 内 HTML 实体编码 ===
ENTITY_CNT=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', c, re.DOTALL)
print(sum(s.count('&lt;') + s.count('&gt;') + s.count('&amp;') for s in scripts))
" 2>/dev/null)
if [ "$ENTITY_CNT" = "0" ]; then
  echo "[3] script 内 HTML 实体: OK (0)"
else
  echo "[3] script 内 HTML 实体: FAIL ($ENTITY_CNT)"; FAIL=1
fi

# === 4. body 上下文 style 标签平衡 ===
STYLE_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
body_only = re.sub(r'<svg\b.*?</svg>', '', c, flags=re.DOTALL)
body_only = re.sub(r'<script\b[^>]*>.*?</script>', '', body_only, flags=re.DOTALL)
opens = len(re.findall(r'<style\b', body_only))
closes = len(re.findall(r'</style>', body_only))
print('OK' if opens == closes else 'FAIL:%d opens vs %d closes' % (opens, closes))
" 2>/dev/null)
if [[ "$STYLE_CHECK" == OK* ]]; then
  echo "[4] body style 平衡: OK"
else
  echo "[4] body style 平衡: FAIL ($STYLE_CHECK)"; FAIL=1
fi

# === 5. figure.chart-figure 必须有 overflow:hidden ===
CHART_FIG_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
m = re.search(r'figure\.chart-figure\s*\{[^}]+\}', c)
print('PASS' if m and 'overflow' in m.group(0) else 'FAIL')
" 2>/dev/null)
if [ "$CHART_FIG_CHECK" = "PASS" ]; then
  echo "[5] chart-figure overflow:hidden: OK"
else
  echo "[5] chart-figure overflow:hidden: FAIL"; FAIL=1
fi

# === 6. figure.diagram 必须无 overflow ===
DIAGRAM_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
m = re.search(r'figure\.diagram\s*\{[^}]+\}', c)
print('PASS' if m and 'overflow' not in m.group(0) else 'FAIL')
" 2>/dev/null)
if [ "$DIAGRAM_CHECK" = "PASS" ]; then
  echo "[6] diagram 无 overflow: OK"
else
  echo "[6] diagram 无 overflow: FAIL"; FAIL=1
fi

# === 7. Mermaid SVG pointer-events: none ===
MERMAID_CHECK=$(grep -c 'mermaid-wrap svg.*pointer-events.*none' "$FILE" 2>/dev/null)
if [ "$MERMAID_CHECK" -gt 0 ]; then
  echo "[7] Mermaid pointer-events:none: OK"
else
  echo "[7] Mermaid pointer-events:none: FAIL"; FAIL=1
fi

# === 8. 模态中 ECharts 用 echarts.init ===
MODAL_ECHARTS=$(grep -c '_modalChart.*echarts.init' "$FILE" 2>/dev/null)
if [ "$MODAL_ECHARTS" -gt 0 ]; then
  echo "[8] 模态 ECharts 用 init(): OK"
else
  echo "[8] 模态 ECharts 用 init(): FAIL"; FAIL=1
fi

# === 9. 查看按钮数量 ===
FIG_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
BTN_COUNT=$(grep -oP 'class="zoom-btn"' "$FILE" | wc -l)
if [ "$FIG_COUNT" -eq "$BTN_COUNT" ]; then
  echo "[9] 查看按钮数量: OK ($FIG_COUNT = $BTN_COUNT)"
else
  echo "[9] 查看按钮数量: FAIL ($FIG_COUNT != $BTN_COUNT)"; FAIL=1
fi

# === 10. ECharts tooltip appendToBody (如果有 charts.js) ===
if [ -n "$CHARTS_JS" ] && [ -f "$CHARTS_JS" ]; then
  APPEND_CNT=$(grep -c 'appendToBody: true' "$CHARTS_JS" 2>/dev/null)
  if [ "$APPEND_CNT" -gt 0 ]; then
    echo "[10] ECharts appendToBody: OK ($APPEND_CNT 处)"
  else
    echo "[10] ECharts appendToBody: FAIL"; FAIL=1
  fi
fi

# === 11. ECharts 初始化前清除 innerHTML ===
if [ -n "$CHARTS_JS" ] && [ -f "$CHARTS_JS" ]; then
  CLEAR_CHECK=$(grep -c "innerHTML\s*=\s*''" "$CHARTS_JS" 2>/dev/null)
  if [ "$CLEAR_CHECK" -gt 0 ]; then
    echo "[11] ECharts 初始化前清除: OK"
  else
    echo "[11] ECharts 初始化前清除: FAIL"; FAIL=1
  fi
fi

# === 12. ECharts 模态缩放/平移守卫 ===
ZOOM_GUARD=$(grep -c '_modalChart.*return' "$FILE" 2>/dev/null)
if [ "$ZOOM_GUARD" -ge 2 ]; then
  echo "[12] ECharts 模态缩放守卫: OK ($ZOOM_GUARD 处)"
else
  echo "[12] ECharts 模态缩放守卫: FAIL ($ZOOM_GUARD 处，需 >= 2)"; FAIL=1
fi

# === 13. 图片序号连续性 ===
FIG_NUMS=$(grep -oP 'figcaption>图 \K\d+' "$FILE" 2>/dev/null)
FIG_NUM_COUNT=$(echo "$FIG_NUMS" | wc -w)
SEQ_FAIL=0
IDX=1
for n in $FIG_NUMS; do
  if [ "$n" -ne "$IDX" ]; then SEQ_FAIL=1; fi
  IDX=$((IDX + 1))
done
DUP=$(echo "$FIG_NUMS" | tr ' ' '\n' | sort -n | uniq -d)
# 校验 modalTitle 序号为有效图号（1..N 且与某个 figcaption 一致）
MT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE" 2>/dev/null)
NUM_MAX=$((IDX - 1))
MT_FAIL=0
[ -z "$MT" ] && MT_FAIL=1
if [ -n "$MT" ] && { [ "$MT" -lt 1 ] || [ "$MT" -gt "$NUM_MAX" ]; }; then MT_FAIL=1; fi
if [ -n "$MT" ] && ! echo "$FIG_NUMS" | tr ' ' '\n' | grep -qx "$MT"; then MT_FAIL=1; fi
if [ "$SEQ_FAIL" -eq 0 ] && [ -z "$DUP" ] && [ "$FIG_NUM_COUNT" -eq "$FIG_COUNT" ] && [ "$MT_FAIL" -eq 0 ]; then
  echo "[13] 图片序号连续性: OK (图序 $FIG_NUMS, modalTitle=$MT)"
else
  echo "[13] 图片序号连续性: FAIL (顺序: $FIG_NUMS, 重复: $DUP, 数: $FIG_NUM_COUNT/$FIG_COUNT, modalTitle=$MT)"; FAIL=1
fi

echo ""
echo "========================================="
if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "SOME CHECKS FAILED"
fi
echo "========================================="
```

---

## 11. 最佳实践

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
12. **图片序号从 1 开始连续递增**：新增图表后必须对所有既有图表重新编号（图 1-N），序号从 1 开始按文档出现顺序连续递增，并同步更新 figcaption 与模态标题 `#modalTitle` 中的序号，交付前用 `check-figure-numbers.sh` 校验。

---

## 12. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.04 | 2026-08-13 | 删除头部关于废弃 `模态图片查看器修复规则.md` 的"注意"说明（该文件已废弃，避免误导）。强化 8.3 节 `check-figure-numbers.sh` 与综合校验脚本第 13 项：新增 modalTitle 序号有效性校验（须为 1..N 且与某一 figcaption 一致，且数量为 1），明确图序须从 1 开始连续递增。同步更新检查清单 #24、最佳实践 #12 与 8.3 规则说明。 |
| v2.03 | 2026-08-13 | 修复图片序号校验脚本的 PCRE 转义错误：`grep -oP 'figcaption>\u56fe \K\d+'` 中的 `\u56fe` 不被 PCRE 支持（报错 "PCRE does not support \\u"），导致 8.3 节 `check-figure-numbers.sh` 与综合校验脚本第 13 项无法执行。已改为字面字符 `图`（`figcaption>图 \K\d+`），并同步修正 `#modalTitle` 序号提取的同类写法。 |
| v2.02 | 2026-08-13 | 新增陷阱 16（图片序号错乱）及解决规则；新增检查清单 #24；新增 8.3 节图片序号连续性检查脚本 `check-figure-numbers.sh`；综合校验脚本新增第 13 项图片序号连续性检查；新增最佳实践 #12。 |
| v2.01 | 2026-08-13 | 复核修复：`zoomImage`/`resetZoom`/`mousedown` 增加 ECharts 模态守卫（避免 transform 干扰交互）；`deduplicateSvgId` 用计数器替代 `Date.now()` 防碰撞；`initAll` 示例改为通用 `querySelectorAll`；修正最佳实践 #2/#3 与模板的矛盾；新增检查清单 #23 和校验脚本第 12 项；标注旧 `修复规则.md` 已废弃。 |
| v2.00 | 2026-08-13 | 全面重构：更新 HTML/CSS/JS 模板为统一顶部工具栏布局；新增 ECharts 页面内交互规则（初始化前清除预渲染 SVG、appendToBody 机制）；重组陷阱列表（移除旧陷阱 9-11 即"修改未持久化""Write 工具写错文件""ZIP 同步覆盖"，这些属于工作流问题而非查看器设计问题；新增陷阱 11-15 即 overflow:hidden 配对、ECharts 模态交互、预渲染 SVG 拦截事件、Mermaid pointer-events、transform 干扰 ECharts）；新增综合校验脚本（11 项检查）；更新集成检查清单至 22 项。整合 v0.01-v0.23 全部 bug 修复经验。 |
| v1.11 | 2026-08-12 | 优化陷阱 12 检查命令：排除 svg 和 script 块后检查 style 平衡。 |
| v1.10 | 2026-08-12 | 新增陷阱 12：正文文本中未转义的 style 标签。 |
| v1.09 | 2026-08-12 | 新增陷阱 11：分享包 ZIP 同步机制覆盖源文件。 |
| v1.08 | 2026-08-12 | 新增陷阱 10：Write 工具写入错误文件。 |
| v1.07 | 2026-08-12 | 新增陷阱 9：修改未持久化。 |
| v1.06 | 2026-08-12 | 新增陷阱 8：script 内 HTML 实体编码。 |
| v1.05 | 2026-08-12 | 新增陷阱 7：SVG 克隆后 ID 重复。 |
| v1.04 | 2026-08-12 | 新增按钮位置设计规范。 |
| v1.03 | 2026-08-12 | 新增查看按钮管理规则。 |
| v1.02 | 2026-08-12 | 新增文档结构一致性检查规则。 |
| v1.01 | 2026-08-12 | 新增陷阱 6：CSS style.width 替代 viewBox。 |
| v1.00 | 2026-08-12 | 从修复规则 v0.05 升级为完整设计 Skill 文档。 |
