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
  python3 memory_archive.py --apply         # 实际执行（一级：整块迁出零交互日）
  python3 memory_archive.py --apply --tier2 # 超阈值且一级无可迁块时，二级：迁出旧块的业务条目
  python3 memory_archive.py --file X --threshold N --target M --today YYYY-MM-DD   # 测试用
  python3 memory_archive.py --tier2 --min-age 14 --force-plan   # 只出计划：二级归档最小块龄（默认30天）
退出码：0=无需归档或成功；2=出错（不改文件）

二级归档（--tier2）红线：
  只处理日期早于 today-30 天的区块；逐条 bullet 迁移，
  含守卫定义标记（**守卫X（ / 写入即为生效）的 bullet 永不迁出；
  块标题保留，迁出后在原位留一行指针。守卫定义命中数前后必须相等。
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
TIER2_MIN_AGE_DAYS = 30
GUARD_LINE = re.compile(r"\*\*守卫[A-Z]{1,2}（|写入即为生效|守卫[A-Z]{1,2}（")


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


def guard_count(text):
    return len(GUARD_LINE.findall(text))


def tier2_plan(raw, today, need, min_age=TIER2_MIN_AGE_DAYS):
    """逐条迁移旧块的非守卫 bullet。返回 (new_text, arc_chunks, moved_dates, freed)。"""
    blocks = split_blocks(raw)
    today_d = datetime.date.fromisoformat(today) if today else datetime.date.today()
    arc_chunks, moved_dates, freed = [], [], 0
    out = []

    for t, b in blocks:
        if not t or not t.startswith("## "):
            out.append(b)
            continue
        core = t[3:]
        d = extract_date(core)
        if (d is None or any(p in core for p in PROTECT_TITLES)
                or d == today or (today_d - datetime.date.fromisoformat(d)).days < min_age
                or "归档指针" in b):
            out.append(b)
            continue

        lines = b.splitlines(keepends=True)
        head = lines[0] if lines else ""
        keep, moved = [head], []
        for ln in lines[1:]:
            if ln.startswith("- ") and not GUARD_LINE.search(ln) and freed < need:
                moved.append(ln)
                freed += len(ln.encode("utf-8"))
            else:
                keep.append(ln)
        if not moved:
            out.append(b)
            continue
        moved_dates.append(d)
        arc_chunks.append((d, "".join(moved)))
        keep.append(f"- **[条目归档 {d}]** 本块 {len(moved)} 条已迁出至 "
                    f"`cfo/memory/archive/MEMORY-bullets-{d[:7]}.md`（守卫AI 二级归档）\n")
        out.append("".join(keep))

    return "".join(out), arc_chunks, moved_dates, freed



def self_test() -> int:
    """隔离自测：临时目录完整跑一遍 tier2，断言真实归档零变化（守卫BD 判据）。"""
    import hashlib
    import subprocess
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="memarch_selftest_"))
    mem = tmp / "MEMORY.md"
    shutil.copy2(DEFAULT_MEM, mem)
    before_src = len(mem.read_bytes())
    real_before = {p.name: hashlib.md5(p.read_bytes()).hexdigest()
                   for p in ARCH.glob("*.md")} if ARCH.exists() else {}
    rc = subprocess.run([sys.executable, str(HERE), "--apply", "--tier2",
                         "--min-age", "14", "--threshold", "1", "--file", str(mem)],
                        capture_output=True, text=True).returncode
    tmp_arch = tmp / "memory" / "archive"
    made = sorted(p.name for p in tmp_arch.glob("*.md")) if tmp_arch.exists() else []
    after_src = len(mem.read_bytes())
    real_after = {p.name: hashlib.md5(p.read_bytes()).hexdigest()
                  for p in ARCH.glob("*.md")} if ARCH.exists() else {}
    checks = [
        ("子进程 rc=0", rc == 0),
        ("临时目录产出归档文件", len(made) > 0),
        ("MEMORY 字节下降", after_src < before_src),
        ("真实归档零变化", real_before == real_after),
    ]
    for name, ok in checks:
        print(("OK  " if ok else "FAIL") + f" {name}")
    print(f"   src {before_src} -> {after_src}；tmp archive={made}；real archive={sorted(real_after)}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if all(ok for _, ok in checks) else 1


def main():
    if "--self-test" in sys.argv:
        raise SystemExit(self_test())
    apply = "--apply" in sys.argv
    tier2 = "--tier2" in sys.argv
    mem = pathlib.Path(argval("--file", str(DEFAULT_MEM)))
    # 守卫BD 前置（A1 修复）：--file 只隔离 MEMORY 路径、归档目录仍指真实路径，
    # 2026-10-27 一次隔离测试因此污染了真实 memory/archive/。归档目录一律随 MEMORY 推导。
    global ARCH
    if "--archive-dir" in sys.argv:
        ARCH = pathlib.Path(argval("--archive-dir", str(ARCH)))
    elif "--file" in sys.argv:
        ARCH = mem.parent / "memory" / "archive"
    threshold = int(argval("--threshold", THRESHOLD))
    target = int(argval("--target", TARGET))
    today = argval("--today", datetime.date.today().isoformat())

    if not mem.exists():
        print("FAIL: MEMORY.md 不存在")
        return 2
    raw = mem.read_text(encoding="utf-8")
    size = len(raw.encode("utf-8"))
    print(f"MEMORY.md: {size} bytes (threshold={threshold}, target={target}, today={today})")
    min_age = int(argval("--min-age", str(TIER2_MIN_AGE_DAYS)))
    if size <= threshold and "--force-plan" not in sys.argv:
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
        print("WARN: 无符合安全条件的可归档区块（一级）")
        if not tier2:
            print("提示：可加 --tier2 走二级归档（迁出旧块业务条目，守卫行不动）")
            return 0
        new_text, chunks, dates, freed2 = tier2_plan(raw, today, need, min_age)
        if not chunks:
            print("WARN: 二级亦无可迁条目，体积未减（红线保护块不迁出）")
            return 0
        before, after = guard_count(raw), guard_count(new_text)
        new_size = len(new_text.encode("utf-8"))
        print(f"二级计划：{len(dates)} 块 / {sum(c[1].count(chr(10)) for c in chunks)} 行 -> "
              f"{size} → {new_size} bytes (freed≈{freed2})；守卫定义 {before} → {after}")
        if before != after:
            print("FAIL: 守卫定义命中数变化，拒绝写入")
            return 2
        if not apply:
            print("DRY-RUN：未改文件。加 --apply 执行。")
            return 0
        shutil.copy2(mem, f"/tmp/cfo_MEMORY_prearchive_{today}.md")
        ARCH.mkdir(parents=True, exist_ok=True)
        by_month = {}
        for d, chunk in chunks:
            by_month.setdefault(d[:7], []).append((d, chunk))
        for mon, items in by_month.items():
            p = ARCH / f"MEMORY-bullets-{mon}.md"
            with p.open("a", encoding="utf-8") as f:
                f.write(f"\n<!-- 二级归档 {datetime.datetime.now():%Y-%m-%d %H:%M:%S} -->\n")
                for d, chunk in items:
                    f.write(f"\n### {d}\n\n{chunk}")
        mem.write_text(new_text, encoding="utf-8")
        print(f"APPLIED(二级): {size} -> {new_size} bytes；归档目录 {ARCH}")
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
