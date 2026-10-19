#!/usr/bin/env bash
# dreaming 收尾脚本（守卫AF / 守卫Y 四态 / 守卫AE / 守卫N 自证）
# 顺序固定：全部写动作 -> add -> commit -> 工作区必须空 -> push -> 远端 tip 三态取证
# 用法: bash dreaming_closeout.sh YYYY-MM-DD "commit message"
set -u
REPO="/Users/yifansmacmini/.openclaw/workspace"
TODAY="${1:?usage: dreaming_closeout.sh YYYY-MM-DD \"msg\"}"
MSG="${2:-cfo dreaming $TODAY}"
cd "$REPO" || { echo "FAIL: cannot cd $REPO"; exit 1; }

echo "== 0) MEMORY.md 体量检查 + 自动归档 (守卫AH 阈值 / 守卫AI 动作) =="
MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
echo "MEMORY.md: ${MEMB} bytes / ${MEML} lines"
if [ "$MEMB" -gt 131072 ]; then
  echo "超 128KB (${MEMB}B) -> 触发 memory_archive.py --apply（守卫AI：动作编译进默认路径）"
  python3 cfo/tmp/giftlist/memory_archive.py --apply --tier2 --today "$TODAY" || echo "WARN: memory_archive.py 返回非 0"
  MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
  MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
  echo "归档后: ${MEMB} bytes / ${MEML} lines"
  if [ "$MEMB" -gt 131072 ]; then echo "WARN: 归档后仍超 128KB（无安全可迁区块）"; else echo "OK: 已回落到 128KB 以内"; fi
else
  echo "OK: MEMORY.md 在 128KB 以内"
fi

echo "== 0b) pending.json 校验 (守卫AJ) =="
if [ -f cfo/tmp/giftlist/pending.json ]; then
  python3 -c "import json;d=json.load(open('cfo/tmp/giftlist/pending.json'));print('pending.json OK:',len([i for i in d['items'] if i.get('status')=='open']),'open')" 2>&1 || echo "WARN: pending.json 解析失败"
else
  echo "WARN: pending.json 缺失（守卫AJ 落地项）"
fi

echo "== 0c) 当日交互巡检 (守卫AM: 不得默认零交互) =="
SESS_DIR="$HOME/.openclaw/agents/cfo/sessions"
echo "当日被写入的 session jsonl（含本轮 dreaming）:"
find "$SESS_DIR" -maxdepth 1 -name '*.jsonl' -newermt "$TODAY 00:00" -print 2>/dev/null | sed 's#.*/##'
if [ -f "cfo/memory/$TODAY.md" ]; then echo "当日 memory 文件: 存在"; else echo "当日 memory 文件: 不存在（判断是否零交互须以 session 目录为准，不得默认）"; fi

echo "== 1) staged (cfo paths) =="
git add "cfo/MEMORY.md" "cfo/memory/dreaming-$TODAY.md" 2>/dev/null
git add cfo/memory/archive/ 2>/dev/null
git add -f cfo/tmp/giftlist/*.py cfo/tmp/giftlist/*.sh cfo/tmp/giftlist/*.json 2>/dev/null
git status --short -- cfo/
echo "-- ignored/untracked under cfo/tmp (守卫AG: 假干净检查) --"
git status --short --ignored -- cfo/tmp/ | grep -v '^\.\.' || true

if ! git diff --cached --quiet; then
  git commit -m "$MSG" || { echo "FAIL: commit"; exit 1; }
else
  echo "(nothing new to commit)"
fi

echo "== 2) post-commit working tree (该路径必须为空) =="
DIRTY="$(git status --short -- cfo/)"
if [ -n "$DIRTY" ]; then
  echo "WARN: cfo/ 工作区仍非空:"
  echo "$DIRTY"
else
  echo "OK: cfo/ 工作区干净（非 ignored 路径）"
fi
echo "-- 关键脚本跟踪态 (must be 1 each) --"
for f in cfo/tmp/giftlist/audit.py cfo/tmp/giftlist/rec_api.py cfo/tmp/giftlist/dreaming_closeout.sh; do
  echo -n "$f: "; git ls-files "$f" | wc -l | tr -d ' '
done

echo "== 3) push (守卫Z: 实际通道探活, curl 不算) =="
git push github HEAD 2>&1 | tail -3
echo "push_exit=${PIPESTATUS[0]}"

echo "== 4) ahead/behind (左=远端独有 右=本地待推) =="
git rev-list --left-right --count github/main...HEAD

echo "== 5) remote tip 三态取证 =="
echo -n "remote MEMORY 含 $TODAY 区块: "; git show "github/main:cfo/MEMORY.md" 2>/dev/null | grep -c "$TODAY"
echo -n "remote dreaming-$TODAY.md 存在: "; git ls-tree github/main "cfo/memory/dreaming-$TODAY.md" | wc -l | tr -d ' '
echo -n "remote audit.py 含 邮寄编号: "; git show "github/main:cfo/tmp/giftlist/audit.py" 2>/dev/null | grep -c "邮寄编号"

echo "== 6) 守卫AK cron 余量检查 (ok 轮 duration 超上限 80% 即高危；阈值随实际 timeout 动态计算) =="
DB="$HOME/.openclaw/state/openclaw.sqlite"
JOB="07cd1aef-08d4-4109-a178-a20c8adc8209"
ROW="$(sqlite3 "$DB" "SELECT datetime(last_run_at_ms/1000,'unixepoch','+8 hours')||'|'||ifnull(last_run_status,'')||'|'||ifnull(last_duration_ms,0)||'|'||ifnull(payload_timeout_seconds,0) FROM cron_jobs WHERE job_id='$JOB';" 2>/dev/null)"
echo "上一轮 cron (run_at|status|duration_ms|timeout_s): $ROW"
DUR="$(echo "$ROW" | awk -F'|' '{print $3}')"
TMO="$(echo "$ROW" | awk -F'|' '{print $4}')"
if [ -n "$DUR" ] && [ "$DUR" -gt 0 ] 2>/dev/null && [ -n "$TMO" ] && [ "$TMO" -gt 0 ] 2>/dev/null; then
  LIMIT=$((TMO * 1000))
  THRESH=$((LIMIT * 80 / 100))
  echo "距 ${TMO}s 上限余量: $((LIMIT - DUR)) ms（高危线 = 上限 80% = ${THRESH}ms）"
  if [ "$DUR" -gt "$THRESH" ]; then echo "WARN 守卫AK: 上一轮 duration ${DUR}ms > 上限 80%（${THRESH}ms）高危线"; else echo "OK 守卫AK: 上一轮 duration ${DUR}ms 在上限 80% 以下"; fi
else
  echo "WARN 守卫AK: 未能读到 last_duration_ms / payload_timeout_seconds"
fi
