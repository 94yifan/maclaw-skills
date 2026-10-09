#!/usr/bin/env python3
"""MEMORY.md 体量归档器（守卫AH 阈值 + 守卫AI 可执行动作落地）

触发：MEMORY.md 字节数 > THRESHOLD（默认 131072 = 128KB）
目标：降到 TARGET（默认 120000）以下，留足余量
      （承 10/07 教训：不能只降到「刚好不越界」，次日必再超 = 没修）

安全红线（by construction，宁可少迁、绝不误迁）：
  只迁出整块「零交互日 / 断档」区块；块标题或正文出现守卫定义标记即整块跳过。
  定义标记 = 正则 \\*\\*守卫[A-Z]{1,2}（  或 标题含 守卫[A-Z]{1,2}（  或 正文含「写入即为生效」。
  当日区块（TODAY）永不迁出。

用法：
  python3 memory_archive.py                 # dry-run（默认，只打印计划）
  python3 memory_archive.py --apply         # 实际执行
  python3 memory_archive.py --file X --threshold N --target M --today YYYY-MM-DD   # 测试用
退出码：0=无需归档或成功；2=出错（不改文件）
"""
import re
import sys
import pathlib
import datetime
import shutil

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3]                                    # .../workspace
DEFAULT_MEM = ROOT / "cfo" / "MEMORY.md"
ARCH = ROOT / "cfo" / "memory" / "archive"
THRESHOLD = 131072
TARGET = 120000

DEF_BODY = re.compile(r"\*\*守卫[A-Z]{1,2}（")
DEF_TITLE = re.compile(r"守卫[A-Z]{1,2}（")
PROTECT_TITLES = ("身份", "yifan 本人", "客户结算规则", "审核汇报偏好",
                  "核心客户礼单", "配置状态", "返点核算数据")
ARCHIVABLE_KW = ("零交互日", "断档")


def argval(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        return sys.argv[i + 1]
    return default


def split_blocks(text):
    out, cur_title, cur = [], None, []
    for ln in text.splitlines(keepends=True):
        if ln.startswith("## "):
            out.append((cur_title, "".join(cur)))
            cur_title, cur = ln.rstrip("\n"), [ln]
        else:
            cur.append(ln)
    out.append((cur_title, "".join(cur)))
    return out


def extract_date(title):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", title)
    return m.group(0) if m else None


def is_archivable(title, body, today):
    if not title or not title.startswith("## "):
        return False
    core = title[3:]
    if any(p in core for p in PROTECT_TITLES):
        return False
    if not any(k in core for k in ARCHIVABLE_KW):
        return False
    if extract_date(core) is None:
        return False
    if today and extract_date(core) == today:      # 当日区块永不迁出
        return False
    if DEF_TITLE.search(core):                     # 标题含守卫定义 -> 受保护
        return False
    if DEF_BODY.search(body):                      # 正文含守卫定义 -> 受保护
        return False
    if "写入即为生效" in body:                       # 定义强信号 -> 受保护
        return False
    if "归档指针" in body:                          # 已处理过 -> 跳过
        return False
    return True


def main():
    apply = "--apply" in sys.argv
    mem = pathlib.Path(argval("--file", str(DEFAULT_MEM)))
    threshold = int(argval("--threshold", THRESHOLD))
    target = int(argval("--target", TARGET))
    today = argval("--today", datetime.date.today().isoformat())

    if not mem.exists():
        print("FAIL: MEMORY.md 不存在")
        return 2
    raw = mem.read_text(encoding="utf-8")
    size = len(raw.encode("utf-8"))
    print(f"MEMORY.md: {size} bytes (threshold={threshold}, target={target}, today={today})")
    if size <= threshold:
        print("OK: 未超阈值，无需归档")
        return 0

    blocks = split_blocks(raw)
    cands = [(extract_date(t[3:]), i, t, b) for i, (t, b) in enumerate(blocks)
             if t and is_archivable(t, b, today)]
    cands.sort(key=lambda x: (x[0], x[1]))
    print(f"可归档区块 {len(cands)} 个：{[c[0] for c in cands]}")

    need = size - target
    moved, freed = [], 0
    for d, i, t, b in cands:
        if freed >= need:
            break
        moved.append((d, i, t, b))
        freed += len(b.encode("utf-8"))
    if not moved:
        print("WARN: 无符合安全条件的可归档区块，体积未减（红线保护块不迁出）")
        return 0

    d0, d1 = moved[0][0], moved[-1][0]
    tag = f"2026-{d0[5:7]}{d0[8:10]}_{d1[5:7]}{d1[8:10]}"
    arc_path = ARCH / f"MEMORY-log-{tag}.md"
    if arc_path.exists():
        arc_path = ARCH / f"MEMORY-log-{tag}_{datetime.datetime.now():%H%M%S}.md"
    pointer = (f"- **[归档指针 {d0}~{d1}]** 已迁出至 "
               f"`cfo/memory/archive/{arc_path.name}`（守卫AH/守卫AI 自动归档）\n\n")

    moved_idx = {m[1] for m in moved}
    new_text = "".join(pointer if i in moved_idx else b
                       for i, (t, b) in enumerate(blocks))
    new_size = len(new_text.encode("utf-8"))
    print(f"计划迁出 {len(moved)} 块 -> {arc_path.name}")
    print(f"预计 {size} -> {new_size} bytes (freed≈{freed})")
    if not apply:
        print("DRY-RUN：未改文件。加 --apply 执行。")
        return 0

    shutil.copy2(mem, f"/tmp/cfo_MEMORY_prearchive_{today}.md")
    ARCH.mkdir(parents=True, exist_ok=True)
    with arc_path.open("a", encoding="utf-8") as f:
        f.write(f"\n<!-- 归档 {datetime.datetime.now():%Y-%m-%d %H:%M:%S}，"
                f"memory_archive.py 迁出 -->\n")
        for d, i, t, b in moved:
            f.write(b)
    mem.write_text(new_text, encoding="utf-8")
    print(f"APPLIED: {size} -> {new_size} bytes；归档 {arc_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
