#!/bin/bash
# BM run-status reader — 读 cron 运行记录，永不非零退出
# 背景：2026-10-18 / 10-19 / 10-21 三次跑因「读数命令失败」被标记 error，产物写完了但复盘没送达。
# 处置：所有读数收敛到一个脚本，任何一步失败都回退成 NA，退出码恒 0（守卫二十一：无消费者的读数不拦交付）。
set +e
DB="$HOME/.openclaw/state/openclaw.sqlite"
JOB="218d4b80"
SQL="select seq,datetime(ts/1000,'unixepoch','+8 hours') as t,status,duration_ms,delivery_status,delivered,substr(coalesce(error,''),1,50) from cron_run_logs where job_id like '${JOB}%' order by seq desc limit 8;"

OUT=$(sqlite3 -cmd ".timeout 8000" "$DB" "$SQL" 2>/dev/null)
if [ -z "$OUT" ]; then
  OUT=$(sqlite3 -cmd ".timeout 8000" "$DB" "select seq,status from cron_run_logs order by seq desc limit 3;" 2>/dev/null)
  [ -z "$OUT" ] && OUT="NA  (db 不可读或表结构变动)"
fi

echo "== BM cron ($JOB) 近 8 跑 =="
echo "$OUT"
echo "== 全期 =="
sqlite3 -cmd ".timeout 8000" "$DB" "select count(*)||' 跑 / '||sum(status='ok')||' ok / '||sum(status='error')||' error' from cron_run_logs where job_id like '${JOB}%';" 2>/dev/null || echo "NA"
exit 0
