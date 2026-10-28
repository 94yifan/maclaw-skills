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
# 守卫BB：阈值单一来源。PRE_LINE = 下一轮 dreaming_open.py 预检线（超了下一轮必须先归档才能写）
# HARD_LINE = read 工具单次上限，越界即真损伤。两者不得混用。
PRE_LINE=126976
HARD_LINE=131072
MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
echo "MEMORY.md: ${MEMB} bytes / ${MEML} lines | 预检线 ${PRE_LINE} 余量 $((PRE_LINE - MEMB))B | 硬线 ${HARD_LINE} 余量 $((HARD_LINE - MEMB))B"
if [ "$MEMB" -gt "$PRE_LINE" ]; then
  echo "超 128KB (${MEMB}B) -> 触发 memory_archive.py --apply（守卫AI：动作编译进默认路径）"
  python3 cfo/tmp/giftlist/memory_archive.py --apply --tier2 --today "$TODAY" || echo "WARN: memory_archive.py 返回非 0"
  MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
  MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
  echo "归档后: ${MEMB} bytes / ${MEML} lines"
  if [ "$MEMB" -gt "$PRE_LINE" ]; then
    echo "二级(30天) 仍超预检线 -> 升级 min-age 14（守卫AV：归档容量须实测，不得假设滚动供给足够）"
    python3 cfo/tmp/giftlist/memory_archive.py --apply --tier2 --min-age 14 --today "$TODAY" || echo "WARN: 升级归档返回非 0"
    MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
    MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
    echo "升级归档后: ${MEMB} bytes / ${MEML} lines"
  fi
  if [ "$MEMB" -gt "$HARD_LINE" ]; then echo "WARN: 归档后仍超硬线 ${HARD_LINE}（无安全可迁区块，须改策略）"; elif [ "$MEMB" -gt "$PRE_LINE" ]; then echo "WARN: 已降到硬线内但仍超预检线，下一轮需先归档才能写"; else echo "OK: 已回落，余量 $((PRE_LINE - MEMB))B"; fi
else
  echo "OK: MEMORY.md 在预检线以内（余量 $((PRE_LINE - MEMB))B）"
fi

echo "== 0b) pending.json 校验 (守卫AJ) =="
if [ -f cfo/tmp/giftlist/pending.json ]; then
  python3 -c "import json;d=json.load(open('cfo/tmp/giftlist/pending.json'));print('pending.json OK:',len([i for i in d['items'] if i.get('status')=='open']),'open')" 2>&1 || echo "WARN: pending.json 解析失败"
  # 守卫BE：待办只认 pending.json —— 当日区块写了「待办」而 pending.json 未更新即漏记
  python3 - "$TODAY" <<'PY'
import json, pathlib, re, sys
today = sys.argv[1]
mem = pathlib.Path("cfo/MEMORY.md").read_text(encoding="utf-8")
m = re.search(r"(?ms)^## " + re.escape(today) + r".*?(?=^## |\Z)", mem)
block = m.group(0) if m else ""
# 只认业务待办行：守卫定义行自身含「待办」字样，须排除，否则每条新守卫都会点亮本检查
scan = "\n".join(l for l in block.split("\n")
                 if "写入即为生效" not in l and not l.lstrip().startswith("- **守卫"))
hit = [k for k in ("新增待办", "待办：", "待办:") if k in scan]
d = json.load(open("cfo/tmp/giftlist/pending.json"))
upd = d.get("updated", "?")
if hit and upd != today:
    print(f"WARN 守卫BE: 当日区块含待办标记 {hit}，但 pending.json updated={upd} != {today}（待办漏记）")
else:
    print(f"OK 守卫BE: pending.json updated={upd}，当日待办标记 {len(hit)} 处")
PY
else
  echo "WARN: pending.json 缺失（守卫AJ 落地项）"
fi

echo "== 0c) 当日交互巡检 (守卫AM: 不得默认零交互) =="
SESS_DIR="$HOME/.openclaw/agents/cfo/sessions"
echo "当日被写入的 session jsonl（含本轮 dreaming）:"
find "$SESS_DIR" -maxdepth 1 -name '*.jsonl' -newermt "$TODAY 00:00" -print 2>/dev/null | sed 's#.*/##'
if [ -f "cfo/memory/$TODAY.md" ]; then echo "当日 memory 文件: 存在"; else echo "当日 memory 文件: 不存在（判断是否零交互须以 session 目录为准，不得默认）"; fi

echo "== 0d) 骨架顺序自检 (守卫AN: 第一条工具调用必须是 dreaming_open.py) =="
python3 - "$SESS_DIR" "$TODAY" <<'PY'
import glob, json, os, sys
sess_dir, today = sys.argv[1], sys.argv[2]
cands = [p for p in glob.glob(os.path.join(sess_dir, "*.jsonl")) if os.path.getmtime(p) >= 0]
cands.sort(key=os.path.getmtime, reverse=True)
first = None
for p in cands[:3]:
    for line in open(p, errors="ignore"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        msg = o.get("message") or {}
        for c in msg.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "toolCall":
                cmd = str((c.get("arguments") or {}).get("command", ""))
                first = (os.path.basename(p), c.get("name"), cmd[:80])
                break
        if first:
            break
    if first:
        break
if not first:
    print("WARN 守卫AN: 未找到当日工具调用记录，无法自检")
else:
    f, name, cmd = first
    ok = "dreaming_open.py" in cmd
    print(f"首个工具调用: {name} | {cmd}")
    print(("OK 守卫AN: 首调用即骨架脚本" if ok else "WARN 守卫AN: 首调用不是骨架脚本（先读后写第 N 轮）"))
PY

echo "== 0e) 当日区块体量 (守卫BF: MEMORY 只放摘要，明细进 dreaming 文件) =="
python3 - "$TODAY" <<'PY'
import re, sys, pathlib
today = sys.argv[1]
t = pathlib.Path("cfo/MEMORY.md").read_text(encoding="utf-8")
m = re.search(r"(?ms)^## " + re.escape(today) + r".*?(?=^## |\Z)", t)
if not m:
    print(f"WARN 守卫BF: 当日区块缺失")
else:
    n = len(m.group(0).encode())
    print(("OK" if n <= 1200 else "WARN") + f" 守卫BF: 当日区块 {n}B（上限 1200B，明细应在 dreaming-{today}.md）")
PY

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

echo "== 6a) 时间坐标对齐 (守卫BC: ts 是完成时刻，起跑 = ts - duration) =="
LOG="$(sqlite3 "$DB" "SELECT ifnull(datetime(ts/1000,'unixepoch','+8 hours'),'')||'|'||ifnull(duration_ms,0)||'|'||ifnull(datetime((ts-duration_ms)/1000,'unixepoch','+8 hours'),'')||'|'||ifnull(seq,'') FROM cron_run_logs WHERE job_id='$JOB' ORDER BY seq DESC LIMIT 1;" 2>/dev/null)"
echo "最新日志 (ts_完成|duration_ms|起跑=ts-duration|seq): $LOG"
SEQ="$(echo "$LOG" | awk -F'|' '{print $4}')"
LTS="$(echo "$LOG" | awk -F'|' '{print $1}')"
LDUR="$(echo "$LOG" | awk -F'|' '{print $2}')"
LSTART="$(echo "$LOG" | awk -F'|' '{print $3}')"
if [ -n "$LTS" ] && [ -n "$LDUR" ] && [ "$LDUR" -gt 0 ] 2>/dev/null; then
  ETS="$(date -j -f '%Y-%m-%d %H:%M:%S' "$LTS" +%s 2>/dev/null)"
  ESTART="$(date -j -f '%Y-%m-%d %H:%M:%S' "$LSTART" +%s 2>/dev/null)"
  if [ -n "$ETS" ] && [ -n "$ESTART" ]; then
    DIFF=$(( (ETS - ESTART) * 1000 ))
    SKEW=$(( DIFF - LDUR )); [ "$SKEW" -lt 0 ] && SKEW=$(( -SKEW ))
    echo "seq $SEQ 起跑 $LSTART / 完成 $LTS / 耗时 ${LDUR}ms / 差 ${DIFF}ms / 偏差 ${SKEW}ms"
    if [ "$SKEW" -le 2000 ]; then echo "OK 守卫BC: ts - duration = 起跑时刻（口径自洽）"; else echo "WARN 守卫BC: 完成时刻与耗时不自洽（偏差 ${SKEW}ms），引用前须核对字段来源"; fi
  else
    echo "WARN 守卫BC: 时间解析失败（$LTS / $LSTART）"
  fi
else
  echo "WARN 守卫BC: 未能读到 cron_run_logs 最新一行"
fi

echo "== 6b) 上一轮 error 归类 (守卫AX: status=error 不等于失败轮) =="
ERR="$(sqlite3 "$DB" "SELECT ifnull(last_error,'') FROM cron_jobs WHERE job_id='$JOB';" 2>/dev/null)"
echo "last_error: ${ERR:-<空>}"
case "$ERR" in
  "") echo "OK: 无 error" ;;
  *timeout*) echo "归类: 超时截断（撞 payload_timeout，产物可能已落盘，须核对 commit）" ;;
  *"gateway restart"*) echo "归类: 进程级 gateway 重启（守卫AO 须当轮回填缺失日）" ;;
  *"Process:"*|*killed*|*"SIGKILL"*) echo "归类: 进程级子进程失败/被杀（须核对产物完整性）" ;;
  *) echo "WARN 守卫AX: 错误文本非超时/重启/进程类 = 工具层失败。判定失败轮前必须三读数对齐：产物（commit + 远端命中）、收尾（最后一条 assistant 消息 stopReason）、运行（status/duration）。三者齐全且收尾正常则归『已恢复的工具失败』，不计失败轮。" ;;
esac

echo "== 7) 上一轮诊断层告警 (守卫AW: 工具级失败只落在 lastDiagnostics，无通知出口) =="
DIAG="$(sqlite3 "$DB" "SELECT ifnull(json_extract(state_json,'$.lastDiagnosticSummary'),'') FROM cron_jobs WHERE job_id='$JOB';" 2>/dev/null)"
if [ -n "$DIAG" ]; then echo "WARN 上一轮存在诊断告警: $DIAG"; else echo "OK: 上一轮无诊断告警"; fi
