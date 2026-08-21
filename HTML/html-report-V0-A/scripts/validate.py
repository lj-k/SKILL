#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py —— 交付前HTML报告校验（规则 4.1–4.5 + 版本号一致性）。

检查项：
  4.1 每个章节 <div> 开闭严格配对（grep 等价：open==close）
  4.2 截断行检测：grep -P '</\\w+\\s*$' 应为 0 行
  4.3 标签平衡：用 HTMLParser 栈式解析，检测未闭合/错配标签
  4.4 重复 id 检测：所有 id 全局唯一（含 figure id 必须带章节前缀）
  4.5 目录完整性：#main 内每个标题都有 id（无 id 则由 toc.js 自动补，告警即可）
  +   版本号一致性：config.js 的 REPORT_VERSION 与 CHANGELOG.md / DEV_DOC.md 版本一致

用法：
  python3 validate.py <report.html 或 报告目录>
  python3 validate.py ./REPORTS/foo/my-report
退出码：全部通过为 0，否则非 0（便于 CI/脚本串联）。
"""
import os, re, sys, glob
from html.parser import HTMLParser

VOID = {"meta","link","br","hr","img","input","source","area","base","col","embed","param","track","wbr"}

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag in VOID: return
        self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        pass  # 自闭合
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.stack:
            self.errors.append("多余闭合 </%s>" % tag); return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            # 尝试回溯匹配
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.errors.append("未闭合 <%s>（遇 </%s>）" % (self.stack[-1], tag))
                    self.stack.pop()
                if self.stack: self.stack.pop()
            else:
                self.errors.append("无匹配开标签 </%s>" % tag)

def find_html(target):
    if os.path.isdir(target):
        hs = glob.glob(os.path.join(target, "*.html"))
        return hs[0] if hs else None
    return target if target.endswith(".html") else None

def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate.py <report.html | 报告目录>"); sys.exit(1)
    html_path = find_html(sys.argv[1])
    if not html_path or not os.path.isfile(html_path):
        print("未找到 HTML 文件:", sys.argv[1]); sys.exit(1)

    ok = True
    with open(html_path, "r", encoding="utf-8") as f:
        s = f.read()

    # 4.1 div 配对
    d_open = len(re.findall(r'<div\b', s)); d_close = s.count('</div>')
    print("[4.1] <div> 开=%d 闭=%d" % (d_open, d_close), "PASS" if d_open == d_close else "FAIL")
    if d_open != d_close: ok = False

    # 4.2 截断行
    trunc = re.findall(r'</\w+\s*$', s, re.M)
    print("[4.2] 截断行(应为0):", len(trunc), "PASS" if len(trunc) == 0 else "FAIL")
    if trunc: ok = False

    # 4.3 标签平衡
    chk = TagChecker(); chk.feed(s)
    if chk.stack:
        for t in chk.stack: chk.errors.append("文件结束仍未闭合 <%s>" % t)
    print("[4.3] 标签平衡:", "PASS" if not chk.errors else "FAIL (%d 处)" % len(chk.errors))
    for e in chk.errors[:20]: print("      -", e)
    if chk.errors: ok = False

    # 4.4 重复 id（含 figure id 前缀检查）
    ids = re.findall(r'\bid="([^"]+)"', s)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    print("[4.4] 重复 id:", dup if dup else "无", "PASS" if not dup else "FAIL")
    if dup: ok = False
    fig_ids = re.findall(r'<figure\b[^>]*\bid="([^"]+)"', s)
    bad_prefix = [f for f in fig_ids if not re.match(r'fig-[\d]+-', f)]
    print("[4.4] figure id 带章节前缀(fig-N-):", "全部符合" if not bad_prefix else ("不符合: " + str(bad_prefix)))
    if bad_prefix: ok = False

    # 4.5 目录完整性：#main 内标题应有 id
    m = re.search(r'<main id="main">(.*?)</main>', s, re.S)
    main_block = m.group(1) if m else s
    heads = re.findall(r'<(h[1-6])\b', main_block)
    heads_with_id = re.findall(r'<h[1-6]\b[^>]*\bid=', main_block)
    miss = len(heads) - len(heads_with_id)
    print("[4.5] #main 标题总数=%d, 含 id=%d, 缺 id=%d" % (len(heads), len(heads_with_id), miss),
          "PASS" if miss == 0 else "WARN(将自动补 id)")
    # 标题编号层级检查（h1 应存在且唯一为章）
    h1 = len(re.findall(r'<h1\b', main_block))
    if h1 < 1: print("      - 警告: 未发现 h1 章节标题")

    # 4.6 跨文件契约：模态 SVG 源查找须兼容 diagrams.js 注入位置（.mermaid-wrap > svg）
    # 防止回归到仅查 `.mermaid svg`（与原 modal-image-viewer-skill 约定一致，但本 skill 的 diagrams.js 注入在 .mermaid-wrap）
    base = os.path.dirname(html_path)
    mjs = os.path.join(base, "_shared", "js", "modal.js")
    djs = os.path.join(base, "_shared", "js", "diagrams.js")
    if os.path.isfile(mjs):
        mtxt = open(mjs, encoding="utf-8").read()
        has_fallback = ('.mermaid-wrap' in mtxt) or ('mermaid svg' in mtxt)
        print("[4.6] modal.js SVG 源兜底选择器(应含 .mermaid-wrap 或 .mermaid svg):",
              "PASS" if has_fallback else "FAIL(仅查固定位置易回归)")
        if not has_fallback: ok = False
    else:
        print("[4.6] 未找到 _shared/js/modal.js: SKIP")

    # 4.7 宽屏隐藏移动端目录：report.css 须含 @media (min-width:769px) 且含 display:none（防宽窗残留底部目录）
    rcss = os.path.join(base, "_shared", "css", "report.css")
    if os.path.isfile(rcss):
        ctxt = open(rcss, encoding="utf-8").read()
        m = re.search(r'@media\s*\(min-width:\s*769px\)', ctxt)
        has_wide_hide = bool(m) and ('display:none' in ctxt[m.start():m.start()+400])
        print("[4.7] report.css 宽屏隐藏移动端目录(@media min-width:769px + display:none):",
              "PASS" if has_wide_hide else "FAIL(宽屏可能残留底部目录)")
        if not has_wide_hide: ok = False
    else:
        print("[4.7] 未找到 _shared/css/report.css: SKIP")

    # 4.9 本地相对资源引用（src/href="./..."）必须实际存在，防断链（如 mermaid.min.js 本地路径缺失导致图不渲染）
    res_missing = []
    for attr in ("src", "href"):
        for ref in re.findall(r'%s="\./([^"]+)"' % attr, s):
            rp = os.path.normpath(os.path.join(base, ref))
            if not os.path.isfile(rp):
                res_missing.append("%s: ./%s" % (attr, ref))
    print("[4.9] 本地资源存在性(相对路径):",
          "PASS" if not res_missing else ("FAIL 缺失: " + str(res_missing[:5])))
    if res_missing: ok = False

    # 4.8 移动端目录面板默认隐藏机制（对齐 参考实现：.mobile-toc-panel 默认 display:none，仅 .open 时 flex）
    # 防止回归到"display:flex 默认 + transform 隐藏"的脆弱机制（导致宽窄屏残留/样子不对）
    if os.path.isfile(rcss):
        c2 = open(rcss, encoding="utf-8").read()
        m = re.search(r'\.mobile-toc-panel[^\{]*\{', c2)
        block = c2[m.start():m.start()+260] if m else ''
        panel_default_none = ('display:none' in block)
        fab_narrow = ('@media (max-width:768px)' in c2) and ('.mobile-toc-fab' in c2) and ('display:flex' in c2[c2.find('@media (max-width:768px)'):c2.find('@media (max-width:768px)')+400])
        ok8 = panel_default_none and fab_narrow
        print("[4.8] 面板默认display:none 且 FAB窄屏显示:",
              "PASS" if ok8 else "FAIL(面板默认display:flex 或 FAB未窄屏显示)")
        if not ok8: ok = False
    else:
        print("[4.8] 未找到 _shared/css/report.css: SKIP")

    # 版本号一致性
    base = os.path.dirname(html_path)
    cfg = os.path.join(base, "_shared", "js", "config.js")
    ver = None
    if os.path.isfile(cfg):
        cm = re.search(r'REPORT_VERSION\s*=\s*["\']([^"\']+)', open(cfg, encoding="utf-8").read())
        ver = cm.group(1) if cm else None
    chlog = os.path.join(base, "CHANGELOG.md")
    devdoc = os.path.join(base, "DEV_DOC.md")
    cv = re.search(r'v\d+\.\d+', open(chlog, encoding="utf-8").read()) if os.path.isfile(chlog) else None
    dv = re.search(r'版本:\s*(v\d+\.\d+)', open(devdoc, encoding="utf-8").read()) if os.path.isfile(devdoc) else None
    print("[VER] config.js=%s  CHANGELOG=%s  DEV_DOC=%s" % (ver, cv.group(0) if cv else "?", dv.group(1) if dv else "?"),
          "PASS" if (ver and cv and dv and cv.group(0) == ver and dv.group(1) == ver) else "FAIL")
    if not (ver and cv and dv and cv.group(0) == ver and dv.group(1) == ver): ok = False

    print("\n结果:", "ALL PASS ✅" if ok else "存在失败项 ❌")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
