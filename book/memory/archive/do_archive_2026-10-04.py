#!/usr/bin/env python3
# 归档脚本 2026-10-04 · 归档 9/19、9/20 两个缝合区块
# 安全三条件（运行规则4）：①校验输入完整 ②原子写入 ③备份只在不存在时创建
# 路径基于 __file__ 推导（守卫十六），不依赖 cwd。
import os, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))          # book/memory/archive
MEM = os.path.normpath(os.path.join(BASE, "..", "..", "MEMORY.md"))
ARCHIVE = os.path.join(BASE, "stitching-archive-through-2026-09-20.md")
BACKUP = os.path.join(BASE, "MEMORY-backup-2026-10-04.md")

START = "## 2026-09-20 Dreaming知识串联"
END = "## 2026-07-12 系统性教训"

with open(MEM, "r", encoding="utf-8") as f:
    text = f.read()

size_before = len(text.encode("utf-8"))
# ①校验输入完整
assert size_before > 100000, f"输入过小，中止: {size_before}B"
assert START in text, "缺少起始标记 9/20，中止"
assert END in text, "缺少结束标记 7/12 系统性教训，中止"
assert "## 2026-10-04 Dreaming知识串联" in text, "缺少 10/04 缝合区，中止"

i = text.index(START)
j = text.index(END)
section = text[i:j]
assert "## 2026-09-19 Dreaming知识串联" in section, "9/19 区块不在待归档范围内，中止"

new = text[:i] + text[j:]
size_after = len(new.encode("utf-8"))
assert size_after < size_before, "归档后未减小，中止"

# ③备份只在不存在时创建
if not os.path.exists(BACKUP):
    shutil.copy2(MEM, BACKUP)
    print(f"backup created: {BACKUP}")

# 追加到归档文件
with open(ARCHIVE, "a", encoding="utf-8") as f:
    f.write(section)
    print(f"archive appended: {ARCHIVE} (+{len(section.encode('utf-8'))}B)")

# ②原子写入
tmp = MEM + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    f.write(new)
os.replace(tmp, MEM)

print(f"MEMORY.md: {size_before} -> {size_after}B")
