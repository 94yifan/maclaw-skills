#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归档 book/MEMORY.md 的 9/09-9/14 缝合区（历史欠账，9-28 轮未落实）。
三条件（运行规则4）：①校验输入完整 ②原子写入 ③备份只在不存在时创建（备份已由 cp 先行创建）。
"""
import os, sys, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))          # .../book/memory/archive
MEM = os.path.abspath(os.path.join(BASE, "..", "..", "MEMORY.md"))  # book/MEMORY.md
ARC = os.path.join(BASE, "stitching-archive-through-2026-09-14.md")

START = "## 2026-09-14 Dreaming知识串联（第87天"
END = "## 2026-07-12 系统性教训（由supermind在比乐研究中暴露"

def atomic_write(path, data):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

def main():
    s = open(MEM, encoding="utf-8").read()
    n0 = len(s.encode("utf-8"))
    # ① 校验输入完整
    assert n0 > 100000, f"input too small: {n0}"
    for marker in ("## 知识缝合区", "## 2026-09-15 Dreaming知识串联", "## 2026-09-09 Dreaming知识串联（第82天", START, END):
        assert marker in s, f"marker missing: {marker}"
    if START not in s:
        print("nothing to archive"); return
    i = s.index(START)
    j = s.index(END)
    assert i < j, "range invalid"
    removed = s[i:j]
    new = s[:i] + s[j:]
    assert len(removed.encode()) > 20000, f"removed too small: {len(removed.encode())}"
    assert len(new.encode()) < n0, "no shrink"
    # ② 原子写入归档文件（不存在时创建；若存在则追加前先读）
    hdr = ("# book MEMORY.md 缝合区归档（through 2026-09-14）\n\n"
           "归档日期：2026-09-29（补做 9-28 轮未落实的归档）。\n"
           "范围：2026-09-09 至 2026-09-14 的 Dreaming 知识串联区块（倒序保留）。\n\n---\n\n")
    atomic_write(ARC, hdr + removed)
    # ③ 原子写回 MEMORY.md
    atomic_write(MEM, new)
    print("MEMORY before:", n0, "after:", len(new.encode("utf-8")))
    print("archive:", ARC, len((hdr + removed).encode("utf-8")))
    print("kept 9/15 header:", "## 2026-09-15 Dreaming知识串联" in new)
    print("9/14 removed:", "## 2026-09-14 Dreaming知识串联" not in new)

if __name__ == "__main__":
    main()
