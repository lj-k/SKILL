/* =========================================================================
 * toc.js —— 动态目录 + 滚动高亮(scroll-spy) + 固定/滚动级别 + 移动端目录
 *          + 侧边栏折叠 + 文内引用悬停预览（3.4）
 * 用法：在 report.html 末尾 <script src="_shared/js/toc.js"></script> 引入即可，
 *       无需任何额外调用。依赖 DOM 中存在：
 *         #main(正文) / #toc-list(侧边栏目录) / #mobile-toc-list(移动端目录)
 *         #level-fixed / #level-scroll(级别下拉) / #sidebar-toggle(侧栏开关)
 *         #mobile-toc-fab / #mobile-toc-panel(移动端)
 * 目录由 JS 从正文标题树动态生成（规则 2.1/2.8：收录所有级别标题）。
 * 暴露 window.__tocRefresh() 供 collapse.js 在折叠后重算高亮（规则 2.6）。
 * ========================================================================= */
(function () {
  'use strict';
  var main = document.getElementById('main');
  if (!main) return;

  var allNodes = [], flatNodes = [], maxLevel = 1, levelCount = {};
  var fixedLevel = 2, scrollLevel = 2, activeId = '', activePath = {};

  function levelOf(tag) { return parseInt(tag.charAt(1), 10); }

  function buildTree() {
    allNodes = []; flatNodes = []; maxLevel = 1; levelCount = {};
    var heads = Array.prototype.slice.call(main.querySelectorAll('h1,h2,h3,h4,h5,h6'));
    var stack = [], idx = 0;
    heads.forEach(function (h) {
      if (!h.id) h.id = 'toc-' + (idx++);
      var lv = levelOf(h.tagName);
      if (lv > maxLevel) maxLevel = lv;
      levelCount[lv] = (levelCount[lv] || 0) + 1;   // 统计各级标题数量（级别菜单显示 Hn (count)）
      // 标题文本须剔除已注入的 .sec-num 序号 span，否则折叠/刷新后目录条目重复显示序号
      var titleText = h.textContent.trim();
      var secNumSpan = h.querySelector(':scope > .sec-num');
      if (secNumSpan) titleText = titleText.replace(secNumSpan.textContent, '').trim();
      var node = { el: h, id: h.id, level: lv, title: titleText, children: [], parent: null, number: '' };
      while (stack.length && stack[stack.length - 1].level >= lv) stack.pop();
      if (stack.length === 0) allNodes.push(node);
      else { var p = stack[stack.length - 1]; p.children.push(node); node.parent = p; }
      stack.push(node);
      flatNodes.push(node);
    });
    (function numberize(list, prefix) {
      list.forEach(function (n, i) {
        n.number = prefix ? prefix + '.' + (i + 1) : String(i + 1);
        numberize(n.children, n.number);
      });
    })(allNodes, '');
  }

  // 标题自动编号：注入 <span class="sec-num">（规则 3.2，避免手工编号漏改）
  function numberHeadings() {
    flatNodes.forEach(function (n) {
      var span = n.el.querySelector(':scope > .sec-num');
      if (!span) { span = document.createElement('span'); span.className = 'sec-num'; n.el.insertBefore(span, n.el.firstChild); }
      span.textContent = n.number + ' ';
    });
  }

  // 可见性规则（移植成熟实现例1/例2/例3）：
  //   例1 固定骨架：level ≤ fixedLevel 始终显示；
  //   例3 滚动级别 ≤ 固定级别时不生效；
  //   活动路径上的节点：level ≤ scrollLevel 显示；
  //   例2 路径节点的直接子节点：父级 ≥ fixedLevel 且自身 ≤ scrollLevel 时展开显示。
  function isVisible(node) {
    if (node.level <= fixedLevel) return true;
    if (scrollLevel <= fixedLevel) return false;
    if (activePath[node.id]) return node.level <= scrollLevel;
    if (node.parent && activePath[node.parent.id] &&
        node.parent.level >= fixedLevel && node.level <= scrollLevel) return true;
    return false;
  }

  function scrollToId(id) {
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function buildList(list) {
    var ul = document.createElement('ul');
    ul.className = 'toc-ul toc-l' + (list[0] ? list[0].level : 1);
    list.forEach(function (n) {
      var li = document.createElement('li');
      li.className = 'toc-item'; li.dataset.id = n.id; li.dataset.level = n.level;
      var a = document.createElement('a');
      a.href = '#' + n.id; a.className = 'toc-link';
      a.textContent = n.number + ' ' + n.title;
      a.addEventListener('click', function (e) { e.preventDefault(); scrollToId(n.id); closeMobilePanel(); });
      li.appendChild(a);
      if (n.children.length) li.appendChild(buildList(n.children));
      ul.appendChild(li);
    });
    return ul;
  }

  function renderInto(container) {
    if (!container) return;
    container.innerHTML = '';
    container.appendChild(buildList(allNodes));
  }

  function centerActive(a) {
    var sb = document.getElementById('toc-list');
    if (sb && sb.scrollHeight > sb.clientHeight) sb.scrollTop = a.offsetTop - sb.clientHeight / 2 + a.clientHeight / 2;
    var mb = document.querySelector('.mobile-toc-body');
    if (mb) mb.scrollTop = a.offsetTop - mb.clientHeight / 2 + a.clientHeight / 2;
  }

  function updateVisibility() {
    var links = document.querySelectorAll('.toc-link');
    Array.prototype.forEach.call(links, function (a) {
      var li = a.parentElement;
      var node = null;
      for (var i = 0; i < flatNodes.length; i++) if (flatNodes[i].id === li.dataset.id) { node = flatNodes[i]; break; }
      if (!node) return;
      li.style.display = isVisible(node) ? '' : 'none';
      if (node.id === activeId) { a.classList.add('active'); centerActive(a); }
      else a.classList.remove('active');
    });
  }

  function onScroll() {
    var y = window.scrollY + 120, cur = '';
    for (var i = 0; i < flatNodes.length; i++) {
      var top = flatNodes[i].el.getBoundingClientRect().top + window.scrollY;
      if (top <= y) cur = flatNodes[i].id; else break;
    }
    if (cur === activeId) { updateVisibility(); return; }
    activeId = cur; activePath = {};
    var node = null;
    for (var j = 0; j < flatNodes.length; j++) if (flatNodes[j].id === cur) { node = flatNodes[j]; break; }
    while (node) { activePath[node.id] = true; node = node.parent; }
    updateVisibility();
  }

  // 级别切换：按钮 + 下拉菜单（菜单项显示 "Hn (标题数)"，参考成熟实现）
  function fillMenu(menu, key) {
    if (!menu) return;
    menu.innerHTML = '';
    for (var l = 1; l <= maxLevel; l++) {
      (function (v) {
        var b = document.createElement('button');
        b.type = 'button';
        b.textContent = 'H' + v + ' (' + (levelCount[v] || 0) + ')';
        if (v === (key === 'fixed' ? fixedLevel : scrollLevel)) b.classList.add('sel');
        b.addEventListener('click', function () {
          if (key === 'fixed') { fixedLevel = v; var fb = document.getElementById('toc-fixed-btn'); if (fb) fb.textContent = '固定级别: H' + v; }
          else { scrollLevel = v; var sb = document.getElementById('toc-scroll-btn'); if (sb) sb.textContent = '滚动级别: H' + v; }
          closeLevelMenus();
          fillMenu(document.getElementById('toc-fixed-menu'), 'fixed');
          fillMenu(document.getElementById('toc-scroll-menu'), 'scroll');
          updateVisibility();
        });
        menu.appendChild(b);
      })(l);
    }
  }

  function closeLevelMenus() {
    var fm = document.getElementById('toc-fixed-menu'), sm = document.getElementById('toc-scroll-menu');
    if (fm) fm.classList.remove('open');
    if (sm) sm.classList.remove('open');
  }

  function bindLevel() {
    var fb = document.getElementById('toc-fixed-btn'), sb = document.getElementById('toc-scroll-btn');
    var fm = document.getElementById('toc-fixed-menu'), sm = document.getElementById('toc-scroll-menu');
    if (fb && fm) fb.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = fm.classList.toggle('open'); if (sm) sm.classList.remove('open');
      if (open) fillMenu(fm, 'fixed');
    });
    if (sb && sm) sb.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = sm.classList.toggle('open'); if (fm) fm.classList.remove('open');
      if (open) fillMenu(sm, 'scroll');
    });
    document.addEventListener('click', closeLevelMenus);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLevelMenus(); });
  }

  var mobileFab = null, mobilePanel = null, mobileLevelBtns = null;

  // 展开/收起移动端面板：display 由 JS 权威设定（不依赖 CSS 是否加载），FAB 兼关闭按钮（✕/☰）
  function openMobilePanel() {
    if (!mobilePanel || !mobileFab) return;
    mobilePanel.classList.add('open');
    mobilePanel.style.display = 'flex';     // 权威显示
    mobilePanel.style.background = '#fff';  // 权威白底（防止 report.css 未加载时透明）
    mobilePanel.style.maxHeight = '33vh';   // 2.7 高度上限：不超过视口 1/3（JS 权威兜底）
    // 目录少时自动降低面板高度（移植成熟实现）：每项约 1.7vh，下限 10vh，上限 25vh（≤ 1/3 视口）
    var list = document.getElementById('mobile-toc-list');
    var items = list ? list.querySelectorAll('li').length : 0;
    mobilePanel.style.height = Math.max(10, Math.min(25, items * 1.7 + 4)) + 'vh';
    mobileFab.textContent = '✕';
    if (mobileLevelBtns) mobileLevelBtns.classList.add('visible');
  }
  function closeMobilePanel() {
    if (!mobilePanel || !mobileFab) return;
    mobilePanel.classList.remove('open');
    mobilePanel.style.display = 'none';      // 权威隐藏
    mobileFab.textContent = '☰';
    if (mobileLevelBtns) mobileLevelBtns.classList.remove('visible');
  }

  // 2.7 移动端目录：FAB（在 .fab-stack 内）点击展开/收起；面板固定视口底由 JS 强制定位
  function initToggles() {
    var st = document.getElementById('sidebar-toggle');
    if (st) st.addEventListener('click', function () { document.body.classList.toggle('sidebar-collapsed'); });
    mobileFab = document.getElementById('mobile-toc-fab');
    mobilePanel = document.getElementById('mobile-toc-panel');
    mobileLevelBtns = document.getElementById('mobile-level-btns');
    if (mobileFab && mobilePanel) {
      // 权威设置面板定位：固定视口底（即使 report.css 未加载也生效）
      mobilePanel.style.position = 'fixed';
      mobilePanel.style.left = '0'; mobilePanel.style.right = '0'; mobilePanel.style.bottom = '0';
      mobilePanel.style.background = '#fff';   // 权威白底兜底
      mobileFab.addEventListener('click', function () {
        if (mobilePanel.classList.contains('open')) closeMobilePanel(); else openMobilePanel();
      });
      mobilePanel.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') closeMobilePanel();   // 点击目录项收起
      });
    }
    // 移动端级别按钮（对齐成熟实现）：点击循环 H1..HmaxLevel，同步侧栏下拉并刷新可见性
    var mFixedBtn = document.getElementById('mobile-fixed-btn');
    var mScrollBtn = document.getElementById('mobile-scroll-btn');
    function setMobileLevelBtn(which, v) {
      var b = document.getElementById(which === 'fixed' ? 'mobile-fixed-btn' : 'mobile-scroll-btn');
      if (b) b.textContent = 'H' + v;
    }
    if (mFixedBtn) mFixedBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      fixedLevel = (fixedLevel % maxLevel) + 1;
      setMobileLevelBtn('fixed', fixedLevel);
      var f = document.getElementById('level-fixed'); if (f) f.value = fixedLevel;
      updateVisibility();
    });
    if (mScrollBtn) mScrollBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      scrollLevel = (scrollLevel % maxLevel) + 1;
      setMobileLevelBtn('scroll', scrollLevel);
      var s = document.getElementById('level-scroll'); if (s) s.value = scrollLevel;
      updateVisibility();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobilePanel && mobilePanel.classList.contains('open')) closeMobilePanel();
    });
  }

  // 2.7 窄屏显示 FAB、宽屏隐藏 FAB 与面板（JS 权威控制，不依赖 CSS 媒体查询/预览容器视口误判）
  function syncMobileToc() {
    if (!mobileFab || !mobilePanel) return;
    if (window.innerWidth > 768) {
      mobileFab.style.display = 'none';
      closeMobilePanel();
    } else {
      mobileFab.style.display = '';          // 交还 CSS：窄屏显示 FAB
      mobilePanel.style.display = 'none';   // 窄屏默认隐藏面板，仅 FAB 可见，点击才展开
    }
  }

  // 文内引用悬停预览（规则 3.4）：事件委托（移植成熟实现），兼容动态目录/折叠生成的链接
  function initLinkTooltip() {
    var tip = document.createElement('div'); tip.className = 'link-tooltip'; tip.style.display = 'none';
    document.body.appendChild(tip);
    document.addEventListener('mouseover', function (e) {
      var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (!a || a.classList.contains('toc-link')) return;
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if (!t) return;
      tip.textContent = t.textContent.trim().slice(0, 200);
      tip.style.display = 'block';
      tip._link = a;
    });
    document.addEventListener('mousemove', function (e) {
      if (tip.style.display !== 'none') {
        tip.style.left = (e.clientX + 12) + 'px';
        tip.style.top = (e.clientY + 12) + 'px';
      }
    });
    document.addEventListener('mouseout', function (e) {
      var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (a && a === tip._link) return;   // 仍在同一链接内
      tip.style.display = 'none';
    });
  }

  // 回到顶部按钮滚动显隐（移植成熟实现）：滚动超过阈值显示
  function initBackToTop() {
    var btn = document.getElementById('back-to-top');
    if (!btn) return;
    function upd() { btn.classList.toggle('visible', window.scrollY > 300); }
    upd();
    window.addEventListener('scroll', upd, { passive: true });
  }

  function init() {
    buildTree(); numberHeadings();
    renderInto(document.getElementById('toc-list'));
    renderInto(document.getElementById('mobile-toc-list'));
    bindLevel(); initToggles();
    var fb0 = document.getElementById('toc-fixed-btn'), sb0 = document.getElementById('toc-scroll-btn');
    if (fb0) fb0.textContent = '固定级别: H' + fixedLevel;
    if (sb0) sb0.textContent = '滚动级别: H' + scrollLevel;
    onScroll();                                   // 立即渲染一次，避免初始空目录
    window.addEventListener('scroll', onScroll, { passive: true });
    syncMobileToc();                              // 2.7 初始化即按视口权威控制移动端目录显隐
    window.addEventListener('resize', syncMobileToc);
    window.__tocRefresh = function () {
      buildTree(); numberHeadings();
      renderInto(document.getElementById('toc-list'));
      renderInto(document.getElementById('mobile-toc-list'));
      onScroll();
    };
    initLinkTooltip();
    initBackToTop();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
