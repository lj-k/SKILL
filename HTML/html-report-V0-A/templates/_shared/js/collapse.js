/* =========================================================================
 * collapse.js —— 标题折叠（3.2）+ 代码块默认折叠（3.1）
 * 用法：在 report.html 末尾 <script src="_shared/js/collapse.js"></script> 引入。
 *  - 折叠对象：.section 的直接子标题 h1~h4；点击标题折叠其 .section-content。
 *  - 折叠后调用 window.__tocRefresh()（toc.js 暴露）重算目录高亮（规则 2.6 位置漂移）。
 *  - 代码块：所有 <pre>（除 .mermaid 外）默认折叠，提供"代码 ▸/▾"开关。
 * 模板约定：每个章节用 <div class="section"><hN>..</hN><div class="section-content">..</div></div>
 * ========================================================================= */
(function () {
  'use strict';
  function init() {
    var main = document.getElementById('main');
    if (!main) return;

    main.querySelectorAll('.section > h1, .section > h2, .section > h3, .section > h4').forEach(function (h) {
      var sec = h.parentElement;
      if (!sec || !sec.classList.contains('section')) return;
      var marker = h.querySelector(':scope > .fold-marker');
      if (!marker) { marker = document.createElement('span'); marker.className = 'fold-marker'; h.insertBefore(marker, h.firstChild); }
      h.classList.add('collapsible');
      h.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return;            // 不拦截标题内跳转链接
        sec.classList.toggle('collapsed');
        if (window.__tocRefresh) setTimeout(window.__tocRefresh, 320);
      });
    });

    main.querySelectorAll('pre:not(.mermaid)').forEach(function (pre) {
      if (pre.closest('.code-block')) return;
      var wrap = document.createElement('div'); wrap.className = 'code-block code-collapsed';
      pre.parentNode.insertBefore(wrap, pre); wrap.appendChild(pre);
      // 代码标题（3.1）：pre[data-title] 生成 .code-title 标题栏（参考成熟实现 summary 语义）
      if (pre.getAttribute('data-title')) {
        var title = document.createElement('div'); title.className = 'code-title';
        title.textContent = pre.getAttribute('data-title');
        wrap.insertBefore(title, pre);
      }
      var btn = document.createElement('button'); btn.className = 'code-toggle'; btn.textContent = '代码 ▸';
      wrap.insertBefore(btn, pre);
      btn.addEventListener('click', function () {
        wrap.classList.toggle('code-collapsed');
        btn.textContent = wrap.classList.contains('code-collapsed') ? '代码 ▸' : '代码 ▾';
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
