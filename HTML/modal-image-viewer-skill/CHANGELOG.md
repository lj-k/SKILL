# Changelog

> 本文件记录 `modal-image-viewer` skill 的所有版本变更。当前版本见 `SKILL.md` 头部。

## v1.04

**日期**: 2026-08-13

将版本历史从 `SKILL.md` 独立为 `CHANGELOG.md`。`SKILL.md` 移除第 8 章"版本历史"，改为在头部与资源索引中引用 `CHANGELOG.md`。版本记录集中管理，避免指令文档携带历史噪音。

## v1.03

**日期**: 2026-08-13

重构 SKILL.md 组织结构，按"资源索引 / 集成实现 / 特殊规则 / 交付校验 / 排除故障 / 最佳实践"分门别类。新增第 2 章资源索引表；将 16 个陷阱按问题域归档为 4 张表格（布局与样式、SVG 渲染、ECharts 交互、文档结构）；合并交付校验与检查清单；ECharts 规则独立成章消除交叉。

## v1.02

**日期**: 2026-08-13

彻底清理 SKILL.md 正文中的内嵌代码：移除第 3 章 CSS 全部代码块（改为要点清单）、第 4 章 JS 的 showModalContent/deduplicateSvgId 完整实现、第 5 章 initAll/tooltip 代码块、第 9.2 节标准按钮 HTML 及陷阱 5/7 的代码示例。正文现在只保留规则文字与关键 API 说明，所有代码统一收敛到 `templates/`。

## v1.01

**日期**: 2026-08-13

将 HTML/CSS/JS 模板从 SKILL.md 正文拆分为独立 `templates/` 文件（`modal-window.html`、`figure.html`、`modal.css`、`modal.js`），正文改为引用模板文件并仅保留关键规则与注释。标准 skill 包结构现为 `SKILL.md` + `templates/` + `scripts/`。

## v1.00

**日期**: 2026-08-13

由《模态图片查看器设计 Skill》v2.04 重构为标准 skill 包：新增 frontmatter（name/description），校验脚本从正文中拆分为独立 `scripts/` 目录文件，正文改为引用脚本。整合全部设计规范、陷阱与最佳实践。