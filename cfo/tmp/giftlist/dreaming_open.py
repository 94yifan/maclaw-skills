#!/usr/bin/env python3
"""dreaming_open.py — 守卫AA/AN 落地：一条命令完成 date + MEMORY 占位区块 + dreaming 骨架。

用法: python3 cfo/tmp/giftlist/dreaming_open.py [YYYY-MM-DD]
不传日期则取本机当日（Asia/Shanghai 由系统时区决定）。

设计要点（守卫L）: 所有路径由 __file__ 推导，不依赖 cwd。
幂等: 当日区块/骨架已存在则不重复写。
"""
import datetime
import pathlib
import re
import subprocess
import sys

CFO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # .../cfo
MEMORY = CFO_ROOT / "MEMORY.md"
MEM_DIR = CFO_ROOT / "memory"
ARCHIVER = CFO_ROOT / "tmp" / "giftlist" / "memory_archive.py"
PRECHECK_BYTES = 130_000  # 留 1KB 余量：本节骨架 + 当日区块约 250-400B


def today_str() -> str:
    """只接受严格 YYYY-MM-DD；其余参数一律忽略并回落本机当日。

    守卫A1（2026-10-22）: 原实现把 sys.argv[1] 直接当日期，跑 `--help` 会生成
    `## --help` 区块与 `memory/dreaming---help.md`。骨架脚本是全轮第一个写动作，
    它一旦能写脏数据，守卫AA 的"先落盘"就会先把噪声写进唯一自动加载文件。
    """
    if len(sys.argv) > 1:
        cand = sys.argv[1].strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", cand):
            try:
                datetime.date.fromisoformat(cand)
                return cand
            except ValueError:
                pass
        if cand in ("-h", "--help"):
            print(__doc__)
            raise SystemExit(0)
        print(f"WARN: 忽略非法日期参数 {cand!r}，回落本机当日", file=sys.stderr)
    return datetime.datetime.now().strftime("%Y-%m-%d")


def ensure_memory_block(today: str) -> str:
    text = MEMORY.read_text()
    if f"## {today}" in text:
        return "exists"
    block = f"""
## {today}【骨架先写，守卫AA/AN】

- **交互判定（待填）**：session 目录巡检结果待填。
- **实测快照（待填）**。
- **cron 实读（待填）**。
- **A/B/C/D 全文见 `memory/dreaming-{today}.md`**。
"""
    MEMORY.write_text(text.rstrip("\n") + "\n" + block)
    return "appended"


def ensure_dreaming_skeleton(today: str) -> str:
    MEM_DIR.mkdir(parents=True, exist_ok=True)
    f = MEM_DIR / f"dreaming-{today}.md"
    if f.exists():
        return "exists"
    f.write_text(
        f"# Dreaming {today}\n\n"
        "- 交互：待填（session 目录巡检）\n"
        "- 礼单：待填（audit.py）\n"
        "- cron：待填\n"
        "- A/B/C/D：待填\n"
    )
    return "created"


def main() -> int:
    today = today_str()

    # 守卫AI/AH 前置：写入前先量体量，越线先归档再写（不等到收尾第 0 步）。
    # 依据 10/22 D2 —— 检查在写之后只告警，等于让越界态存在于两轮之间；
    # 若本轮中途被 gateway restart 打断，下一轮 startups 仍要读超限文件。
    if MEMORY.exists() and MEMORY.stat().st_size > PRECHECK_BYTES and ARCHIVER.exists():
        size_before = MEMORY.stat().st_size
        print(f"PRECHECK: MEMORY.md {size_before} bytes > {PRECHECK_BYTES}，先归档再写")
        rc = subprocess.run(
            [sys.executable, str(ARCHIVER), "--apply", "--tier2", "--today", today],
            capture_output=True, text=True,
        ).returncode
        size_after = MEMORY.stat().st_size
        print(f"PRECHECK: memory_archive.py rc={rc} | {size_before} → {size_after} bytes")
        if rc != 0:
            print("WARN: 归档器返回非 0，继续写入（收尾第 0 步会重试）", file=sys.stderr)

    m = ensure_memory_block(today)
    d = ensure_dreaming_skeleton(today)
    size = MEMORY.stat().st_size
    print(f"TODAY={today}")
    print(f"MEMORY 区块: {m} | {MEMORY} ({size} bytes)")
    print(f"dreaming 骨架: {d} | {MEM_DIR / ('dreaming-' + today + '.md')}")
    if size > 131072:
        print("WARN: MEMORY.md 已超 128KB，收尾第 0 步将触发归档")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
