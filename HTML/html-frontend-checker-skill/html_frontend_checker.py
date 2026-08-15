#!/usr/bin/env python3
"""
HTML Frontend Checker v0.01
Comprehensive HTML document checker based on historical bug analysis.
Derived from 40+ bugs across 5 documentation projects (C910, GEM5, SOC, CHI, CMN-700).

Usage:
    python3 html_frontend_checker.py --file path/to/file.html
    python3 html_frontend_checker.py --dir path/to/directory
    python3 html_frontend_checker.py --list
    python3 html_frontend_checker.py --file path/to/file.html --tags structure,css
"""

import os
import re
import sys
import time
import argparse
import html as html_module
from collections import defaultdict, OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed

# ============================================================================
# Registry
# ============================================================================

_TEST_REGISTRY = []

def register(category, name, tags=None, description=""):
    def decorator(func):
        _TEST_REGISTRY.append((func, category, name, tags or [], description or func.__doc__ or ""))
        return func
    return decorator

# ============================================================================
# Utility Functions
# ============================================================================

def count_tag(content, tag):
    """Count opening and closing tags for a given tag name."""
    open_count = len(re.findall(r'<' + tag + r'[\s>]', content))
    close_count = len(re.findall(r'</' + tag + r'>', content))
    return open_count, close_count

def strip_script_style(content):
    """Remove <script>...</script> and <style>...</style> blocks so anchor/id
    scans do not match JS comments or CSS selectors (common false-positive source)."""
    text = re.sub(r'<script\b[^>]*>.*?</script>', ' ', content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style\b[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    return text

def extract_id_matches(content):
    """Extract all id attributes from HTML content (ignores <script>/<style>)."""
    return re.findall(r'id="([^"]+)"', strip_script_style(content))

def extract_href_anchors(content):
    """Extract all href="#xxx" anchors from HTML content (ignores <script>/<style>)."""
    return re.findall(r'href="#([^"]+)"', strip_script_style(content))

# ---------------------------------------------------------------------------
# Generic scroll-spy detection (replaces brittle initScrollSpy name check)
# ---------------------------------------------------------------------------
SCROLLSPY_NAMES = ['initScrollSpy', 'scrollSpy', 'scrollspy', 'spy', 'updateSpy',
                   'activateNav', 'setActiveNav', 'initNavSpy', 'onScroll', 'navSpy']

def detect_scrollspy(content):
    """Heuristically detect whether a scroll-spy (active-nav highlighting) mechanism
    exists. Catches ANY naming convention, not just initScrollSpy."""
    has_def = any(re.search(
        r'(?:function\s+' + re.escape(n) + r'\b|' + re.escape(n) + r'\s*=\s*function|'
        r'const\s+' + re.escape(n) + r'\b|let\s+' + re.escape(n) + r'\b|var\s+' + re.escape(n) + r'\b)',
        content) for n in SCROLLSPY_NAMES)
    has_call = any((n + '()' in content) or (n + '();' in content) for n in SCROLLSPY_NAMES)
    has_scroll_listener = bool(re.search(r'addEventListener\s*\(\s*["\']scroll["\']', content))
    has_active_toggle = bool(re.search(
        r'classList\.(?:add|remove|toggle)\s*\(\s*[^)]*active', content, re.I)) or \
        bool(re.search(r'\.(?:active|nav-active|current)\b', content))
    has_rect = 'getBoundingClientRect' in content
    mechanism = has_def or (has_scroll_listener and has_active_toggle) or (has_scroll_listener and has_rect)
    return {"has_def": has_def, "has_call": has_call,
            "has_scroll_listener": has_scroll_listener,
            "has_active_toggle": has_active_toggle, "has_rect": has_rect,
            "mechanism": mechanism}

def _norm_nav_text(s):
    """Normalize nav/heading text for lenient comparison: drop whitespace, fold
    arrows/bullets, strip parentheticals and leading numbering."""
    if not s:
        return ""
    s = re.sub(r'\s+', '', s)
    for ch in '▾▸▶▼▲◂◀→←•·':
        s = s.replace(ch, '')
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'^[\d.．、]+', '', s)
    return s.lower()

def find_script_position(content):
    """Find the position of the first <script> tag that contains inline JS (not external src)."""
    for i, line in enumerate(content.split('\n')):
        if '<script>' in line or ('<script ' in line and 'src=' not in line):
            return i
    return -1

def find_element_position(content, element_id):
    """Find the line number of an element with given id."""
    for i, line in enumerate(content.split('\n')):
        if f'id="{element_id}"' in line or f"id='{element_id}'" in line:
            return i
    return -1

# ============================================================================
# 1. STRUCTURE CHECKS (18 checks)
# ============================================================================

@register("结构检查", "DOCTYPE声明", ["structure"])
def check_doctype(content, lines, file_path):
    if '<!DOCTYPE html>' in content or '<!DOCTYPE HTML>' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "fail", "detail": "缺失 <!DOCTYPE html>"}

@register("结构检查", "html lang属性", ["structure"])
def check_html_lang(content, lines, file_path):
    m = re.search(r'<html\s+[^>]*lang="([^"]+)"', content)
    if m:
        lang = m.group(1)
        if lang in ('zh-CN', 'zh', 'en'):
            return {"status": "pass", "detail": f"lang={lang}"}
        return {"status": "warning", "detail": f"lang={lang}，建议使用 zh-CN"}
    return {"status": "warning", "detail": "缺失 lang 属性"}

@register("结构检查", "charset声明", ["structure"])
def check_charset(content, lines, file_path):
    if 'charset="UTF-8"' in content or 'charset="utf-8"' in content or 'charset=UTF-8' in content:
        return {"status": "pass", "detail": "UTF-8"}
    return {"status": "fail", "detail": "缺失 charset 声明"}

@register("结构检查", "div标签配对", ["structure", "tag"])
def check_div_pairing(content, lines, file_path):
    o, c = count_tag(content, 'div')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}，差{abs(o-c)}"}

@register("结构检查", "未闭合标签行", ["structure", "tag"])
def check_unclosed_tags(content, lines, file_path):
    """Rule 4.2: grep -P '</\\w+\\s*$' file.html should output 0 lines."""
    bad_lines = []
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if re.search(r'</\w+\s*$', stripped) and not stripped.startswith('//'):
            # Exclude lines that are purely closing tags on their own (which is normal)
            # This check targets malformed closing patterns
            if not re.match(r'^\s*</\w+>\s*$', stripped):
                bad_lines.append(i + 1)
    if bad_lines:
        return {"status": "fail", "detail": f"行 {bad_lines[:5]}"}
    return {"status": "pass", "detail": "0行"}

@register("结构检查", "html/body配对", ["structure", "tag"])
def check_html_body_pairing(content, lines, file_path):
    ho, hc = count_tag(content, 'html')
    bo, bc = count_tag(content, 'body')
    if ho == hc and bo == bc:
        return {"status": "pass", "detail": f"html {ho}/{hc}, body {bo}/{bc}"}
    return {"status": "fail", "detail": f"html {ho}/{hc}, body {bo}/{bc}"}

@register("结构检查", "script标签配对", ["structure", "tag"])
def check_script_pairing(content, lines, file_path):
    o, c = count_tag(content, 'script')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "style标签配对", ["structure", "tag"])
def check_style_pairing(content, lines, file_path):
    o, c = count_tag(content, 'style')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "code标签配对", ["structure", "tag"])
def check_code_pairing(content, lines, file_path):
    o, c = count_tag(content, 'code')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}（可能有stray标签或双层嵌套）"}

@register("结构检查", "pre标签配对", ["structure", "tag"])
def check_pre_pairing(content, lines, file_path):
    o, c = count_tag(content, 'pre')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "figure标签配对", ["structure", "tag"])
def check_figure_pairing(content, lines, file_path):
    o, c = count_tag(content, 'figure')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "details标签配对", ["structure", "tag"])
def check_details_pairing(content, lines, file_path):
    o, c = count_tag(content, 'details')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "article标签配对", ["structure", "tag"])
def check_article_pairing(content, lines, file_path):
    o, c = count_tag(content, 'article')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "section标签配对", ["structure", "tag"])
def check_section_pairing(content, lines, file_path):
    o, c = count_tag(content, 'section')
    if o == c:
        return {"status": "pass", "detail": f"{o}/{c}"}
    return {"status": "fail", "detail": f"开{o}/关{c}"}

@register("结构检查", "标题层级完整性", ["structure"])
def check_heading_hierarchy(content, lines, file_path):
    """Check h2->h3->h4 ordering, no skipped levels."""
    headings = re.findall(r'<(h[1-6])[^>]*>', content)
    if not headings:
        return {"status": "pass", "detail": "无标题（可能为非标准文档）"}
    issues = []
    prev_level = 0
    for h in headings:
        level = int(h[1])
        if prev_level > 0 and level > prev_level + 1:
            issues.append(f"{h}跳级（前{prev_level}→{level}）")
        prev_level = level
    if issues:
        return {"status": "warning", "detail": "；".join(issues[:3])}
    return {"status": "pass", "detail": f"{len(headings)}个标题，层级连续"}

@register("结构检查", "DOM元素位置(script前)", ["structure", "js"])
def check_dom_element_position(content, lines, file_path):
    """Bug C910 v0.06: HTML elements after <script> cause getElementById() to return null."""
    interactive_ids = ['back-to-top', 'link-tooltip', 'diagram-modal', 'diagram-modal-content',
                       'diagram-modal-body', 'sidebar', 'main']
    script_pos = find_script_position(content)
    if script_pos < 0:
        return {"status": "pass", "detail": "无内联script"}
    issues = []
    for eid in interactive_ids:
        pos = find_element_position(content, eid)
        if pos > script_pos:
            issues.append(f"#{eid}在第{pos+1}行（script在第{script_pos+1}行之后）")
    if issues:
        return {"status": "fail", "detail": "；".join(issues[:3])}
    return {"status": "pass", "detail": "交互元素均在script之前"}

@register("结构检查", "stray闭合标签检测", ["structure"])
def check_stray_closing_tags(content, lines, file_path):
    """Detect stray closing tags without matching opening tags (C910 v0.12 bug pattern)."""
    issues = []
    for tag in ['code', 'article', 'div', 'section', 'figure']:
        o, c = count_tag(content, tag)
        if c > o:
            issues.append(f"</{tag}> 多出 {c-o} 个（stray标签）")
    if issues:
        return {"status": "fail", "detail": "；".join(issues)}
    return {"status": "pass", "detail": "无stray闭合标签"}

@register("结构检查", "双层code标签嵌套", ["structure"])
def check_double_nested_code(content, lines, file_path):
    """Bug C910 v0.09: double-nested <code> tags in table rows."""
    pattern = r'<code[^>]*>\s*<code'
    matches = re.findall(pattern, content)
    if matches:
        return {"status": "fail", "detail": f"发现{len(matches)}处双层code嵌套"}
    return {"status": "pass", "detail": "0处"}

# ============================================================================
# 2. CSS CHECKS (14 checks)
# ============================================================================

@register("CSS检查", "模态窗口背景透明", ["css", "diagram"])
def check_modal_transparency(content, lines, file_path):
    """Rule 1.1: Modal background must be transparent, no colored overlay."""
    modal_patterns = [
        r'#diagram-modal\s*\{[^}]*background:\s*rgba\(\s*0\s*,\s*0\s*,\s*0',
        r'#diagram-modal\s*\{[^}]*background:\s*black',
        r'#diagram-modal\s*\{[^}]*background:\s*#\s*0{3,6}',
        r'\.modal-overlay\s*\{[^}]*background:\s*rgba\(\s*0\s*,',
    ]
    for pattern in modal_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return {"status": "fail", "detail": "模态窗口使用有色遮罩（违反规则1.1）"}
    # Check for transparent
    if 'transparent' in content and ('diagram-modal' in content or 'modal' in content.lower()):
        return {"status": "pass", "detail": "transparent"}
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    return {"status": "warning", "detail": "未检测到transparent声明"}

@register("CSS检查", "模态窗口无尺寸限制", ["css", "diagram"])
def check_modal_no_size_constraint(content, lines, file_path):
    """Rule 1.2: modal-content/modal-body must not have max-width/max-height."""
    if 'diagram-modal' not in content and 'modal-content' not in content:
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    issues = []
    for selector in ['modal-content', 'modal-body', 'img-wrapper']:
        pattern = rf'\.{selector}\s*\{{[^}}]*max-(width|height)'
        m = re.search(pattern, content, re.DOTALL)
        if m:
            issues.append(f".{selector} 含max-{m.group(1)}")
    if issues:
        return {"status": "fail", "detail": "；".join(issues) + "（违反规则1.2）"}
    return {"status": "pass", "detail": "无尺寸限制"}

@register("CSS检查", "图形区域白色背景", ["css", "diagram"])
def check_svg_area_background(content, lines, file_path):
    """Rule 1.3: SVG area should have white background with padding and border-radius."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    if re.search(r'background:\s*#ffffff', content, re.IGNORECASE) or re.search(r'background:\s*#fff\b', content, re.IGNORECASE):
        return {"status": "pass", "detail": "白色背景存在"}
    return {"status": "warning", "detail": "未检测到SVG区域白色背景（规则1.3）"}

@register("CSS检查", "侧边栏禁止换行", ["css", "nav"])
def check_sidebar_nowrap(content, lines, file_path):
    """Rule 2.2: Sidebar links must have white-space: nowrap."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    if 'white-space' in content and 'nowrap' in content:
        return {"status": "pass", "detail": "nowrap已设置"}
    return {"status": "warning", "detail": "缺少white-space:nowrap（规则2.2）"}

@register("CSS检查", "overflow-x:hidden", ["css"])
def check_overflow_x_hidden(content, lines, file_path):
    """Rule 2.5: html, body must have overflow-x: hidden."""
    if 'overflow-x' in content and 'hidden' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少overflow-x:hidden（规则2.5）"}

@register("CSS检查", "正文margin-left", ["css"])
def check_main_margin_left(content, lines, file_path):
    """Rule 2.5: Main content must have margin-left equal to sidebar width."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    # Check for margin-left in #main or .main-content
    pattern = r'#main\s*\{[^}]*margin-left|\.main-content\s*\{[^}]*margin-left'
    if re.search(pattern, content, re.DOTALL):
        return {"status": "pass", "detail": "margin-left已设置"}
    return {"status": "warning", "detail": "缺少正文margin-left（规则2.5）"}

@register("CSS检查", "table-layout:fixed", ["css"])
def check_table_layout_fixed(content, lines, file_path):
    """Rule 2.5: Tables must have table-layout: fixed."""
    if '<table' not in content:
        return {"status": "pass", "detail": "无表格（不适用）"}
    if 'table-layout' in content and 'fixed' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少table-layout:fixed（规则2.5）"}

@register("CSS检查", "文档底色白色/无色", ["css"])
def check_white_background(content, lines, file_path):
    """Rule 3.3: Document background should be white or transparent."""
    # Check for non-white body background
    m = re.search(r'body\s*\{[^}]*background:\s*(#[0-9a-fA-F]{3,6}|rgb)', content, re.DOTALL)
    if m:
        bg = m.group(1)
        if bg.lower() not in ('#fff', '#ffffff', '#fff;'):
            return {"status": "warning", "detail": f"body背景色={bg}（规则3.3建议白色）"}
    return {"status": "pass", "detail": "白色/无色底色"}

@register("CSS检查", "响应式设计", ["css"])
def check_responsive_design(content, lines, file_path):
    if '@media' in content:
        return {"status": "pass", "detail": "存在@media媒体查询"}
    return {"status": "warning", "detail": "缺少响应式设计"}

# ---------------------------------------------------------------------------
# Responsive cascade-order helpers (catch base-after-media override bug)
# ---------------------------------------------------------------------------
LAYOUT_PROPS = ['margin', 'margin-left', 'margin-right', 'margin-top', 'margin-bottom',
                'padding', 'padding-left', 'padding-right', 'padding-top', 'padding-bottom',
                'width', 'max-width', 'min-width', 'height', 'max-height', 'min-height',
                'display', 'position', 'float', 'flex', 'flex-direction', 'grid',
                'top', 'left', 'right', 'bottom', 'overflow', 'overflow-x', 'overflow-y']

def _extract_css(content):
    """Concatenate CSS from all <style> blocks (offsets are within the result)."""
    parts = re.findall(r'<style\b[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE)
    return "\n".join(parts)

def _extract_media_blocks(css):
    """Return list of (start_offset, end_offset) for each top-level @media block."""
    blocks = []
    idx = 0
    while True:
        m = re.search(r'@media[^{]*\{', css[idx:])
        if not m:
            break
        brace = idx + m.end() - 1          # position of the opening '{'
        depth = 0
        i = brace
        while i < len(css):
            if css[i] == '{':
                depth += 1
            elif css[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blocks.append((brace, i + 1))
        idx = i + 1
    return blocks

@register("CSS检查", "响应式级联顺序(base须在@media之前)", ["css", "responsive"])
def check_responsive_cascade_order(content, lines, file_path):
    """Catch the bug class where a base (desktop) rule is defined AFTER an @media
    override, so at narrow widths the equal-specificity base wins and the media
    query never takes effect (e.g. sidebar folds to bottom but leaves left
    whitespace, body content does not fill width).
    Best practice: base (desktop) styles FIRST, responsive overrides LAST.
    Triggered by the real v0.09 regression in the ADS1263 driver report.
    Flagged as WARNING (not fail) since order only matters when values differ."""
    css = _extract_css(content)
    if not css or '@media' not in css:
        return {"status": "pass", "detail": "无@media或<style>（不适用）"}
    media_blocks = _extract_media_blocks(css)
    if not media_blocks:
        return {"status": "pass", "detail": "无@media块"}
    # Collect every leaf rule block: (selector, prop, value, offset, in_media).
    # The regex matches only leaf blocks (body has no nested braces), so a
    # declaration's selector is unambiguous.
    decls = []
    for blk in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        selector = blk.group(1).strip()
        body = blk.group(2)
        off = blk.start()
        in_media = any(off >= s and off < e for (s, e) in media_blocks)
        for dp in re.finditer(r'\b(' + '|'.join(LAYOUT_PROPS) + r')\s*:\s*([^;{}]+);?', body):
            decls.append((selector, dp.group(1), dp.group(2).strip(), off, in_media))
    issues = []
    for (m_sel, m_prop, m_val, m_off, m_in) in decls:
        if not m_in:
            continue                       # only media-block overrides are the "later" rule
        for (b_sel, b_prop, b_val, b_off, b_in) in decls:
            if b_in or b_sel != m_sel or b_prop != m_prop:
                continue                   # MUST be same selector + same property
            if b_val != m_val and b_off > m_off:
                issues.append(f"选择器 {m_sel}: 属性 {m_prop} 基础值'{b_val}'定义在@media之后"
                              f"(行序靠后)，窄屏下会覆盖媒体查询值'{m_val}'")
                break
    if issues:
        return {"status": "warning", "detail": "；".join(issues[:3])}
    return {"status": "pass", "detail": "响应式级联顺序正确(base先于@media)"}

@register("CSS检查", "CSS变量定义", ["css"])
def check_css_variables(content, lines, file_path):
    if ':root' in content or '--' in content.split('<style>')[1] if '<style>' in content else '':
        return {"status": "pass", "detail": "存在:root变量"}
    return {"status": "warning", "detail": "缺少CSS变量定义"}

@register("CSS检查", "侧边栏滚动高亮样式", ["css", "nav"])
def check_nav_active_style(content, lines, file_path):
    """Check for active/nav-active CSS class for scroll-spy highlighting."""
    patterns = [r'\.active\s*\{', r'\.nav-active\s*\{', r'\.current\s*\{']
    for p in patterns:
        if re.search(p, content):
            return {"status": "pass", "detail": "高亮样式存在"}
    return {"status": "warning", "detail": "缺少目录高亮CSS样式"}

@register("CSS检查", "框图查看器样式", ["css", "diagram"])
def check_diagram_modal_style(content, lines, file_path):
    if 'diagram-modal' in content or 'modal' in content.lower():
        return {"status": "pass", "detail": "框图查看器样式存在"}
    if 'figure' not in content:
        return {"status": "pass", "detail": "无框图（不适用）"}
    return {"status": "warning", "detail": "缺少框图查看器样式"}

@register("CSS检查", "链接悬浮提示样式", ["css"])
def check_tooltip_style(content, lines, file_path):
    if 'link-tooltip' in content or 'tooltip' in content.lower():
        return {"status": "pass", "detail": "悬浮提示样式存在"}
    return {"status": "warning", "detail": "缺少链接悬浮提示样式（规则3.4）"}

@register("CSS检查", "代码块折叠样式", ["css"])
def check_code_block_style(content, lines, file_path):
    if 'details' in content or 'code-block' in content or 'summary' in content:
        return {"status": "pass", "detail": "折叠样式存在"}
    return {"status": "warning", "detail": "缺少代码块折叠样式"}

# ============================================================================
# 3. JAVASCRIPT CHECKS (16 checks)
# ============================================================================

@register("JS检查", "scroll-spy函数完整性", ["js", "nav"])
def check_scrollspy_completeness(content, lines, file_path):
    """Generic scroll-spy completeness check (any naming convention).
    Bug prevention: C910 v0.06 (offsetTop inaccurate), v0.12 (JS missing), v0.21 (JS stripped).
    Downgraded to warnings (not fails) so non-initScrollSpy implementations are not false-flagged."""
    if 'sidebar' not in content.lower() and 'data-spy' not in content:
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    spy = detect_scrollspy(content)
    if not spy['mechanism']:
        return {"status": "warning", "detail": "未检测到 scroll-spy 机制（无 def / scroll监听+高亮 / rect定位）"}
    issues = []
    if spy['has_scroll_listener'] and not spy['has_rect']:
        issues.append("scroll 监听但未用 getBoundingClientRect（v0.06 修复：offsetTop 不准）")
    if spy['has_scroll_listener'] and 'requestAnimationFrame' not in content:
        issues.append("未用 requestAnimationFrame 节流")
    if spy['mechanism'] and not spy['has_def']:
        issues.append("scroll-spy 以非标准函数名实现，请人工确认")
    spy_links = len(re.findall(r'<a[^>]+data-spy', content)) if 'data-spy' in content else 0
    if spy_links == 0 and spy['has_def']:
        issues.append("有 def 但缺 data-spy 锚点（可选）")
    if issues:
        return {"status": "warning", "detail": "；".join(issues)}
    return {"status": "pass", "detail": "scroll-spy 机制完善（generic 检测）"}

@register("JS检查", "折叠JS函数", ["js"])
def check_collapse_js(content, lines, file_path):
    if 'initCollapse' in content or 'toggleCollapse' in content or 'collapsible' in content.lower():
        return {"status": "pass", "detail": "存在"}
    if '<h2' not in content and '<h3' not in content:
        return {"status": "pass", "detail": "无标题（不适用）"}
    return {"status": "warning", "detail": "缺少折叠JS函数（规则3.2）"}

@register("JS检查", "侧边栏切换JS", ["js"])
def check_sidebar_toggle_js(content, lines, file_path):
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    if 'initSidebarToggle' in content or 'toggleSidebar' in content or 'sidebarToggle' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少侧边栏切换JS"}

@register("JS检查", "框图查看器JS函数", ["js", "diagram"])
def check_diagram_viewer_js(content, lines, file_path):
    if 'figure' not in content and 'diagram' not in content.lower():
        return {"status": "pass", "detail": "无框图（不适用）"}
    funcs = ['openDiagramViewer', 'showDiagram', 'diagramZoom', 'diagramReset']
    found = [f for f in funcs if f in content]
    missing = [f for f in funcs if f not in content]
    if len(found) == len(funcs):
        return {"status": "pass", "detail": f"4个函数齐全"}
    if len(found) == 0:
        return {"status": "warning", "detail": "框图查看器JS完全缺失"}
    return {"status": "warning", "detail": f"缺少: {', '.join(missing)}"}

@register("JS检查", "框图查看按钮数量匹配", ["js", "diagram"])
def check_diagram_button_count(content, lines, file_path):
    fig_count = len(re.findall(r'<figure\b', content))
    viewer_calls = len(re.findall(r'openDiagramViewer', content))
    if fig_count == 0:
        return {"status": "pass", "detail": "无框图（不适用）"}
    if abs(fig_count - viewer_calls) <= 1:
        return {"status": "pass", "detail": f"figure {fig_count} / 按钮 {viewer_calls}"}
    return {"status": "warning", "detail": f"figure {fig_count} vs 按钮 {viewer_calls}，不匹配"}

@register("JS检查", "链接悬浮提示JS", ["js"])
def check_link_tooltip_js(content, lines, file_path):
    if 'initLinkTooltip' in content or 'linkTooltip' in content or 'showTooltip' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少链接悬浮提示JS（规则3.4）"}

@register("JS检查", "返回顶部JS", ["js"])
def check_back_to_top_js(content, lines, file_path):
    if 'initBackToTop' in content or 'backToTop' in content or 'back-to-top' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少返回顶部JS"}

@register("JS检查", "DOMContentLoaded事件", ["js"])
def check_dom_ready(content, lines, file_path):
    if 'DOMContentLoaded' in content or "document.readyState" in content or "window.onload" in content:
        return {"status": "pass", "detail": "存在DOM就绪事件"}
    if '<script' not in content:
        return {"status": "pass", "detail": "无脚本（不适用）"}
    return {"status": "warning", "detail": "缺少DOMContentLoaded/readyState检查"}

@register("JS检查", "Mermaid异步渲染处理", ["js", "diagram"])
def check_mermaid_async(content, lines, file_path):
    """Bug GEM5 v0.03: mermaid.run() is async, must await before setting up interactions."""
    if 'mermaid' not in content.lower():
        return {"status": "pass", "detail": "无Mermaid（不适用）"}
    if 'await mermaid.run' in content or 'mermaid.run().then' in content or 'mermaid.initialize' in content:
        return {"status": "pass", "detail": "异步处理存在"}
    if 'mermaid.run' in content and 'await' not in content and '.then' not in content:
        return {"status": "warning", "detail": "mermaid.run()未await（GEM5 v0.03 bug模式）"}
    return {"status": "pass", "detail": "Mermaid初始化方式正常"}

@register("JS检查", "重复按钮检测", ["js", "diagram"])
def check_duplicate_buttons(content, lines, file_path):
    """Bug CHI v0.09: Hardcoded buttons duplicate JS-generated ones (3 buttons instead of 1)."""
    if 'figure' not in content and 'diagram' not in content.lower():
        return {"status": "pass", "detail": "无框图（不适用）"}
    # Check for hardcoded svg-view-btn or view-btn in HTML that would duplicate JS-created ones
    hardcoded = len(re.findall(r'<div[^>]*class="[^"]*(?:svg-view-btn|view-btn|diagram-view-btn)[^"]*"[^>]*>[^<]*查看', content))
    js_created = len(re.findall(r'(?:createElement|innerHTML|insertAdjacentHTML).*?(?:view-btn|查看大图|查看按钮)', content, re.DOTALL))
    if hardcoded > 0 and js_created > 0:
        return {"status": "fail", "detail": f"硬编码按钮{hardcoded}个 + JS动态创建{js_created}个（CHI v0.09 bug模式：重复按钮）"}
    if hardcoded > 10:
        return {"status": "warning", "detail": f"硬编码查看按钮{hardcoded}个，建议JS动态创建"}
    return {"status": "pass", "detail": "无重复按钮"}

@register("JS检查", "scroll-spy重计算(折叠后)", ["js", "nav"])
def check_scrollspy_recalc(content, lines, file_path):
    """Bug GEM5 v0.04: After folding sections, heading positions change but scroll-spy uses stale offsets."""
    spy = detect_scrollspy(content)
    if not spy['mechanism']:
        return {"status": "pass", "detail": "无scroll-spy（不适用）"}
    if 'recalc' in content or 'recalculate' in content or 'calcOffsets' in content or 'updateOffsets' in content:
        return {"status": "pass", "detail": "存在位置重计算逻辑"}
    if spy['has_rect']:
        # getBoundingClientRect is called on each scroll, so it auto-recalculates
        return {"status": "pass", "detail": "使用getBoundingClientRect（实时计算）"}
    return {"status": "warning", "detail": "缺少折叠后位置重计算（GEM5 v0.04 bug模式）"}

@register("JS检查", "DOM空引用防护", ["js"])
def check_null_reference_protection(content, lines, file_path):
    """Check for potential null references: getElementById without null check."""
    if '<script' not in content:
        return {"status": "pass", "detail": "无脚本（不适用）"}
    # Find getElementById calls
    gbi_calls = re.findall(r'getElementById\(["\']([^"\']+)["\']\)', content)
    if not gbi_calls:
        return {"status": "pass", "detail": "无getElementById调用"}
    # Check if there are null checks nearby (rough heuristic)
    has_null_check = 'if (' in content and ('null' in content or '!element' in content or '!== null' in content)
    if not has_null_check and len(gbi_calls) > 3:
        return {"status": "warning", "detail": f"{len(gbi_calls)}个getElementById调用，缺少null检查"}
    return {"status": "pass", "detail": f"{len(gbi_calls)}个调用，有防护"}

@register("JS检查", "事件监听器重复绑定检测", ["js"])
def check_duplicate_event_listeners(content, lines, file_path):
    """Check for potential duplicate event listener bindings."""
    if '<script' not in content:
        return {"status": "pass", "detail": "无脚本（不适用）"}
    scroll_listeners = len(re.findall(r'addEventListener\s*\(\s*["\']scroll["\']', content))
    if scroll_listeners > 1:
        return {"status": "warning", "detail": f"{scroll_listeners}个scroll事件监听器（可能重复绑定）"}
    return {"status": "pass", "detail": f"scroll监听器{scroll_listeners}个"}

@register("JS检查", "代码块默认折叠JS", ["js"])
def check_code_fold_js(content, lines, file_path):
    """Rule 3.1: Code blocks must be collapsed by default."""
    if '<details' not in content and '<pre' not in content and '<code' not in content:
        return {"status": "pass", "detail": "无代码块（不适用）"}
    if '<details' in content:
        open_details = len(re.findall(r'<details\b(?![^>]*open)', content))
        if open_details > 0:
            return {"status": "pass", "detail": f"{open_details}个details默认折叠"}
    return {"status": "warning", "detail": "缺少代码块默认折叠（规则3.1）"}

@register("JS检查", "ESC键关闭模态窗口", ["js", "diagram"])
def check_esc_close_modal(content, lines, file_path):
    """Rule 1.4: Support ESC key to close image viewer."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    if 'Escape' in content or 'keyCode' in content or 'key ===' in content or "'Escape'" in content:
        return {"status": "pass", "detail": "ESC关闭支持"}
    return {"status": "warning", "detail": "缺少ESC键关闭支持（规则1.4）"}

@register("JS检查", "图片缩放/拖拽JS", ["js", "diagram"])
def check_zoom_drag_js(content, lines, file_path):
    """Rule 1.5: Support zoom and drag/pan."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    has_zoom = 'zoom' in content.lower() or 'scale' in content.lower()
    has_drag = 'drag' in content.lower() or 'mousedown' in content or 'mousemove' in content
    has_wheel = 'wheel' in content.lower() or 'onwheel' in content
    features = []
    if has_zoom: features.append("缩放")
    if has_drag: features.append("拖拽")
    if has_wheel: features.append("滚轮")
    if len(features) >= 2:
        return {"status": "pass", "detail": "；".join(features)}
    return {"status": "warning", "detail": f"仅{features}，缺少完整缩放/拖拽支持（规则1.5）"}

# ============================================================================
# 4. NAVIGATION CHECKS (10 checks)
# ============================================================================

@register("导航检查", "侧边栏存在性", ["nav"])
def check_sidebar_presence(content, lines, file_path):
    """Rule 2.1: Must have a sidebar."""
    if 'id="sidebar"' in content or 'class="sidebar"' in content or 'id="toc"' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少侧边栏（规则2.1）"}

@register("导航检查", "内联目录ToC存在性", ["nav"])
def check_toc_presence(content, lines, file_path):
    """Rule 2.1: Must have both sidebar AND inline ToC. Bug GEM5 v0.05: missing ToC."""
    toc_patterns = [r'id="toc"', r'class="toc"', r'目录', r'Table of Contents', r'id="table-of-contents"']
    for p in toc_patterns:
        if re.search(p, content):
            return {"status": "pass", "detail": "存在"}
    # Check for inline nav list in main content
    if re.search(r'<nav\s+class="[^"]*inline', content):
        return {"status": "pass", "detail": "内联nav存在"}
    return {"status": "warning", "detail": "缺少内联目录ToC（规则2.1，GEM5 v0.05 bug模式）"}

@register("导航检查", "侧边栏链接完整性", ["nav"])
def check_sidebar_link_integrity(content, lines, file_path):
    """Check that all sidebar href="#xxx" links point to existing IDs."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    sidebar_match = re.search(r'<(?:div|nav)[^>]*(?:id="sidebar"|class="sidebar")[^>]*>(.*?)</(?:div|nav)>', content, re.DOTALL)
    if not sidebar_match:
        sidebar_text = content
    else:
        sidebar_text = sidebar_match.group(1)
    links = re.findall(r'href="#([^"]+)"', sidebar_text)
    if not links:
        return {"status": "pass", "detail": "无锚点链接"}
    ids = set(extract_id_matches(content))
    broken = [l for l in links if l not in ids]
    if broken:
        return {"status": "fail", "detail": f"断裂链接{len(broken)}个: {broken[:3]}"}
    return {"status": "pass", "detail": f"{len(links)}个链接全部有效"}

@register("导航检查", "内部锚点链接断裂", ["nav"])
def check_internal_link_broken(content, lines, file_path):
    """Check all href="#xxx" links point to existing IDs."""
    links = extract_href_anchors(content)
    if not links:
        return {"status": "pass", "detail": "无内部链接"}
    ids = set(extract_id_matches(content))
    broken = [l for l in links if l not in ids]
    if broken:
        unique_broken = list(set(broken))
        return {"status": "fail", "detail": f"断裂{len(unique_broken)}个: {unique_broken[:3]}"}
    return {"status": "pass", "detail": f"{len(links)}个链接全部有效"}

@register("导航检查", "scroll-spy属性存在", ["nav"])
def check_data_spy_presence(content, lines, file_path):
    spy = detect_scrollspy(content)
    if spy['mechanism'] and 'data-spy' not in content:
        return {"status": "warning", "detail": "有 scroll-spy 机制但无 data-spy 属性（可选）"}
    if 'data-spy' in content:
        return {"status": "pass", "detail": f"{content.count('data-spy')}处"}
    return {"status": "pass", "detail": "无scroll-spy（不适用）"}

@register("导航检查", "侧边栏链接数与标题数匹配", ["nav"])
def check_sidebar_heading_match(content, lines, file_path):
    """Check sidebar link count matches heading count."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    sidebar_match = re.search(r'<(?:div|nav)[^>]*(?:id="sidebar"|class="sidebar")[^>]*>(.*?)</(?:div|nav)>', content, re.DOTALL)
    sidebar_text = sidebar_match.group(1) if sidebar_match else ""
    sidebar_links = len(re.findall(r'href="#[^"]+"', sidebar_text))
    h2_count = len(re.findall(r'<h2[^>]*id=', content))
    h3_count = len(re.findall(r'<h3[^>]*id=', content))
    h4_count = len(re.findall(r'<h4[^>]*id=', content))
    total_headings = h2_count + h3_count + h4_count
    if total_headings == 0:
        return {"status": "pass", "detail": "无带ID标题"}
    diff = abs(sidebar_links - total_headings)
    if diff <= 2:
        return {"status": "pass", "detail": f"链接{sidebar_links} / 标题{total_headings}"}
    return {"status": "warning", "detail": f"链接{sidebar_links} vs 标题{total_headings}，差{diff}"}

@register("导航检查", "返回顶部按钮存在", ["nav"])
def check_back_to_top_presence(content, lines, file_path):
    if 'back-to-top' in content or 'backToTop' in content:
        return {"status": "pass", "detail": "存在"}
    return {"status": "warning", "detail": "缺少返回顶部按钮"}

@register("导航检查", "侧边栏滚动高亮(自动居中)", ["nav", "js"])
def check_sidebar_auto_scroll(content, lines, file_path):
    """Rule 2.3: Active item should auto-scroll to center of sidebar."""
    spy = detect_scrollspy(content)
    if not spy['mechanism']:
        return {"status": "pass", "detail": "无scroll-spy（不适用）"}
    if 'scrollTop' in content and ('sidebar' in content.lower() or 'nav' in content.lower()):
        return {"status": "pass", "detail": "自动滚动存在"}
    return {"status": "warning", "detail": "缺少侧边栏自动滚动居中（规则2.3）"}

@register("导航检查", "重复锚点检测", ["nav"])
def check_duplicate_anchors(content, lines, file_path):
    """Check for duplicate ID attributes."""
    ids = extract_id_matches(content)
    if not ids:
        return {"status": "pass", "detail": "无ID"}
    from collections import Counter
    dupes = [id_val for id_val, count in Counter(ids).items() if count > 1]
    if dupes:
        return {"status": "fail", "detail": f"重复ID: {dupes[:5]}"}
    return {"status": "pass", "detail": f"{len(ids)}个ID唯一"}

@register("导航检查", "侧边栏重复链接检测", ["nav"])
def check_duplicate_sidebar_links(content, lines, file_path):
    """Check for duplicate href links in sidebar."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    sidebar_match = re.search(r'<(?:div|nav)[^>]*(?:id="sidebar"|class="sidebar")[^>]*>(.*?)</(?:div|nav)>', content, re.DOTALL)
    sidebar_text = sidebar_match.group(1) if sidebar_match else ""
    links = re.findall(r'href="#([^"]+)"', sidebar_text)
    if not links:
        return {"status": "pass", "detail": "无链接"}
    from collections import Counter
    dupes = [l for l, c in Counter(links).items() if c > 1]
    if dupes:
        return {"status": "fail", "detail": f"重复链接: {dupes[:5]}"}
    return {"status": "pass", "detail": f"{len(links)}个链接唯一"}

# ============================================================================
# 5. DIAGRAM CHECKS (12 checks)
# ============================================================================

@register("框图检查", "figure.diagram包裹", ["diagram"])
def check_figure_diagram_wrapping(content, lines, file_path):
    """Check that diagrams are wrapped in <figure class="diagram">."""
    if 'mermaid' not in content.lower() and '<svg' not in content:
        return {"status": "pass", "detail": "无框图（不适用）"}
    fig_count = len(re.findall(r'<figure\b', content))
    fig_diagram = len(re.findall(r'<figure[^>]*class="[^"]*diagram', content))
    if fig_count == 0:
        return {"status": "warning", "detail": "有SVG/Mermaid但无figure包裹"}
    if fig_diagram == fig_count:
        return {"status": "pass", "detail": f"{fig_diagram}个figure.diagram"}
    return {"status": "warning", "detail": f"figure {fig_count}个, figure.diagram {fig_diagram}个"}

@register("框图检查", "figcaption存在性", ["diagram"])
def check_figcaption(content, lines, file_path):
    fig_count = len(re.findall(r'<figure\b', content))
    cap_count = len(re.findall(r'<figcaption\b', content))
    if fig_count == 0:
        return {"status": "pass", "detail": "无figure（不适用）"}
    if fig_count == cap_count:
        return {"status": "pass", "detail": f"{cap_count}/{fig_count}"}
    return {"status": "warning", "detail": f"figure {fig_count} vs figcaption {cap_count}"}

@register("框图检查", "框图编号唯一性", ["diagram"])
def check_figure_numbering(content, lines, file_path):
    caps = re.findall(r'<figcaption[^>]*>(.*?)</figcaption>', content, re.DOTALL)
    numbers = []
    for cap in caps:
        m = re.search(r'图\s*(\d+[-.]?\d*)', cap)
        if m:
            numbers.append(m.group(1))
    if not numbers:
        return {"status": "pass", "detail": "无图编号"}
    from collections import Counter
    dupes = [n for n, c in Counter(numbers).items() if c > 1]
    if dupes:
        return {"status": "fail", "detail": f"重复图编号: {dupes}"}
    return {"status": "pass", "detail": f"{len(numbers)}个编号唯一"}

@register("框图检查", "图片查看按钮(zoom in/out)", ["diagram"])
def check_zoom_buttons(content, lines, file_path):
    """Rule 1.5: Provide +/-/reset zoom buttons."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    has_zoom_in = '+' in content and ('zoom' in content.lower() or 'scale' in content.lower())
    has_zoom_out = '-' in content and ('zoom' in content.lower() or 'scale' in content.lower())
    has_reset = 'reset' in content.lower() or '重置' in content
    features = []
    if has_zoom_in: features.append("放大")
    if has_zoom_out: features.append("缩小")
    if has_reset: features.append("重置")
    if len(features) >= 2:
        return {"status": "pass", "detail": "；".join(features)}
    return {"status": "warning", "detail": f"仅{features}（规则1.5）"}

@register("框图检查", "图片左右切换按钮", ["diagram"])
def check_prev_next_buttons(content, lines, file_path):
    """Rule 1.7: Provide prev/next navigation buttons."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    has_prev = 'prev' in content.lower() or '‹' in content or '上一' in content
    has_next = 'next' in content.lower() or '›' in content or '下一' in content
    if has_prev and has_next:
        return {"status": "pass", "detail": "左右切换存在"}
    return {"status": "warning", "detail": "缺少左右切换按钮（规则1.7）"}

@register("框图检查", "关闭按钮存在", ["diagram"])
def check_close_button(content, lines, file_path):
    """Rule 1.4: Provide X close button."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    if '✕' in content or '&times;' in content or 'close' in content.lower() or '关闭' in content:
        return {"status": "pass", "detail": "关闭按钮存在"}
    return {"status": "warning", "detail": "缺少关闭按钮（规则1.4）"}

@register("框图检查", "点击空白关闭", ["diagram"])
def check_click_outside_close(content, lines, file_path):
    """Rule 1.4: Click modal blank area to close."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    if 'target' in content and ('currentTarget' in content or 'e.target' in content or 'event.target' in content):
        return {"status": "pass", "detail": "点击空白关闭逻辑存在"}
    return {"status": "warning", "detail": "缺少点击空白关闭（规则1.4）"}

@register("框图检查", "Mermaid标签兼容性", ["diagram", "known_bugs"])
def check_mermaid_label_compat(content, lines, file_path):
    """Bug C910 v0.04: Mermaid interprets 'N.' prefix as markdown list, causing 'Unsupported markdown: list' error."""
    if 'mermaid' not in content.lower():
        return {"status": "pass", "detail": "无Mermaid（不适用）"}
    # Check for mermaid node labels starting with number+dot (e.g., "1. SAB创建")
    mermaid_blocks = re.findall(r'<div class="mermaid[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
    if not mermaid_blocks:
        mermaid_blocks = re.findall(r'```mermaid\s*(.*?)```', content, re.DOTALL)
    issues = []
    for block in mermaid_blocks:
        # Find node labels like ["1. xxx"] or (1. xxx) or [1. xxx]
        labels = re.findall(r'["\[\(](\d+\.\s+[^"\]\)]+)["\]\)]', block)
        if labels:
            issues.append(f"标签以数字.开头: {labels[:2]}")
    if issues:
        return {"status": "fail", "detail": "；".join(issues[:2]) + "（C910 v0.04 bug模式）"}
    return {"status": "pass", "detail": "无数字.开头标签"}

@register("框图检查", "Mermaid初始化", ["diagram", "js"])
def check_mermaid_init(content, lines, file_path):
    if 'mermaid' not in content.lower():
        return {"status": "pass", "detail": "无Mermaid（不适用）"}
    if 'mermaid.initialize' in content or 'mermaid.init' in content or 'mermaid.run' in content:
        return {"status": "pass", "detail": "初始化存在"}
    return {"status": "warning", "detail": "缺少Mermaid初始化调用"}

@register("框图检查", "框图连线复查标记", ["diagram"])
def check_diagram_line_review(content, lines, file_path):
    """Rule 1.8: Diagram lines/arrows should be reviewed. This is a reminder check."""
    if 'mermaid' not in content.lower() and '<svg' not in content:
        return {"status": "pass", "detail": "无框图（不适用）"}
    # This is a manual review reminder - always pass but note the count
    fig_count = len(re.findall(r'<figure\b', content))
    return {"status": "pass", "detail": f"{fig_count}个框图需人工复查连线（规则1.8）"}

@register("框图检查", "低饱和度底色", ["diagram"])
def check_low_saturation_bg(content, lines, file_path):
    """Rule 1.10: Diagrams with text should use low-saturation background."""
    if 'mermaid' not in content.lower() and '<svg' not in content:
        return {"status": "pass", "detail": "无框图（不适用）"}
    # This is hard to check automatically - just remind
    return {"status": "pass", "detail": "需人工确认低饱和度底色（规则1.10）"}

@register("框图检查", "SVG容器存在性", ["diagram"])
def check_svg_container(content, lines, file_path):
    """Check for SVG container in modal (GEM5 v0.03: SVG display in modal)."""
    if 'diagram-modal' not in content and 'modal' not in content.lower():
        return {"status": "pass", "detail": "无模态窗口（不适用）"}
    if 'svg' in content.lower() or 'svgContainer' in content or 'svg-container' in content or 'modal-svg' in content:
        return {"status": "pass", "detail": "SVG容器存在"}
    return {"status": "warning", "detail": "缺少SVG容器（GEM5 v0.02/v0.03 bug模式）"}

# ============================================================================
# 6. CONTENT CHECKS (8 checks)
# ============================================================================

@register("内容检查", "标题编号格式", ["content"])
def check_heading_numbering(content, lines, file_path):
    """Rule 3.2: All h1/h2/h3 headings should have numbers."""
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL)
    h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL)
    issues = []
    for h in h2s:
        text = re.sub(r'<[^>]+>', '', h).strip()
        if text and not re.match(r'^(第\d+章|\d+[\.\s])', text) and '参考文献' not in text:
            issues.append(f"h2: {text[:20]}")
    if issues:
        return {"status": "warning", "detail": f"{len(issues)}个标题无编号: {issues[:2]}"}
    return {"status": "pass", "detail": "编号格式正确"}

@register("内容检查", "table有caption", ["content", "table"])
def check_table_caption(content, lines, file_path):
    tables = len(re.findall(r'<table\b', content))
    captions = len(re.findall(r'<caption\b', content))
    if tables == 0:
        return {"status": "pass", "detail": "无表格"}
    if tables == captions:
        return {"status": "pass", "detail": f"{captions}/{tables}"}
    return {"status": "warning", "detail": f"table {tables} vs caption {captions}（v0.21 bug模式）"}

@register("内容检查", "表格编号唯一性", ["content", "table"])
def check_table_numbering(content, lines, file_path):
    caps = re.findall(r'<caption[^>]*>(.*?)</caption>', content, re.DOTALL)
    numbers = []
    for cap in caps:
        m = re.search(r'表\s*(\d+[-.]?\d*)', cap)
        if m:
            numbers.append(m.group(1))
    if not numbers:
        return {"status": "pass", "detail": "无表编号"}
    from collections import Counter
    dupes = [n for n, c in Counter(numbers).items() if c > 1]
    if dupes:
        return {"status": "fail", "detail": f"重复表编号: {dupes}（C910 v0.13 bug模式）"}
    return {"status": "pass", "detail": f"{len(numbers)}个编号唯一"}

@register("内容检查", "代码块默认折叠", ["content"])
def check_code_default_collapsed(content, lines, file_path):
    """Rule 3.1: Code blocks must be collapsed by default."""
    details = re.findall(r'<details\b([^>]*)>', content)
    if not details:
        if '<pre' in content or '<code' in content:
            return {"status": "warning", "detail": "有代码块但未使用details折叠（规则3.1）"}
        return {"status": "pass", "detail": "无代码块"}
    open_details = [d for d in details if 'open' in d]
    if open_details:
        return {"status": "warning", "detail": f"{len(open_details)}个details默认展开（规则3.1要求默认折叠）"}
    return {"status": "pass", "detail": f"{len(details)}个details全部默认折叠"}

@register("内容检查", "图引用一致性", ["content", "ref"])
def check_figure_ref_consistency(content, lines, file_path):
    figcaps = re.findall(r'<figcaption[^>]*>(.*?)</figcaption>', content, re.DOTALL)
    fig_numbers = set()
    for cap in figcaps:
        m = re.findall(r'图\s*(\d+[-.]?\d*)', cap)
        fig_numbers.update(m)
    if not fig_numbers:
        return {"status": "pass", "detail": "无图编号"}
    refs = set(re.findall(r'图\s*(\d+[-.]?\d*)', content))
    # Subtract caption numbers from refs to find dangling references
    dangling = refs - fig_numbers
    # But refs in captions are also "references" - need to exclude those
    if dangling:
        return {"status": "warning", "detail": f"引用无对应图: {list(dangling)[:3]}"}
    return {"status": "pass", "detail": "图引用一致"}

@register("内容检查", "表引用一致性", ["content", "ref"])
def check_table_ref_consistency(content, lines, file_path):
    caps = re.findall(r'<caption[^>]*>(.*?)</caption>', content, re.DOTALL)
    tbl_numbers = set()
    for cap in caps:
        m = re.findall(r'表\s*(\d+[-.]?\d*)', cap)
        tbl_numbers.update(m)
    if not tbl_numbers:
        return {"status": "pass", "detail": "无表编号"}
    refs = set(re.findall(r'表\s*(\d+[-.]?\d*)', content))
    dangling = refs - tbl_numbers
    if dangling:
        return {"status": "warning", "detail": f"引用无对应表: {list(dangling)[:3]}"}
    return {"status": "pass", "detail": "表引用一致"}

@register("内容检查", "侧边栏与标题文本一致", ["content", "nav"])
def check_sidebar_heading_text_match(content, lines, file_path):
    """Lenient check: sidebar link text should correspond to heading text.
    Uses _norm_nav_text() to ignore fold arrows (▾/▶), numbering prefixes,
    parentheticals and abbreviations, so design-level divergence
    (e.g. nav '▾ 3.2 折叠' vs heading '折叠本层级内容') is a soft WARNING,
    not a hard FAIL — reduces false positives (v0.09 report case)."""
    if 'sidebar' not in content.lower():
        return {"status": "pass", "detail": "无侧边栏（不适用）"}
    sidebar_match = re.search(r'<(?:div|nav)[^>]*(?:id="sidebar"|class="sidebar")[^>]*>(.*?)</(?:div|nav)>', content, re.DOTALL)
    if not sidebar_match:
        return {"status": "pass", "detail": "无法提取侧边栏"}
    sidebar_links = re.findall(r'<a[^>]+href="#([^"]+)"[^>]*>(.*?)</a>', sidebar_match.group(1), re.DOTALL)
    if not sidebar_links:
        return {"status": "pass", "detail": "无侧边链接"}
    mismatches = []
    for href, text in sidebar_links[:20]:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        h_match = re.search(rf'<h[23][^>]*id="{href}"[^>]*>(.*?)</h', content, re.DOTALL)
        if h_match:
            h_text = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
            lt = _norm_nav_text(clean_text)
            ht = _norm_nav_text(h_text)
            if not lt or not ht:
                continue
            # Lenient: pass if normalized equal, one contains the other,
            # or first 6 significant chars match (handles abbreviation).
            if lt == ht or lt in ht or ht in lt or lt[:6] == ht[:6]:
                continue
            mismatches.append(f"#{href}: 导航'{clean_text[:15]}' vs 标题'{h_text[:15]}'")
    if mismatches:
        return {"status": "warning", "detail": f"{len(mismatches)}处文本差异(柔和告警): {mismatches[:2]}"}
    return {"status": "pass", "detail": "文本基本一致"}

@register("内容检查", "特殊字符转义", ["content", "chars"])
def check_special_chars(content, lines, file_path):
    """Check for unescaped & characters."""
    bad_lines = []
    for i, line in enumerate(lines):
        if re.search(r'&(?![a-zA-Z#])', line) and '<pre' not in line and '<code' not in line and '<script' not in line and '<!--' not in line:
            bad_lines.append(i + 1)
    if len(bad_lines) > 5:
        return {"status": "warning", "detail": f"{len(bad_lines)}行含未转义&"}
    if bad_lines:
        return {"status": "warning", "detail": f"行 {bad_lines[:5]}"}
    return {"status": "pass", "detail": "0行"}

# ============================================================================
# 7. VERSION CHECKS (6 checks)
# ============================================================================

@register("版本检查", "版本号一致性", ["version"])
def check_version_consistency(content, lines, file_path):
    """Check that version numbers are consistent across the document."""
    # Only consider v0.xx format as document versions (rule: version starts from 0.01)
    # This filters out RTL/signal version numbers like v4.127, v4.139, etc.
    versions = re.findall(r'(?<![a-zA-Z])(v0\.\d+)', content)
    doc_versions = [v for v in versions]
    if not doc_versions:
        return {"status": "warning", "detail": "未找到文档版本号（v0.xx格式）"}
    from collections import Counter
    counts = Counter(doc_versions)
    if len(counts) == 1:
        return {"status": "pass", "detail": f"统一为{list(counts.keys())[0]}（{counts[list(counts.keys())[0]]}处）"}
    multi = {v: c for v, c in counts.items() if c > 1}
    if multi:
        return {"status": "fail", "detail": f"多版本高频: {dict(multi)}（C910 v0.05/v0.21 bug模式）"}
    return {"status": "warning", "detail": f"主版本{list(counts.keys())[0]}，残留: {list(counts.keys())[1:]}"}

@register("版本检查", "版本号格式", ["version"])
def check_version_format(content, lines, file_path):
    """Version must start from 0.01 and follow x.xx format."""
    versions = re.findall(r'(?:版本|version|HTML版本)[:\s]*(v?\d+\.\d+)', content, re.IGNORECASE)
    if not versions:
        return {"status": "warning", "detail": "未找到版本号"}
    for v in versions:
        v_clean = v.lstrip('v')
        parts = v_clean.split('.')
        if len(parts) == 2:
            major, minor = int(parts[0]), int(parts[1])
            if major == 0 and minor < 1:
                return {"status": "warning", "detail": f"版本{v}低于0.01"}
    return {"status": "pass", "detail": f"格式正确: {versions[0]}"}

@register("版本检查", "文件名版本匹配", ["version", "file"])
def check_filename_version_match(content, lines, file_path):
    """Check filename version matches document version."""
    fname = os.path.basename(file_path)
    m = re.search(r'[_-]v(\d+\.\d+)', fname)
    if not m:
        return {"status": "pass", "detail": "文件名无版本号"}
    file_ver = 'v' + m.group(1)
    doc_versions = re.findall(r'(?:版本|version|HTML版本)[:\s]*(v?\d+\.\d+)', content, re.IGNORECASE)
    if not doc_versions:
        return {"status": "warning", "detail": "文档内无版本号"}
    doc_ver = doc_versions[0].lstrip('v')
    if not doc_ver.startswith('v'):
        doc_ver = 'v' + doc_ver
    if file_ver == doc_ver:
        return {"status": "pass", "detail": f"文件名{file_ver} = 文档{doc_ver}"}
    return {"status": "fail", "detail": f"文件名{file_ver} ≠ 文档{doc_ver}"}

@register("版本检查", "版本号位置完整", ["version"])
def check_version_locations(content, lines, file_path):
    """Check version appears in expected locations: comment header, sidebar, document head."""
    version_locs = {
        "注释头": bool(re.search(r'<!--.*?v\d+\.\d+.*?-->', content[:500], re.DOTALL)),
        "侧边栏/文档头": bool(re.search(r'(?:sidebar|version|版本)[^<]*v\d+\.\d+', content, re.IGNORECASE)),
        "title标签": bool(re.search(r'<title>[^<]*v\d+\.\d+', content, re.IGNORECASE)),
    }
    found = sum(version_locs.values())
    if found >= 2:
        return {"status": "pass", "detail": f"{found}/3处: {', '.join(k for k,v in version_locs.items() if v)}"}
    return {"status": "warning", "detail": f"仅{found}/3处: {dict(version_locs)}"}

@register("版本检查", "文件损坏检测", ["version"])
def check_file_corruption(content, lines, file_path):
    """Detect file corruption: version mixing, missing content, truncation.
    Bug C910 v0.21: version mixing v0.15/v0.20/v0.22, missing chapters."""
    # Only consider v0.xx format as document versions
    versions = re.findall(r'(?<![a-zA-Z])(v0\.\d+)', content)
    doc_versions = [v for v in versions]
    from collections import Counter
    counts = Counter(doc_versions)
    multi = {v: c for v, c in counts.items() if c > 1}
    if len(multi) >= 2:
        return {"status": "fail", "detail": f"版本混用: {dict(multi)}（v0.21损坏模式）"}
    # Check for truncation (file ends without </html>)
    if not content.rstrip().endswith('</html>') and not content.rstrip().endswith('</body>'):
        return {"status": "fail", "detail": "文件可能被截断（无</html>结尾）"}
    return {"status": "pass", "detail": "无损坏迹象"}

@register("版本检查", "备份文件检测", ["version", "file"])
def check_backup_files(content, lines, file_path):
    """Detect backup files that may indicate past corruption."""
    dir_path = os.path.dirname(file_path)
    if not os.path.isdir(dir_path):
        return {"status": "pass", "detail": "无法检查目录"}
    backups = []
    for f in os.listdir(dir_path):
        if f.endswith('.bak') or f.endswith('.corrupt.bak') or '.v0' in f and f.endswith('.bak'):
            backups.append(f)
    if backups:
        corrupt = [b for b in backups if 'corrupt' in b]
        if corrupt:
            return {"status": "fail", "detail": f"发现损坏备份: {corrupt}（v0.21事故痕迹）"}
        return {"status": "warning", "detail": f"发现备份文件: {backups[:3]}"}
    return {"status": "pass", "detail": "无备份文件"}

# ============================================================================
# 8. KNOWN BUG PATTERN CHECKS (8 checks)
# ============================================================================

@register("已知Bug模式", "JS块完整性(script数量)", ["known_bugs"])
def check_js_block_completeness(content, lines, file_path):
    """Bug C910 v0.12/v0.21: Entire JS block stripped during rebuild.
    Check: script count >= 2 (external lib + inline JS) for interactive docs."""
    scripts = len(re.findall(r'<script\b', content))
    if scripts == 0:
        if '<h2' in content or '<h3' in content:
            return {"status": "warning", "detail": "有标题但无script（可能JS被剥离）"}
        return {"status": "pass", "detail": "无script（静态文档）"}
    if scripts == 1:
        # Check if the only script is external (no inline JS)
        script_content = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        has_inline = any(s.strip() for s in script_content)
        if not has_inline and ('sidebar' in content.lower() or 'initScrollSpy' in content):
            return {"status": "fail", "detail": "仅1个外部script，内联JS缺失（v0.12/v0.21 bug模式）"}
    return {"status": "pass", "detail": f"{scripts}个script标签"}

@register("已知Bug模式", "章节默认展开检测", ["known_bugs"])
def check_no_default_collapsed(content, lines, file_path):
    """Bug C910 v0.12: Chapter incorrectly collapsed by default (class="collapsed" + max-height:0)."""
    issues = []
    # Check for collapsed class on headings
    collapsed_h2 = len(re.findall(r'<h2[^>]*class="[^"]*collapsed', content))
    if collapsed_h2:
        issues.append(f"{collapsed_h2}个h2有collapsed类")
    # Check for max-height: 0px in section content
    max_height_zero = len(re.findall(r'max-height:\s*0px', content))
    if max_height_zero:
        issues.append(f"{max_height_zero}处max-height:0px")
    if issues:
        return {"status": "warning", "detail": "；".join(issues) + "（v0.12 bug模式）"}
    return {"status": "pass", "detail": "无默认折叠章节"}

@register("已知Bug模式", "Mermaid渲染兼容性", ["known_bugs", "diagram"])
def check_mermaid_render_compat(content, lines, file_path):
    """Bug C910 v0.04: Mermaid 'Unsupported markdown: list' error.
    Bug GEM5 v0.03: Mermaid async timing issue."""
    if 'mermaid' not in content.lower():
        return {"status": "pass", "detail": "无Mermaid（不适用）"}
    issues = []
    # Check for numbered list patterns in mermaid labels
    mermaid_blocks = re.findall(r'(?:class="mermaid[^"]*"[^>]*>|```mermaid\s*)(.*?)(?:</div>|```)', content, re.DOTALL)
    for block in mermaid_blocks:
        labels = re.findall(r'["\[\(](\d+\.\s+[^"\]\)]+)["\]\)]', block)
        if labels:
            issues.append(f"数字.开头标签: {labels[:2]}")
    if issues:
        return {"status": "fail", "detail": "；".join(issues[:2]) + "（v0.04 bug模式）"}
    return {"status": "pass", "detail": "无兼容性问题"}

@register("已知Bug模式", "表编号跳跃检测", ["known_bugs", "content"])
def check_table_numbering_gaps(content, lines, file_path):
    """Bug C910 v0.13: Table numbering jumps (表30-32 instead of 表2-1~2-3)."""
    caps = re.findall(r'<caption[^>]*>(.*?)</caption>', content, re.DOTALL)
    numbers = []
    for cap in caps:
        m = re.search(r'表\s*(\d+)', cap)
        if m:
            numbers.append(int(m.group(1)))
    if len(numbers) < 3:
        return {"status": "pass", "detail": "表格数量不足"}
    # Check for large gaps
    numbers.sort()
    for i in range(1, len(numbers)):
        if numbers[i] - numbers[i-1] > 10:
            return {"status": "warning", "detail": f"表编号跳跃: {numbers[i-1]}→{numbers[i]}（v0.13 bug模式）"}
    return {"status": "pass", "detail": "编号连续"}

@register("已知Bug模式", "图编号跳跃检测", ["known_bugs", "content"])
def check_figure_numbering_gaps(content, lines, file_path):
    """Bug C910 v0.13: Figure numbering jumps."""
    caps = re.findall(r'<figcaption[^>]*>(.*?)</figcaption>', content, re.DOTALL)
    numbers = []
    for cap in caps:
        m = re.search(r'图\s*(\d+)', cap)
        if m:
            numbers.append(int(m.group(1)))
    if len(numbers) < 3:
        return {"status": "pass", "detail": "框图数量不足"}
    numbers.sort()
    for i in range(1, len(numbers)):
        if numbers[i] - numbers[i-1] > 5:
            return {"status": "warning", "detail": f"图编号跳跃: {numbers[i-1]}→{numbers[i]}"}
    return {"status": "pass", "detail": "编号连续"}

@register("已知Bug模式", "游离div序列检测", ["known_bugs", "structure"])
def check_stray_div_sequence(content, lines, file_path):
    """Bug C910 v0.21: Stray div sequence at chapter boundaries."""
    # Look for patterns like </p><div><div></div> (orphan div sequences)
    pattern = r'</p>\s*<div>\s*<div>\s*</div>\s*</div>'
    matches = re.findall(pattern, content)
    if matches:
        return {"status": "warning", "detail": f"发现{len(matches)}处游离div序列（v0.21 bug模式）"}
    return {"status": "pass", "detail": "无游离div序列"}

@register("已知Bug模式", "版本号混用检测", ["known_bugs", "version"])
def check_version_mixing(content, lines, file_path):
    """Bug C910 v0.21: Version mixing (v0.15/v0.20/v0.22 in same file)."""
    # Look specifically in version-marking contexts, only v0.xx format
    version_contexts = re.findall(r'(?:HTML版本|版本[:\s]*|version[:\s]*)(v?0\.\d+)', content, re.IGNORECASE)
    doc_versions = [v if v.startswith('v') else 'v' + v for v in version_contexts]
    if not doc_versions:
        return {"status": "pass", "detail": "无版本标记"}
    from collections import Counter
    counts = Counter(doc_versions)
    if len(counts) > 1:
        return {"status": "fail", "detail": f"版本混用: {dict(counts)}（v0.21 bug模式）"}
    return {"status": "pass", "detail": f"统一为{list(counts.keys())[0]}"}

@register("已知Bug模式", "硬编码重复按钮检测", ["known_bugs", "diagram"])
def check_hardcoded_duplicate_buttons(content, lines, file_path):
    """Bug CHI v0.09: 56 hardcoded view buttons duplicating JS-generated ones."""
    hardcoded = re.findall(r'<div[^>]*class="[^"]*(?:svg-view-btn|view-btn|diagram-view-btn)[^"]*"[^>]*>', content)
    if len(hardcoded) > 5:
        # Check if JS also creates buttons
        js_creates = bool(re.search(r'(?:createElement|innerHTML|insertAdjacentHTML|appendChild).*?(?:view-btn|查看)', content, re.DOTALL))
        if js_creates:
            return {"status": "fail", "detail": f"硬编码{len(hardcoded)}个按钮+JS动态创建（CHI v0.09 bug模式）"}
        return {"status": "warning", "detail": f"硬编码{len(hardcoded)}个查看按钮，建议改用JS动态创建"}
    return {"status": "pass", "detail": f"{len(hardcoded)}个硬编码按钮"}

# ============================================================================
# Test Runner
# ============================================================================

class TestItem:
    def __init__(self, category, name, status, detail, tags=None):
        self.category = category
        self.name = name
        self.status = status
        self.detail = detail
        self.tags = tags or []

class TestRunner:
    def __init__(self):
        self.registry = _TEST_REGISTRY

    def run_single(self, file_path, tag_filter=None):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            lines = content.split('\n')
        except Exception as e:
            return file_path, [], str(e)

        results = []
        for func, category, name, tags, desc in self.registry:
            if tag_filter:
                if not any(t in tags for t in tag_filter):
                    continue
            try:
                ret = func(content, lines, file_path)
                if ret is None:
                    item = TestItem(category, name, "pass", "OK", tags)
                elif isinstance(ret, dict):
                    item = TestItem(category, name, ret.get("status", "pass"), ret.get("detail", ""), tags)
                elif isinstance(ret, TestItem):
                    item = ret
                else:
                    item = TestItem(category, name, "error", str(ret), tags)
            except Exception as e:
                item = TestItem(category, name, "error", str(e)[:100], tags)
            results.append(item)
        return file_path, results, None

    def run_batch(self, directory, tag_filter=None, workers=4):
        exclude_dirs = {'reports', '__pycache__', '.git', 'node_modules', '.history', '_shared'}
        html_files = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith('.html') or f.endswith('.htm'):
                    html_files.append(os.path.join(root, f))
        html_files.sort(key=lambda x: os.path.getsize(x), reverse=True)

        all_results = {}
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.run_single, fp, tag_filter): fp for fp in html_files}
            for future in as_completed(futures):
                fp = futures[future]
                try:
                    file_path, results, error = future.result()
                    all_results[file_path] = (results, error)
                except Exception as e:
                    all_results[fp] = ([], str(e))
        return all_results

# ============================================================================
# Report Generator
# ============================================================================

class ReportGenerator:
    def __init__(self, all_results):
        self.results = all_results

    def gen_summary(self):
        total_files = len(self.results)
        total_pass = total_fail = total_warn = total_err = 0
        cat_fail = defaultdict(int)
        cat_warn = defaultdict(int)
        for file_path, (results, error) in self.results.items():
            for item in results:
                if item.status == "pass": total_pass += 1
                elif item.status == "fail":
                    total_fail += 1
                    cat_fail[item.category] += 1
                elif item.status == "warning":
                    total_warn += 1
                    cat_warn[item.category] += 1
                elif item.status == "error": total_err += 1
        total = total_pass + total_fail + total_warn + total_err
        pass_rate = (total_pass / total * 100) if total > 0 else 0
        return {
            "total_files": total_files, "total_pass": total_pass, "total_fail": total_fail,
            "total_warn": total_warn, "total_err": total_err, "pass_rate": pass_rate,
            "cat_fail": dict(cat_fail), "cat_warn": dict(cat_warn)
        }

    def to_html(self, output_path):
        s = self.gen_summary()
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HTML Frontend Check Report - {ts}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f6f8fa; color:#1a1a1a; padding:20px; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; padding:24px; border-radius:8px; margin-bottom:20px; }}
.header h1 {{ font-size:20px; margin-bottom:8px; }}
.header .meta {{ font-size:13px; opacity:0.9; }}
.cards {{ display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }}
.card {{ background:#fff; padding:16px; border-radius:8px; flex:1; min-width:120px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
.card .num {{ font-size:28px; font-weight:700; }}
.card .label {{ font-size:12px; color:#6b7280; margin-top:4px; }}
.card.pass .num {{ color:#10b981; }}
.card.fail .num {{ color:#ef4444; }}
.card.warn .num {{ color:#f59e0b; }}
.card.files .num {{ color:#3b82f6; }}
.card.rate .num {{ color:{'#10b981' if s['pass_rate']>=90 else '#f59e0b' if s['pass_rate']>=70 else '#ef4444'}; }}
.tag-cloud {{ margin-bottom:20px; }}
.tag-cloud h3 {{ font-size:14px; margin-bottom:8px; }}
.tag {{ display:inline-block; padding:4px 10px; border-radius:12px; font-size:12px; margin:2px; }}
.tag.fail {{ background:#fee2e2; color:#dc2626; }}
.tag.warn {{ background:#fef3c7; color:#d97706; }}
.file-panel {{ background:#fff; border-radius:8px; margin-bottom:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.1); }}
.file-header {{ padding:12px 16px; cursor:pointer; display:flex; align-items:center; gap:8px; border-bottom:1px solid #e5e7eb; }}
.file-header:hover {{ background:#f9fafb; }}
.file-header .icon {{ font-size:16px; }}
.file-header .name {{ font-weight:600; font-size:14px; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.file-header .rate {{ font-size:12px; padding:2px 8px; border-radius:10px; }}
.rate.green {{ background:#d1fae5; color:#065f46; }}
.rate.orange {{ background:#fef3c7; color:#92400e; }}
.rate.red {{ background:#fee2e2; color:#991b1b; }}
.file-body {{ display:none; padding:0; }}
.file-body.open {{ display:block; }}
.check-row {{ display:flex; padding:8px 16px; border-bottom:1px solid #f3f4f6; font-size:13px; }}
.check-row .cat {{ width:80px; color:#6b7280; flex-shrink:0; }}
.check-row .name {{ width:200px; font-weight:500; flex-shrink:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.check-row .status {{ width:60px; flex-shrink:0; }}
.check-row .detail {{ flex:1; color:#4b5563; }}
.status-pass {{ color:#10b981; }} .status-fail {{ color:#ef4444; font-weight:600; }}
.status-warning {{ color:#f59e0b; }} .status-error {{ color:#7c3aed; font-weight:600; }}
</style>
</head>
<body>
<div class="header">
<h1>HTML Frontend Check Report</h1>
<div class="meta">{ts} | {s['total_files']} files | {s['total_pass']+s['total_fail']+s['total_warn']+s['total_err']} checks | Pass Rate: {s['pass_rate']:.1f}%</div>
</div>
<div class="cards">
<div class="card pass"><div class="num">{s['total_pass']}</div><div class="label">PASS</div></div>
<div class="card fail"><div class="num">{s['total_fail']}</div><div class="label">FAIL</div></div>
<div class="card warn"><div class="num">{s['total_warn']}</div><div class="label">WARNING</div></div>
<div class="card files"><div class="num">{s['total_files']}</div><div class="label">FILES</div></div>
<div class="card rate"><div class="num">{s['pass_rate']:.0f}%</div><div class="label">PASS RATE</div></div>
</div>
"""]

        # Tag cloud
        if s['cat_fail'] or s['cat_warn']:
            html_parts.append('<div class="tag-cloud"><h3>Failure/Warning Distribution</h3>')
            for cat, cnt in sorted(s['cat_fail'].items(), key=lambda x: -x[1]):
                html_parts.append(f'<span class="tag fail">{cat}: {cnt} fail</span>')
            for cat, cnt in sorted(s['cat_warn'].items(), key=lambda x: -x[1]):
                html_parts.append(f'<span class="tag warn">{cat}: {cnt} warn</span>')
            html_parts.append('</div>')

        # File panels
        file_rates = []
        for fp, (results, error) in self.results.items():
            fp_pass = sum(1 for r in results if r.status == "pass")
            fp_total = len(results)
            fp_rate = (fp_pass / fp_total * 100) if fp_total > 0 else 0
            file_rates.append((fp, results, error, fp_rate, fp_pass, fp_total))

        file_rates.sort(key=lambda x: x[3])  # Sort by pass rate ascending

        for fp, results, error, rate, passed, total in file_rates:
            fname = os.path.basename(fp)
            rate_class = "green" if rate >= 90 else "orange" if rate >= 70 else "red"
            html_parts.append(f'<div class="file-panel">')
            html_parts.append(f'<div class="file-header" onclick="tf(this)">')
            html_parts.append(f'<span class="icon">{"⚠" if rate < 90 else "✓"}</span>')
            html_parts.append(f'<span class="name" title="{fp}">{fname}</span>')
            html_parts.append(f'<span class="rate {rate_class}">{rate:.0f}% ({passed}/{total})</span>')
            html_parts.append(f'</div><div class="file-body">')

            if error:
                html_parts.append(f'<div class="check-row"><span class="cat">ERROR</span><span class="name">读取错误</span><span class="status status-error">ERROR</span><span class="detail">{error}</span></div>')
            else:
                for item in results:
                    status_class = f"status-{item.status}"
                    icon = {"pass": "✓", "fail": "✗", "warning": "⚠", "error": "！"}.get(item.status, "?")
                    html_parts.append(f'<div class="check-row"><span class="cat">{item.category}</span><span class="name" title="{item.name}">{item.name}</span><span class="status {status_class}">{icon}</span><span class="detail">{html_module.escape(item.detail)}</span></div>')
            html_parts.append('</div></div>')

        html_parts.append("""
<script>
function tf(el) {
    var body = el.nextElementSibling;
    body.classList.toggle('open');
}
</script>
</body>
</html>""")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))

    def to_text(self):
        lines = []
        s = self.gen_summary()
        lines.append(f"=== HTML Frontend Check Summary ===")
        lines.append(f"Files: {s['total_files']} | Pass: {s['total_pass']} | Fail: {s['total_fail']} | Warning: {s['total_warn']} | Error: {s['total_err']}")
        lines.append(f"Pass Rate: {s['pass_rate']:.1f}%")
        lines.append("")
        for fp, (results, error) in self.results.items():
            issues = [r for r in results if r.status in ("fail", "warning", "error")]
            if issues or error:
                lines.append(f"--- {os.path.basename(fp)} ---")
                if error:
                    lines.append(f"  ERROR: {error}")
                for item in issues:
                    lines.append(f"  [{item.status.upper()}] {item.name}: {item.detail}")
                lines.append("")
        return '\n'.join(lines)

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="HTML Frontend Checker v0.01")
    parser.add_argument('--file', '-f', help='Check a single file')
    parser.add_argument('--dir', '-d', default='/workspace/NOTE', help='Directory to scan (default: /workspace/NOTE)')
    parser.add_argument('--tags', '-t', help='Filter by tags (comma-separated)')
    parser.add_argument('--list', '-l', action='store_true', help='List all registered checks')
    parser.add_argument('--workers', '-w', type=int, default=4, help='Parallel workers')
    parser.add_argument('--output', '-o', help='Report output path')
    args = parser.parse_args()

    if args.list:
        print(f"{'Category':<12} {'Name':<30} {'Tags'}")
        print("-" * 70)
        for func, cat, name, tags, desc in _TEST_REGISTRY:
            print(f"{cat:<12} {name:<30} {','.join(tags)}")
        print(f"\nTotal: {len(_TEST_REGISTRY)} checks")
        return

    tag_filter = args.tags.split(',') if args.tags else None
    runner = TestRunner()

    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: {args.file} not found")
            sys.exit(1)
        file_path, results, error = runner.run_single(args.file, tag_filter)
        all_results = {file_path: (results, error)}
    else:
        all_results = runner.run_batch(args.dir, tag_filter, args.workers)

    # Generate report
    output_path = args.output or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               'report_' + time.strftime('%Y%m%d_%H%M%S') + '.html')
    rg = ReportGenerator(all_results)
    rg.to_html(output_path)

    # Also print text summary
    print(rg.to_text())
    print(f"\nHTML report: {output_path}")

if __name__ == '__main__':
    main()
