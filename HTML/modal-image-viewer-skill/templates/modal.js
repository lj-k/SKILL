/* ============ 模态图片查看器 JS ============ */

/* 4.1 状态管理 */
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

/* 4.2 核心：showModalContent — 按类型区分渲染策略 */
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

/* 4.3 SVG ID 去重工具函数 */
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

/* 4.4 关闭、导航、缩放、平移 */
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