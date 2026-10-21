#!/usr/bin/env python3
"""dreaming_open.py — 守卫AA/AN 落地：一条命令完成 date + MEMORY 占位区块 + dreaming 骨架。

用法: python3 cfo/tmp/giftlist/dreaming_open.py [YYYY-MM-DD]
不传日期则取本机当日（Asia/Shanghai 由系统时区决定）。

设计要点（守卫L）: 所有路径由 __file__ 推导，不依赖 cwd。
幂等: 当日区块/骨架已存在则不重复写。
"""
import datetime
import pathlib
import sys

CFO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # .../cfo
MEMORY = CFO_ROOT / "MEMORY.md"
MEM_DIR = CFO_ROOT / "memory"


def today_str() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
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
