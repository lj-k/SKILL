#!/bin/bash
# 用法: ./check-figure-numbers.sh <file.html>
# 检查 figcaption 中的图片序号是否按文档出现顺序连续递增（1,2,3...N），
# 并校验模态标题 #modalTitle 的序号是否为有效图号。
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

echo "========================================="
echo "图片序号连续性检查"
echo "文件: $FILE"
echo "========================================="

# 提取 figcaption 中的序号（按文档出现顺序）
NUMS=$(grep -oP 'figcaption>图 \K\d+' "$FILE")
echo "文档中图片序号顺序: $NUMS"

FAIL=0

# 1) 检查是否 1,2,3...N 连续递增
IDX=1
for n in $NUMS; do
  if [ "$n" -ne "$IDX" ]; then
    echo "  FAIL: 第 $IDX 张图序号为 $n（应为 $IDX，须从 1 开始递增）"
    FAIL=1
  fi
  IDX=$((IDX + 1))
done

# 2) 检查是否有重复
DUP=$(echo "$NUMS" | tr ' ' '\n' | sort -n | uniq -d)
if [ -n "$DUP" ]; then
  echo "  FAIL: 存在重复序号: $DUP"
  FAIL=1
fi

# 3) 检查 figure 数量与序号数量是否一致
FIG_COUNT=$(grep -oP '<figure\s+class="(chart-figure|diagram)"' "$FILE" | wc -l)
NUM_COUNT=$(echo "$NUMS" | wc -w)
if [ "$FIG_COUNT" -ne "$NUM_COUNT" ]; then
  echo "  FAIL: figure 数($FIG_COUNT) 与序号数($NUM_COUNT) 不一致"
  FAIL=1
fi

# 4) 校验模态标题 #modalTitle 序号为有效图号（1..N 且与某个 figcaption 一致）
echo ""
echo "[模态标题一致性]"
NUM_MAX=$((IDX - 1))
MT_COUNT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE" | wc -l)
if [ "$MT_COUNT" -ne 1 ]; then
  echo "  FAIL: modalTitle 数量为 $MT_COUNT（应为 1）"
  FAIL=1
else
  MT=$(grep -oP 'id="modalTitle">图 \K\d+' "$FILE")
  echo "  modalTitle 序号: $MT"
  if [ "$MT" -lt 1 ] || [ "$MT" -gt "$NUM_MAX" ]; then
    echo "  FAIL: modalTitle 序号 $MT 超出有效范围 1..$NUM_MAX"
    FAIL=1
  else
    if ! echo "$NUMS" | tr ' ' '\n' | grep -qx "$MT"; then
      echo "  FAIL: modalTitle 序号 $MT 与任一 figcaption 序号不一致"
      FAIL=1
    else
      echo "  OK: modalTitle 序号 $MT 与 figcaption 一致"
    fi
  fi
fi

echo ""
echo "========================================="
if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED: 图片序号从 1 连续递增且无重复，modalTitle 一致"
else
  echo "SOME CHECKS FAILED: 请按文档顺序从 1 重新编号"
fi
echo "========================================="
exit "$FAIL"