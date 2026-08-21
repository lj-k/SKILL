// ===== 报告唯一版本号来源 =====
// 规则：正文中仅此一处版本号变量，避免设置多个版本号导致漏改。
// 侧边栏与 meta 的版本显示由 report.html 末尾的注入脚本读取本变量自动填充。
// 修改版本时只改这里；CHANGELOG.md / DEV_DOC.md 的版本号应与之保持一致。
window.REPORT_VERSION = "v0.01";
window.REPORT_TITLE = "技术报告标题（请在 config.js 中修改）";
window.REPORT_DESC  = "报告一句话描述（请在 config.js 中修改）";
