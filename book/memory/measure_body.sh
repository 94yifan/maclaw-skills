#!/bin/sh
# 规则28 量体执行器：计「复盘正文 A-D 段」字节数（截止到「## 执行记录」行之前）
# 用法：sh memory/measure_body.sh memory/dreaming-YYYY-MM-DD.md [...]
# 对象定义：A-D 段 = 文件开头到 "## 执行记录" 之前；无执行记录段则计全文并标 WARN。
# 缺文件 / 空文件一律 fail-fast，不返回 0 字节冒充合格。
set -eu

if [ "$#" -eq 0 ]; then
  echo "usage: sh memory/measure_body.sh <dreaming.md> [...]" >&2
  exit 2
fi

for f in "$@"; do
  if [ ! -f "$f" ]; then
    echo "FAIL $f: 文件不存在" >&2
    exit 3
  fi
  full=$(wc -c < "$f" | tr -d ' ')
  if [ "$full" -eq 0 ]; then
    echo "FAIL $f: 0 字节（占位文件，不是产物）" >&2
    exit 4
  fi
  if grep -q '^## 执行记录' "$f"; then
    body=$(awk '/^## 执行记录/{exit} 1' "$f" | wc -c | tr -d ' ')
    printf '%s  A-D=%sB  全文=%sB  上限=1536B  %s\n' "$f" "$body" "$full" \
      "$( [ "$body" -le 1536 ] && echo 达标 || echo 超线 )"
  else
    printf '%s  A-D=%sB(无执行记录段, WARN)  全文=%sB  上限=1536B\n' "$f" "$full" "$full"
  fi
done
