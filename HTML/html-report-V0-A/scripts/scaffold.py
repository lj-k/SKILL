#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold.py —— 依据 html-report-V0-A 模板生成一个新报告工程。

生成结构（满足"报告文件夹"要求）：
    <name>/
    ├── _shared/            # 共享脚本（js/css），从 skill 模板复制，可直接复用
    │   ├── css/report.css
    │   └── js/{config,toc,collapse,modal,diagrams}.js
    ├── <name>.html         # 报告正文（已替换标题占位符）
    ├── CHANGELOG.md        # 变更日志（含版本号，与 HTML 一致）
    └── DEV_DOC.md          # 开发文档（用户要求 / 答复 / 目的 / 架构 / 大纲）

用法：
    python3 scaffold.py <报告名> [输出父目录]
例：
    python3 scaffold.py my-report ./REPORTS/foo

版本号：新报告默认 v0.01；后续修改递增（见 SKILL.md 版本号要求）。
"""
import os, sys, shutil, datetime

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SKILL_DIR, "..", "templates")   # skill/templates
PLACEHOLDER_TITLE = "通用技术报告模板"

def main():
    if len(sys.argv) < 2:
        print("用法: python3 scaffold.py <报告名> [输出父目录]")
        sys.exit(1)
    name = sys.argv[1].strip()
    out_parent = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    out_dir = os.path.join(out_parent, name)
    if os.path.exists(out_dir):
        print("错误: 目标已存在 ->", out_dir)
        sys.exit(1)

    tpl_html = os.path.join(TEMPLATE_DIR, "report.html")
    tpl_shared = os.path.join(TEMPLATE_DIR, "_shared")
    if not os.path.isfile(tpl_html) or not os.path.isdir(tpl_shared):
        print("错误: 模板缺失", tpl_html, tpl_shared)
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    # 复制共享脚本
    shutil.copytree(tpl_shared, os.path.join(out_dir, "_shared"))
    # 复制并改写 HTML 标题占位符
    with open(tpl_html, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("<title>" + PLACEHOLDER_TITLE + "（html-report-V0-A）</title>",
                        "<title>" + name + "</title>")
    html = html.replace('id="doc-title">' + PLACEHOLDER_TITLE + "</h1>",
                        'id="doc-title">' + name + "</h1>")
    with open(os.path.join(out_dir, name + ".html"), "w", encoding="utf-8") as f:
        f.write(html)

    today = datetime.date.today().isoformat()
    # CHANGELOG.md
    with open(os.path.join(out_dir, "CHANGELOG.md"), "w", encoding="utf-8") as f:
        f.write("# 更新日志（Changelog）\n\n")
        f.write("> 版本号从 v0.01 递增，与 HTML 报告（config.js 的 REPORT_VERSION）保持一致。\n")
        f.write("> 每次更新文档必须同步更新本文件；HTML 正文内不保存变更记录。\n\n")
        f.write("## 版本 v0.01\n\n")
        f.write("### v0.01 - " + today + "\n\n")
        f.write("- 版本升级: 新建（基于 html-report-V0-A 模板）\n")
        f.write("- 初始化报告骨架：_shared 共享脚本 + 章节/目录/模态查看器/折叠/引用预览。\n")
        f.write("- 校验：div 配对、截断行、标签平衡、figure id 唯一性均通过。\n")
    # DEV_DOC.md
    with open(os.path.join(out_dir, "DEV_DOC.md"), "w", encoding="utf-8") as f:
        f.write("# 开发说明文档（DEV_DOC）\n\n")
        f.write("## 版本: v0.01\n\n")
        f.write("> 开发文档版本号与 HTML 报告版本号保持一致。\n\n")
        f.write("## 1. 用户要求\n\n- （在此记录每次对话中的用户要求）\n\n")
        f.write("## 2. 答复摘要\n\n- （在此记录关键答复与决策）\n\n")
        f.write("## 3. 开发目的\n\n（报告要解决什么问题）\n\n")
        f.write("## 4. 组织架构\n\n- 顶层：`<name>.html` 正文 + `_shared/` 共享脚本 + `CHANGELOG.md` + `DEV_DOC.md`。\n")
        f.write("- 正文按 `chapter(.section>h1)` → `section(.section>h2)` → 子节(h3/h4) 组织。\n\n")
        f.write("## 5. 大纲\n\n- 第一章：概述与方法\n- 第二章：方案与示意图\n\n")
        f.write("## 6. 变更历史\n\n| 版本 | 日期 | 变更内容 |\n|------|------|----------|\n")
        f.write("| v0.01 | " + today + " | 基于 html-report-V0-A 模板初始化 |\n")

    print("已生成报告工程:")
    for root, dirs, files in os.walk(out_dir):
        for fn in sorted(files):
            print("  " + os.path.relpath(os.path.join(root, fn), out_parent))
    print("\n下一步: 编辑", name + "/<name>.html", "正文；修改 _shared/js/config.js 的版本号；交付前运行 validate.py。")

if __name__ == "__main__":
    main()
