#!/usr/bin/env python3
# Dreaming 2026-09-15 归档动作：把 2026-08-20 之前的 Dreaming 串联条目移出 MEMORY.md，
# 保留近 30 天 + 全部方法论条目（含可复用框架/教训/协议）。
# 安全措施：先校验输入完整，再原子写入（临时文件 + rename），绝不先截断目标文件。
import re, os, shutil, datetime, sys

WS = "/Users/yifansmacmini/.openclaw/workspace/book"
MEM = os.path.join(WS, "MEMORY.md")
ARCH_DIR = os.path.join(WS, "memory", "archive")
ARCH = os.path.join(ARCH_DIR, "stitching-archive-through-2026-08-15.md")
BACKUP = os.path.join(ARCH_DIR, "MEMORY-backup-2026-09-15.md")

CUTOFF = datetime.date(2026, 8, 16)

# 显式保留的最早期方法论条目日期（协议方法论期 6/23-7/09 + 读书方法论期 7/12-7/14
# + 等待协议方法论期 7/15-7/21）。其余 <CUTOFF 的串联条目归档。
KEEP_DATES = {
    "2026-06-23", "2026-06-24", "2026-06-25", "2026-06-26", "2026-06-27",
    "2026-06-28", "2026-06-29", "2026-06-30", "2026-07-03", "2026-07-09",
    "2026-07-12", "2026-07-13", "2026-07-14",
    "2026-07-15", "2026-07-17", "2026-07-19", "2026-07-20", "2026-07-21",
}

with open(MEM, encoding="utf-8") as f:
    raw = f.read()

# 输入完整性校验：内容过小或缺缝合区则中止，避免在已被截断的文件上再操作
if len(raw.encode("utf-8")) < 100_000 or "## 知识缝合区" not in raw:
    sys.exit("ABORT: MEMORY.md looks truncated/unsafe (size=%d)" % len(raw.encode("utf-8")))

lines = raw.splitlines(keepends=True)

start = next(i for i, l in enumerate(lines) if l.startswith("## 知识缝合区"))
prefix, body = lines[:start], lines[start:]

sec_starts = [i for i, l in enumerate(body)
              if re.match(r"^#{2,3} (20\d\d-\d\d-\d\d|知识缝合区|E\.|F\.)", l)]
sec_starts.append(len(body))
sections = [body[a:b] for a, b in zip(sec_starts, sec_starts[1:])]

keep, archive = [], []
for sec in sections:
    text = "".join(sec)
    m = re.search(r"(20\d\d-\d\d-\d\d)", sec[0]) if sec and sec[0] else None
    if m:
        ds = m.group(1)
        d = datetime.date.fromisoformat(ds)
        if d < CUTOFF and ds not in KEEP_DATES:
            archive.append(sec)
            continue
    keep.append(sec)

def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)

if not os.path.exists(BACKUP):
    shutil.copy2(MEM, BACKUP)

atomic_write(MEM, "".join(prefix + [l for sec in keep for l in sec]))

arch_head = (
    "# MEMORY.md 归档 · 旧 Dreaming 串联条目\n\n"
    "归档时间：2026-09-15 Dreaming。触发规则：MEMORY.md 顶部『运行规则』第 2 条（超 150KB 归档旧缝合区）。\n"
    "归档范围：2026-08-16 之前的 Dreaming 串联条目（保留近 30 天 + 方法论条目），方法论条目除外（已在 MEMORY.md 保留）。\n"
    "说明：保留项 = 2026-08-16 起的全部串联 + 6/23-7/21 的方法论簇（协议生命周期/零数据诊断梯/推理根因/等待协议）。\n"
    "原件备份：MEMORY-backup-2026-09-15.md（备份文件按需，若不存在则用 MEMORY-backup-2026-09-14.md）。\n\n---\n\n"
)
atomic_write(ARCH, arch_head + "".join([l for sec in archive for l in sec]))

print("original bytes:", len(raw.encode("utf-8")))
print("new MEMORY bytes:", os.path.getsize(MEM))
print("archive bytes:", os.path.getsize(ARCH))
print("kept sections:", len(keep), "| archived sections:", len(archive))
print("kept dates:", [re.search(r"20\d\d-\d\d-\d\d", s[0]).group(0) for s in keep if s and s[0] and re.search(r"20\d\d-\d\d-\d\d", s[0])])
print("archived dates:", [re.search(r"20\d\d-\d\d-\d\d", s[0]).group(0) for s in archive if s and s[0] and re.search(r"20\d\d-\d\d-\d\d", s[0])])
