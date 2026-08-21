---
name: "html-report-V0-A"
description: "通用 HTML 技术报告生成 skill：包含规则、约束、模板、测试用例。当需要从零创建一份结构化技术报告（含动态目录/侧边栏、标题折叠、图片模态查看器、引用悬停预览、Mermaid 直角框图、校验脚本），或按统一规范（绘图/模态/目录/正文/版本号/校验）产出或修正 HTML 报告时使用。用户要求生成'报告模板/skill'或'通用 html 报告'时优先调用。本 skill 是官方 html/image 类 skill 的**补充与约束层**：模态图片查看器与图形查看请调用 `modal-image-viewer-skill`（按名字，AI 自行定位），HTML 前端校验请调用 `html-frontend-checker-skill`（按名字）；本 skill 在其上补充动态目录/折叠/版本单一来源/文件结构/样式约束，并对背景透明度等施加约束覆盖。"
---
# 通用 HTML 报告 Skill（html-report-V0-A）

> **版本**: v0.01
> **用途**: 以"指令 + 模板 + 脚本 + 规则 + 测试用例"五段式，提供一套**通用、可信、可靠**的 HTML 技术报告工程。未来 AI 可直接复制 `_shared/js/*.js`、`_shared/css/report.css`、`templates/report.html`，无需重新推导交互逻辑，从而显著降低 token 消耗并保证一致性。
> **设计哲学**: 一切可复用代码进入 `templates/_shared/`；一切规则进入 `rules/`；一切检查进入 `scripts/validate.py`；一切可验证项进入 `tests/`。

---

## 0. 定位与依赖（官方 skill 优先，本 skill 为补充/约束层）

本 skill **不是**从零造轮子，而是对官方 html/image 类 skill 的**补充与约束**：

| 能力 | 由谁提供（按名字调用） | 本 skill 的补充/约束 |
|------|------------------------|----------------------|
| **图片模态查看器**（缩放/拖拽/平移/切换/ESC） | **`modal-image-viewer-skill`**（AI 按名字自行定位） | 随附其适配副本于 `_shared/js/modal.js` + `_shared/css/modal.css`（保证 scaffold 开箱即用）；施加约束覆盖：**1.2 遮罩透明**（覆盖该 skill 默认的 `rgba(0,0,0,.55)` 深色遮罩）、**1.4 白底图形区**。 |
| **SVG / Mermaid 图形绘制与 figure 结构** | **`modal-image-viewer-skill`**（其 `templates/figure.html` 给出 `figure.diagram`/`figure.chart-figure` 结构与 `openImageModal` 约定） | 本 skill 的 `diagrams.js` 仅负责**页面侧 Mermaid 渲染**（在 modal 克隆 SVG 前完成），绘图规则（直角连线/低饱和底色/唯一 id）见 `rules/constraints.md`。 |
| **HTML 前端合规校验** | **`html-frontend-checker-skill`**（80+ 项检查） | 本 skill 的 `scripts/validate.py` 提供轻量交付前校验（4.1–4.5 + 版本一致性），两者可并行使用。 |

> 调用约定：**只给名字**，让 AI 自行在工作区定位 `modal-image-viewer-skill` / `html-frontend-checker-skill` 并采用其 `templates/` 与 `scripts/`，无需写出绝对路径。若需离线/加固，可将官方 skill 的最新 `modal.js`/`modal.css` 复制进本 skill 的 `_shared/` 覆盖适配副本。

---

## 1. 资源索引

| 分类 | 文件                                 | 用途                                                                    |
| ---- | ------------------------------------ | ----------------------------------------------------------------------- |
| 文档 | `SKILL.md`                         | 本文件（指令与总览）                                                    |
| 文档 | `CHANGELOG.md`                     | 本 skill 的版本变更历史                                                 |
| 模板 | `templates/report.html`            | 报告正文完整模板（已接线所有 JS/CSS，含示例章节）                       |
| 模板 | `templates/_shared/css/report.css` | 全部样式（颜色/字体/布局/目录/折叠/表格/代码块）+ 对 modal.css 的约束覆盖（1.2 透明/1.4 白底） |
| 模板 | `templates/_shared/css/modal.css`  | **源自 `modal-image-viewer-skill`** 的模态查看器样式（适配副本）        |
| 模板 | `templates/_shared/js/config.js`   | **唯一版本号来源** `window.REPORT_VERSION` + 标题/描述占位      |
| 模板 | `templates/_shared/js/toc.js`      | 动态目录 + scroll-spy + 固定/滚动级别 + 移动端目录 + 引用悬停 + 标题自动编号；暴露 `window.__tocRefresh()` |
| 模板 | `templates/_shared/js/collapse.js` | 标题折叠（3.2）+ 代码块默认折叠（3.1）                                  |
| 模板 | `templates/_shared/js/modal.js`    | **源自 `modal-image-viewer-skill`** 的模态查看器（适配副本，满足 1.1–1.10） |
| 模板 | `templates/_shared/js/diagrams.js` | 页面侧 Mermaid 渲染 + 直角连线（0.4）+ 自动注入查看按钮（1.1）          |
| 脚本 | `scripts/scaffold.py`              | 生成报告工程（同名父文件夹 +`_shared/` + html + CHANGELOG + DEV_DOC） |
| 脚本 | `scripts/validate.py`              | 交付前校验（4.1–4.5 + 版本一致性），退出码 0/非0                       |
| 规则 | `rules/constraints.md`             | 全部约束（绘图/模态/目录/正文/校验/版本/结构）逐条清单                  |
| 规则 | `rules/style-spec.md`              | 色块颜色、字体、间距等样式令牌（token）规范                             |
| 测试 | `tests/testcases.md`               | 交付前测试用例与验收清单                                                |

---

## 2. 何时使用 / 工作流

1. **调用官方 skill（按名字）**：模态查看器与图形查看调用 **`modal-image-viewer-skill`**；交付前 HTML 前端合规可调用 **`html-frontend-checker-skill`**。本 skill 的 `_shared/js/modal.js`、`_shared/css/modal.css` 即这两 skill 的适配副本，可直接复用。
2. **创建新报告**：运行 `python3 scripts/scaffold.py <报告名> [父目录]`，得到 `<报告名>/`（含 `_shared/`、`CHANGELOG.md`、`DEV_DOC.md`、`<报告名>.html`）。
3. **编辑正文**：删除 `templates/report.html` 示例，按"章节结构"约定撰写（见 §4）。修改 `_shared/js/config.js` 的 `REPORT_VERSION` / 标题。
4. **加图形**：每个图用 `<figure class="diagram" id="fig-<章>-<序号>">`（结构遵循 `modal-image-viewer-skill` 的 `figure.html`），内部 `<pre class="mermaid">` 写 Mermaid 源码；查看按钮由 `diagrams.js` 自动注入（或手写 `<button class="zoom-btn" onclick="openImageModal('fig-x')">查看</button>`）。
5. **同步文档**：每次修改后更新 `CHANGELOG.md`（必须）与 `DEV_DOC.md`（用户要求/答复/目的/架构/大纲）。
6. **交付前校验**：`python3 scripts/validate.py <报告目录或html>`（轻量），必要时叠加 `html-frontend-checker-skill`，必须 ALL PASS。

> 通用性提示：模板与脚本**不绑定任何业务领域**。业务知识应只出现在具体报告正文，不在 skill 内。

---

## 3. 章节结构约定（模板默认写法）

```html
<div class="section" id="ch1">              <!-- 章：h1 -->
  <h1>第一章 标题</h1>
  <div class="section-content">
    <div class="section" id="sec1-1">        <!-- 节：h2 -->
      <h2>小节标题</h2>
      <div class="section-content"> ... </div>
    </div>
  </div>
</div>
```

- 标题编号由 `toc.js` 自动注入（3.2），**正文中不要手工写"1.1"**，避免与 CSS/JS 编号错位。
- 每个图/代码/表格都放在某个 `.section-content` 内，便于折叠（3.2）。

---

## 4. 关键规则速览（完整版见 `rules/constraints.md`）

| 域             | 要点                                                                                                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 绘图 0.1–0.5  | 含文字图形低饱和底色；直角连线（0.4）；复查连线/箭头（0.2/0.3）；`figure` id 全局唯一且带章节前缀（0.5）                                                                                                    |
| 模态 1.1–1.10 | 调用 **`modal-image-viewer-skill`**（按名字）实现查看器；本 skill 覆盖其默认深色遮罩为**透明背景（1.2）**、保持**白底图形区（1.4）**；支持 +/-/拖拽/滚轮缩放（1.6）、‹/›切换且首尾 disabled（1.8）、完整显示优先 SVG 真实尺寸（1.9）                                                                               |
| 目录 2.1–2.8  | 侧边栏 + 移动端双目录（2.1）；滚动高亮居中（2.3）；收纳所有级别（2.8）；窄屏折叠为下方目录（2.7）                                                                                                             |
| 正文 3.1–3.14 | 代码默认折叠（3.1）；标题折叠+编号（3.2）；白/无色底（3.3）；引用悬停预览（3.4）；系统字体（3.5）；标签实体转义（3.6）；插入不破坏收尾块（3.8）；特别说明强调正确点（3.11/3.13）；结论须推理/参考得出（3.14） |
| 校验 4.1–4.5  | div 配对（4.1）；截断行 0（4.2）；标签平衡（4.3）；重复 id 空（4.4）；目录收纳所有标题（4.5）                                                                                                                 |
| 版本号         | 0.01→0.99 递增；非用户要求禁止大版本/后缀；正文仅`config.js` 一处版本变量；`CHANGELOG`/`DEV_DOC` 版本须一致                                                                                            |
| 文件结构       | 同名父文件夹含`_shared/`、`html`、`CHANGELOG.md`、`DEV_DOC.md`；HTML 正文不保存变更记录                                                                                                               |

---

## 5. 样式规范（摘要，完整见 `rules/style-spec.md`）

- **底色**：文档 `#ffffff`（白/无色，3.3）；模态背景 `transparent`（1.2）；图形区 `#ffffff`（1.4）。
- **低饱和图形色**：节点填充 `#f6f8fa`、高亮 `#fef9c3`、描边 `#6b7280`（0.1）。
- **字体**：系统默认字体栈（`-apple-system, …, "PingFang SC", "Microsoft YaHei", sans-serif`），不引入外部字体（3.5）。
- **强调色**：`--accent:#3b6cb7`（低饱和蓝）；callout 四色（tip/warn/note/danger）均为低饱和底+彩色左边框。
- **布局**：固定左侧边栏 `300px`，正文 `margin-left:300px; overflow-x:hidden`；`html,body` 同设 `overflow-x:hidden`；表格 `table-layout:fixed`。

---

## 6. 交付前校验（必须全过）

```bash
python3 scripts/validate.py <报告目录或 html>
# 输出 4.1 div配对 / 4.2 截断行 / 4.3 标签平衡 / 4.4 重复id / 4.5 目录完整性 / 版本一致性
# 全部 PASS ✅ 方可交付；非 0 退出码表示失败
```

---

## 7. 测试用例

见 `tests/testcases.md`：覆盖脚手架生成、目录动态性、模态查看器各交互、折叠、Mermaid 直角、版本一致性、各校验项失败注入等，交付前逐项核对。

---

## 8. 版本历史

本 skill 的版本变更见 `CHANGELOG.md`。当前 v0.01。
