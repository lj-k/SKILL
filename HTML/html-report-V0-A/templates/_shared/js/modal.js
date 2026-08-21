/* ============ 模态图片查看器 JS ============
 * 源自 skill「modal-image-viewer-skill」（按名字调用，AI 自行定位其权威实现）。
 * html-report-V0-A 随附此适配副本，仅保证 scaffold 开箱即用；约束 1.2/1.4 的
 * 透明背景 / 白底图形区由 report.css 覆盖。请勿在此改动业务逻辑。
 */
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
  if (stage._modalChart) { stage._modalChart.dispose(); stage._modalChart = null; }
  stage.innerHTML = '';
  var clone;
  // 已渲染的 SVG 由 diagrams.js 注入在 .mermaid-wrap 内（与隐藏的 <pre> 同级兄弟节点），
  // 兼容 modal-image-viewer-skill 原始结构（SVG 置于 .mermaid 内），并兜底全图查找（规则 1.9）。
  var svg = fig.querySelector('.mermaid-wrap > svg') || fig.querySelector('.mermaid svg') || fig.querySelector('svg');
  if (svg) {
    clone = svg.cloneNode(true);
    clone.removeAttribute('width');
    clone.removeAttribute('height');
    clone.removeAttribute('style');
    clone = deduplicateSvgId(clone);
    var vb = clone.getAttribute('viewBox');
    if (vb) {
      var parts = vb.trim().split(/\s+/);
      if (parts.length === 4) {
        var vbW = parseFloat(parts[2]), vbH = parseFloat(parts[3]);
        var scale = Math.min(window.innerWidth * 0.9 / vbW, window.innerHeight * 0.85 / vbH);
        clone.setAttribute('width', Math.round(vbW * scale));
        clone.setAttribute('height', Math.round(vbH * scale));
      }
    }
    clone.setAttribute('style', 'pointer-events: none;');
    stage.appendChild(clone);
  } else {
    var chartDiv = fig.querySelector('.chart-canvas');
    if (chartDiv) {
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
      if (!stage._modalChart) {
        var chartSvg = chartDiv.querySelector('svg');
        if (chartSvg) {
          clone = chartSvg.cloneNode(true);
          var origW = parseInt(clone.getAttribute('width'), 10);
          var origH = parseInt(clone.getAttribute('height'), 10);
          clone.removeAttribute('width'); clone.removeAttribute('height'); clone.removeAttribute('style');
          clone = deduplicateSvgId(clone);
          var cvb = clone.getAttribute('viewBox');
          if (!cvb && origW > 0 && origH > 0) { cvb = '0 0 ' + origW + ' ' + origH; clone.setAttribute('viewBox', cvb); }
          if (cvb) {
            var cparts = cvb.trim().split(/\s+/);
            if (cparts.length === 4) {
              var cvbW = parseFloat(cparts[2]), cvbH = parseFloat(cparts[3]);
              var cscale = Math.min(window.innerWidth * 0.9 / cvbW, window.innerHeight * 0.85 / cvbH);
              clone.setAttribute('width', Math.round(cvbW * cscale));
              clone.setAttribute('height', Math.round(cvbH * cscale));
            }
          }
          stage.appendChild(clone);
        }
      }
    }
  }
  document.getElementById('navPrev').disabled = (modalState.index <= 0);
  document.getElementById('navNext').disabled = (modalState.index >= modalState.figures.length - 1);
  if (!stage._modalChart) resetZoom();
  else { modalState.scale = 1; modalState.panX = 0; modalState.panY = 0; stage.style.transform = 'none'; }
}
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
function navImage(dir) {
  var newIndex = modalState.index + dir;
  if (newIndex < 0 || newIndex >= modalState.figures.length) return;
  modalState.index = newIndex; showModalContent();
}
function closeImageModal() {
  document.getElementById('imgModal').classList.remove('open');
  document.removeEventListener('keydown', modalKeyHandler);
  window.removeEventListener('resize', modalResizeHandler);
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) { stage._modalChart.dispose(); stage._modalChart = null; }
}
function modalResizeHandler() {
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) stage._modalChart.resize();
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
  if (stage._modalChart) return;
  modalState.scale = Math.max(0.3, Math.min(5, modalState.scale + delta));
  applyTransform();
}
function resetZoom() {
  var stage = document.getElementById('imgStage');
  if (stage._modalChart) return;
  modalState.scale = 1; modalState.panX = 0; modalState.panY = 0; applyTransform();
}
function applyTransform() {
  var stage = document.getElementById('imgStage');
  stage.style.transform = 'translate(' + modalState.panX + 'px,' + modalState.panY + 'px) scale(' + modalState.scale + ')';
}
(function () {
  var stage = document.getElementById('imgStage');
  stage.addEventListener('mousedown', function (e) {
    if (stage._modalChart) return;
    modalState.isDragging = true;
    modalState.startX = e.clientX - modalState.panX;
    modalState.startY = e.clientY - modalState.panY;
    stage.classList.add('dragging'); e.preventDefault();
  });
  document.addEventListener('mousemove', function (e) {
    if (!modalState.isDragging) return;
    modalState.panX = e.clientX - modalState.startX;
    modalState.panY = e.clientY - modalState.startY;
    applyTransform();
  });
  document.addEventListener('mouseup', function () { modalState.isDragging = false; stage.classList.remove('dragging'); });
  var modal = document.getElementById('imgModal');
  modal.addEventListener('wheel', function (e) {
    if (!modal.classList.contains('open')) return;
    e.preventDefault();
    zoomImage(e.deltaY < 0 ? 0.15 : -0.15);
  }, { passive: false });
})();
