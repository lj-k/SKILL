# HTML Frontend Checker v0.01

综合 HTML 前端检查工具，基于 5 个文档项目 40+ 个历史 bug 整理而成。

## 快速开始

```bash
# 检查单个文件
python3 html_frontend_checker.py --file /path/to/file.html

# 检查目录下所有 HTML 文件
python3 html_frontend_checker.py --dir /path/to/directory

# 列出所有检查项
python3 html_frontend_checker.py --list

# 按标签过滤检查
python3 html_frontend_checker.py --file /path/to/file.html --tags structure,css

# 指定报告输出路径
python3 html_frontend_checker.py --file /path/to/file.html --output /path/to/report.html
```

## 检查项一览

共 80+ 项检查，分 8 个类别：

| 类别 | 检查数 | 说明 |
|------|--------|------|
| 结构检查 | 20 | 标签配对、标题层级、DOM元素位置、stray标签、双层嵌套、callout不包裹子节标题、figure id唯一性 |
| CSS检查 | 15 | 模态窗口透明/无限制、侧边栏nowrap、overflow-x、margin-left、table-layout、响应式级联顺序 |
| JS检查 | 16 | scroll-spy完整性、折叠/查看器/提示JS、DOMContentLoaded、Mermaid异步、重复检测 |
| 导航检查 | 10 | 侧边栏/ToC存在性、链接完整性、重复锚点、标题匹配 |
| 框图检查 | 13 | 查看器按钮(缩放/拖拽/ESC/切换)、figure包裹、figcaption、Mermaid兼容性、openImageModal引用有效性 |
| 内容检查 | 8 | 标题编号、表格caption、编号唯一性、代码折叠、引用一致性 |
| 版本检查 | 6 | 版本一致性/格式/位置、文件名匹配、损坏检测、备份检测 |
| 已知Bug模式 | 8 | JS块剥离、默认折叠、Mermaid标签、编号跳跃、版本混用、重复按钮 |

## 与 html-check 的关系

本工具是对现有 `html-check` 的扩展和增强：

| 对比项 | html-check | html-frontend-checker |
|--------|-----------|----------------------|
| 检查数 | 51 | 80+ |
| CSS合规检查 | 无 | 14项（模态窗口/侧边栏/overflow等） |
| JS完整性检查 | 基础 | 增强（async/重复/空引用/重计算） |
| 框图查看器 | 无 | 12项（缩放/拖拽/ESC/切换/兼容性） |
| 已知Bug模式 | 无 | 8项（历史bug模式检测） |
| 损坏检测 | 无 | 有（版本混用/截断/备份） |

两者可同时运行以获得最大覆盖。

## 文件结构

```
html-frontend-checker/
├── SKILL.md                    # Skill 定义文件
├── html_frontend_checker.py    # 主检查脚本（自包含，无外部依赖）
├── known_bugs.md               # 已知 bug 模式参考文档
└── README.md                   # 本文件
```

## 报告格式

生成的 HTML 报告包含：
- 汇总卡片（通过/失败/警告/错误数、通过率、文件数）
- 失败/警告按分类统计的标签云
- 每个文件的可折叠详情面板
- 通过率颜色编码（绿色>=90%，橙色>=70%，红色<70%）

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.01 | 2026-08-14 | 初始版本，80+ 检查项，基于 5 个项目 40+ 历史 bug |
| v0.02 | 2026-08-16 | 新增响应式级联顺序检查；修复 3 类误报（oldId/scroll-spy硬编码/侧栏标题文本）+ 跨选择器级联误报 |
| v0.03 | 2026-08-20 | 新增检查：`callout不包裹子节标题`（栈式解析，防 div 配对盲区）、`figure id 唯一性(fig-)`、`openImageModal引用有效性`；源自 V1A v0.07~v0.10 系列修复经验 |
