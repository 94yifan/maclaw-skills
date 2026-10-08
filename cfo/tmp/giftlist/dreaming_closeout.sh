#!/usr/bin/env bash
# dreaming 收尾脚本（守卫AF / 守卫Y 四态 / 守卫AE / 守卫N 自证）
# 顺序固定：全部写动作 -> add -> commit -> 工作区必须空 -> push -> 远端 tip 三态取证
# 用法: bash dreaming_closeout.sh YYYY-MM-DD "commit message"
set -u
REPO="/Users/yifansmacmini/.openclaw/workspace"
TODAY="${1:?usage: dreaming_closeout.sh YYYY-MM-DD \"msg\"}"
MSG="${2:-cfo dreaming $TODAY}"
cd "$REPO" || { echo "FAIL: cannot cd $REPO"; exit 1; }

echo "== 0) MEMORY.md 体量检查 (守卫AH: 超 128KB 即 WARN+归档) =="
MEMB="$(wc -c < cfo/MEMORY.md | tr -d ' ')"
MEML="$(wc -l < cfo/MEMORY.md | tr -d ' ')"
echo "MEMORY.md: ${MEMB} bytes / ${MEML} lines"
if [ "$MEMB" -gt 131072 ]; then
  echo "WARN: MEMORY.md 超 128KB 上限 (${MEMB}B) -> 需归档最早的零交互日区块到 cfo/memory/archive/ （守卫定义块与业务规则块不得迁出）"
else
  echo "OK: MEMORY.md 在 128KB 以内"
fi

echo "== 0b) pending.json 校验 (守卫AJ) =="
if [ -f cfo/tmp/giftlist/pending.json ]; then
  python3 -c "import json;d=json.load(open('cfo/tmp/giftlist/pending.json'));print('pending.json OK:',len([i for i in d['items'] if i.get('status')=='open']),'open')" 2>&1 || echo "WARN: pending.json 解析失败"
else
  echo "WARN: pending.json 缺失（守卫AJ 落地项）"
fi

echo "== 1) staged (cfo paths) =="
git add "cfo/MEMORY.md" "cfo/memory/dreaming-$TODAY.md" 2>/dev/null
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
