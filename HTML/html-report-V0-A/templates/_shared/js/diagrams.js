/* =========================================================================
 * diagrams.js —— Mermaid 运行时渲染 + 直角连线（0.4）+ 自动注入"查看"按钮（1.1 单一来源）
 * 用法：report.html 中先引入 mermaid CDN，再 <script src="_shared/js/diagrams.js"></script>。
 *  - 0.4 架构框图连线使用直角连线：flowchart curve='stepBefore'（原生可靠，非 DOM 手术）。
 *  - 0.1 含文字图形低饱和底色：themeVariables 设浅色填充（详见 report.css .mermaid 规则）。
 *  - 0.2/0.3 连线与箭头复查：Mermaid 原生把边端点吸附到节点边界（box edge），无需手工处理；
 *         交付前建议人工复核方向/语义与意图一致。
 *  - 1.1 每个 figure.diagram 保证有且仅有一个"查看"按钮（缺失则自动补齐，单一来源原则）。
 * ========================================================================= */
(function () {
  'use strict';

  function renderMermaid() {
    if (typeof mermaid === 'undefined') return;
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: 'loose',
      theme: 'base',
      flowchart: { curve: 'stepBefore', htmlLabels: true, useMaxWidth: false, rankSpacing: 40, nodeSpacing: 40 },
      themeVariables: {
        background: '#ffffff',
        primaryColor: '#f6f8fa', primaryBorderColor: '#6b7280', primaryTextColor: '#1f2937',
        lineColor: '#6b7280', secondaryColor: '#fef9c3', tertiaryColor: '#eef2ff',
        fontFamily: 'inherit'
      }
    });
    var pres = Array.prototype.slice.call(document.querySelectorAll('pre.mermaid'));
    var i = 0;
    function renderOne() {
      if (i >= pres.length) return;
      var p = pres[i++];
      try {
        var res = mermaid.render('mmd-' + Date.now() + '-' + i, p.textContent);
        Promise.resolve(res).then(function (r) { place(r && r.svg ? r.svg : res, p); }).catch(function () { place(null, p); });
      } catch (e) { place(null, p); }
      renderOne();
    }
    function place(svg, p) {
      if (!svg) return;
      var tmp = document.createElement('div');
      tmp.innerHTML = (typeof svg === 'string') ? svg : new XMLSerializer().serializeToString(svg);
      var s = tmp.querySelector('svg');
      if (s) { p.parentNode.insertBefore(s, p); p.style.display = 'none'; }
    }
    renderOne();
  }

  function ensureButtons() {                 // 1.1 查看按钮单一来源
    document.querySelectorAll('figure.diagram').forEach(function (fig) {
      if (fig.querySelector('.zoom-btn')) return;
      var bar = fig.querySelector('.fig-bar') || fig;
      var btn = document.createElement('button');
      btn.className = 'zoom-btn';
      btn.setAttribute('onclick', "openImageModal('" + fig.id + "')");
      btn.textContent = '查看';
      bar.appendChild(btn);
    });
  }

  function init() { ensureButtons(); renderMermaid(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
