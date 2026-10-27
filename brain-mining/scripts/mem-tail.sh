#!/bin/bash
# mem-tail.sh —— 读 MEMORY.md 的唯一入口（10-24 立，10-25 升级为 brief 优先）
# 为什么存在：MEMORY 已 584KB，read 在 128KB 截断，一次大读全沉没。
# 10-23 记规则 / 10-24 再犯 / 10-25 三犯（知道有脚本仍裸 read）→ 判定「提醒形态失效」。
# 升级逻辑：不再靠提醒，改为让本脚本的输出严格优于裸读 —— 裸读只能拿到 128KB 截断正文，
# 本脚本一次给出体积、编号水位、最近串联标题、观测项台账状态、待拍板项。没有理由再裸读。
# 用法：
#   bash scripts/mem-tail.sh            # brief 模式（默认）：结构 + 尾部状态块
#   bash scripts/mem-tail.sh 300        # 取末 300 行正文
set +e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEM="$ROOT/MEMORY.md"
OBS="$ROOT/memory/observations.md"
ARG="$1"

SIZE=$(wc -c < "$MEM" | tr -d ' ')
LINES=$(wc -l < "$MEM" | tr -d ' ')
echo "== MEMORY：${SIZE}B / ${LINES} 行 =="

# 若传入数字则按旧行为输出正文
if [[ "$ARG" =~ ^[0-9]+$ ]]; then
  echo "== 正文末 ${ARG} 行 =="
  tail -n "$ARG" "$MEM"
  echo ""
  echo "== 编号水位 =="
  grep -o "^### 串联[^（]*" "$MEM" | tail -1
  exit 0
fi

echo ""
echo "== 编号水位（全文最后一处串联标题）=="
grep -o "^### 串联[^（]*" "$MEM" | tail -1
echo ""
echo "== 最近 8 条串联标题 =="
grep -o "^### 串联[^（]*" "$MEM" | tail -8
echo ""
echo "== 知识缝合区段数 =="
grep -c "^## 知识缝合 \[" "$MEM"
echo ""
if [ -f "$OBS" ]; then
  echo "== 观测项台账（外置：memory/observations.md）=="
  echo "未关闭 $(grep -c '^- \[ \]' "$OBS" 2>/dev/null) / 已关闭 $(grep -c '^- \[x\]' "$OBS" 2>/dev/null)"
else
  echo "== 观测项台账文件缺失：memory/observations.md =="
fi
echo ""
echo "== 待逸凡拍板（全文最后一次出现）=="
grep "待逸凡拍板" "$MEM" | tail -1 | cut -c1-400
echo ""
echo "== MEMORY 尾部 10 行 =="
tail -n 10 "$MEM"
exit 0
