#!/bin/bash
# 用法: ./check-view-buttons.sh <file.html>
# 检查每个 figure 恰好有一个"查看"按钮，且未使用禁用模式
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

FIGURE_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
VIEW_BTN_COUNT=$(grep -oP 'class="zoom-btn"' "$FILE" | wc -l)
INLINE_BTN_COUNT=$(grep -oP '<button\s+style="[^"]*">查看</button>' "$FILE" | wc -l)
DYNAMIC_JS=$(grep -c 'appendChild.*btn\|createElement.*button.*查看' "$FILE")

echo "Figures: $FIGURE_COUNT, zoom-btn: $VIEW_BTN_COUNT, inline: $INLINE_BTN_COUNT, dynamic JS: $DYNAMIC_JS"
if [ "$VIEW_BTN_COUNT" -eq "$FIGURE_COUNT" ] && [ "$INLINE_BTN_COUNT" -eq 0 ] && [ "$DYNAMIC_JS" -eq 0 ]; then
  echo "OK: 每图恰好 1 个按钮"
else
  echo "FAIL: 按钮数量不一致或存在禁用模式"
fi