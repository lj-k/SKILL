#!/bin/bash
# 用法: ./check-modal-viewer.sh <file.html> [charts.js]
# 综合校验模态图片查看器的所有规则
FILE="${1:?用法: $0 <file.html> [charts.js]}"
CHARTS_JS="${2:-}"

echo "========================================="
echo "模态图片查看器综合校验"
echo "文件: $FILE"
echo "========================================="
FAIL=0

# === 1. div 标签平衡 ===
DIV_OPEN=$(grep -oP '<div\b' "$FILE" | wc -l)
DIV_CLOSE=$(grep -oP '</div>' "$FILE" | wc -l)
if [ "$DIV_OPEN" -eq "$DIV_CLOSE" ]; then
  echo "[1] div 平衡: OK ($DIV_OPEN = $DIV_CLOSE)"
else
  echo "[1] div 平衡: FAIL ($DIV_OPEN != $DIV_CLOSE)"; FAIL=1
fi

# === 2. 未闭合标签 ===
UNCLOSED=$(grep -Pn '</\w+\s*$' "$FILE" | wc -l)
if [ "$UNCLOSED" -eq 0 ]; then
  echo "[2] 未闭合标签: OK (0)"
else
  echo "[2] 未闭合标签: FAIL ($UNCLOSED)"; FAIL=1
fi

# === 3. script 内 HTML 实体编码 ===
ENTITY_CNT=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', c, re.DOTALL)
print(sum(s.count('&lt;') + s.count('&gt;') + s.count('&amp;') for s in scripts))
" 2>/dev/null)
if [ "$ENTITY_CNT" = "0" ]; then
  echo "[3] script 内 HTML 实体: OK (0)"
else
  echo "[3] script 内 HTML 实体: FAIL ($ENTITY_CNT)"; FAIL=1
fi

# === 4. body 上下文 style 标签平衡 ===
STYLE_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
body_only = re.sub(r'<svg\b.*?</svg>', '', c, flags=re.DOTALL)
body_only = re.sub(r'<script\b[^>]*>.*?</script>', '', body_only, flags=re.DOTALL)
opens = len(re.findall(r'<style\b', body_only))
closes = len(re.findall(r'</style>', body_only))
print('OK' if opens == closes else 'FAIL:%d opens vs %d closes' % (opens, closes))
" 2>/dev/null)
if [[ "$STYLE_CHECK" == OK* ]]; then
  echo "[4] body style 平衡: OK"
else
  echo "[4] body style 平衡: FAIL ($STYLE_CHECK)"; FAIL=1
fi

# === 5. figure.chart-figure 必须有 overflow:hidden ===
CHART_FIG_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
m = re.search(r'figure\.chart-figure\s*\{[^}]+\}', c)
print('PASS' if m and 'overflow' in m.group(0) else 'FAIL')
" 2>/dev/null)
if [ "$CHART_FIG_CHECK" = "PASS" ]; then
  echo "[5] chart-figure overflow:hidden: OK"
else
  echo "[5] chart-figure overflow:hidden: FAIL"; FAIL=1
fi

# === 6. figure.diagram 必须无 overflow ===
DIAGRAM_CHECK=$(python3 -c "
import re
with open('$FILE', 'r') as f: c = f.read()
m = re.search(r'figure\.diagram\s*\{[^}]+\}', c)
print('PASS' if m and 'overflow' not in m.group(0) else 'FAIL')
" 2>/dev/null)
if [ "$DIAGRAM_CHECK" = "PASS" ]; then
  echo "[6] diagram 无 overflow: OK"
else
  echo "[6] diagram 无 overflow: FAIL"; FAIL=1
fi

# === 7. Mermaid SVG pointer-events: none ===
MERMAID_CHECK=$(grep -c 'mermaid-wrap svg.*pointer-events.*none' "$FILE" 2>/dev/null)
if [ "$MERMAID_CHECK" -gt 0 ]; then
  echo "[7] Mermaid pointer-events:none: OK"
else
  echo "[7] Mermaid pointer-events:none: FAIL"; FAIL=1
fi

# === 8. 模态中 ECharts 用 echarts.init ===
MODAL_ECHARTS=$(grep -c '_modalChart.*echarts.init' "$FILE" 2>/dev/null)
if [ "$MODAL_ECHARTS" -gt 0 ]; then
  echo "[8] 模态 ECharts 用 init(): OK"
else
  echo "[8] 模态 ECharts 用 init(): FAIL"; FAIL=1
fi

# === 9. 查看按钮数量 ===
FIG_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
BTN_COUNT=$(grep -oP 'class="zoom-btn"' "$FILE" | wc -l)
if [ "$FIG_COUNT" -eq "$BTN_COUNT" ]; then
  echo "[9] 查看按钮数量: OK ($FIG_COUNT = $BTN_COUNT)"
else
  echo "[9] 查看按钮数量: FAIL ($FIG_COUNT != $BTN_COUNT)"; FAIL=1
fi

# === 10. ECharts tooltip appendToBody (如果有 charts.js) ===
if [ -n "$CHARTS_JS" ] && [ -f "$CHARTS_JS" ]; then
  APPEND_CNT=$(grep -c 'appendToBody: true' "$CHARTS_JS" 2>/dev/null)
  if [ "$APPEND_CNT" -gt 0 ]; then
    echo "[10] ECharts appendToBody: OK ($APPEND_CNT 处)"
  else
    echo "[10] ECharts appendToBody: FAIL"; FAIL=1
  fi
fi

# === 11. ECharts 初始化前清除 innerHTML ===
if [ -n "$CHARTS_JS" ] && [ -f "$CHARTS_JS" ]; then
  CLEAR_CHECK=$(grep -c "innerHTML\s*=\s*''" "$CHARTS_JS" 2>/dev/null)
  if [ "$CLEAR_CHECK" -gt 0 ]; then
    echo "[11] ECharts 初始化前清除: OK"
  else
    echo "[11] ECharts 初始化前清除: FAIL"; FAIL=1
  fi
fi

# === 12. ECharts 模态缩放/平移守卫 ===
ZOOM_GUARD=$(grep -c '_modalChart.*return' "$FILE" 2>/dev/null)
if [ "$ZOOM_GUARD" -ge 2 ]; then
  echo "[12] ECharts 模态缩放守卫: OK ($ZOOM_GUARD 处)"
else
  echo "[12] ECharts 模态缩放守卫: FAIL ($ZOOM_GUARD 处，需 >= 2)"; FAIL=1
fi

# === 13. 图片序号连续性 ===
FIG_NUMS=$(grep -oP 'figcaption>图 \K\d+' "$FILE" 2>/dev/null)
FIG_NUM_COUNT=$(echo "$FIG_NUMS" | wc -w)
SEQ_FAIL=0
IDX=1
for n in $FIG_NUMS; do
  if [ "$n" -ne "$IDX" ]; then SEQ_FAIL=1; fi
  IDX=$((IDX + 1))
done
DUP=$(echo "$FIG_NUMS" | tr ' ' '\n' | sort -n | uniq -d)
# 校验 modalTitle 序号为有效图号（1..N 且与某个 figcaption 一致）
MT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE" 2>/dev/null)
NUM_MAX=$((IDX - 1))
MT_FAIL=0
[ -z "$MT" ] && MT_FAIL=1
if [ -n "$MT" ] && { [ "$MT" -lt 1 ] || [ "$MT" -gt "$NUM_MAX" ]; }; then MT_FAIL=1; fi
if [ -n "$MT" ] && ! echo "$FIG_NUMS" | tr ' ' '\n' | grep -qx "$MT"; then MT_FAIL=1; fi
if [ "$SEQ_FAIL" -eq 0 ] && [ -z "$DUP" ] && [ "$FIG_NUM_COUNT" -eq "$FIG_COUNT" ] && [ "$MT_FAIL" -eq 0 ]; then
  echo "[13] 图片序号连续性: OK (图序 $FIG_NUMS, modalTitle=$MT)"
else
  echo "[13] 图片序号连续性: FAIL (顺序: $FIG_NUMS, 重复: $DUP, 数: $FIG_NUM_COUNT/$FIG_COUNT, modalTitle=$MT)"; FAIL=1
fi

echo ""
echo "========================================="
if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
else
  echo "SOME CHECKS FAILED"
fi
echo "========================================="