#!/bin/bash
# 用法: ./check-structure.sh <file.html>
# 检查文档结构一致性：TOC <-> 正文锚点、版本号、HTML 结构完整性
FILE="$1"
[ -z "$FILE" ] && { echo "用法: $0 <file.html>"; exit 1; }

echo "========================================="
echo "文档结构一致性检查"
echo "文件: $FILE"
echo "========================================="

# 1. TOC <-> 正文锚点
grep -oP 'href="#(sec-[^"]+)"' "$FILE" | sort > /tmp/_toc.txt
grep -oP 'id="(sec-[^"]+)"' "$FILE" | sort > /tmp/_body.txt
echo ""
echo "[1] TOC <-> 正文锚点一致性"
TOC_ONLY=$(comm -23 /tmp/_toc.txt /tmp/_body.txt)
BODY_ONLY=$(comm -13 /tmp/_toc.txt /tmp/_body.txt)
if [ -n "$TOC_ONLY" ]; then echo "  TOC 有但正文无:"; echo "$TOC_ONLY"; fi
if [ -n "$BODY_ONLY" ]; then echo "  正文有但 TOC 无:"; echo "$BODY_ONLY"; fi
if [ -z "$TOC_ONLY" ] && [ -z "$BODY_ONLY" ]; then echo "  OK 全部一致"; fi

# 2. 版本号
echo ""
echo "[2] 版本号一致性"
grep -n '版本 [0-9]\.[0-9][0-9]*' "$FILE"
echo "Badge 版本: $(grep -oP 'badge"[^>]*>v\K[0-9]+\.[0-9]+' "$FILE")"

# 3. HTML 结构
echo ""
echo "[3] HTML 结构完整性"
DIV_OPEN=$(grep -oP '<div\b' "$FILE" | wc -l)
DIV_CLOSE=$(grep -oP '</div>' "$FILE" | wc -l)
echo "  div 开: $DIV_OPEN  关: $DIV_CLOSE"
if [ "$DIV_OPEN" -eq "$DIV_CLOSE" ]; then echo "  OK div 平衡"; else echo "  WARN 不平衡 (差 $((DIV_OPEN - DIV_CLOSE)))"; fi
UNCLOSED=$(grep -Pn '</\w+\s*$' "$FILE" | wc -l)
if [ "$UNCLOSED" -eq 0 ]; then echo "  OK 无未闭合标签"; else echo "  WARN 存在 $UNCLOSED 个未闭合标签"; fi

echo ""
echo "========================================="
echo "检查完成"
echo "========================================="