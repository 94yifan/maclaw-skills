#!/usr/bin/env python3
"""交付落盘器（守卫AR / 守卫B4）

一条命令完成两件事，绑在「交付」这个动作上，不依赖记忆：
  1. 复制交付物到 ~/Documents/cfo-deliverables/<date>/（仓库外，不进远端）
  2. 追加一行到 cfo/memory/<date>.md（时间 / 文件 / 说明）

用法:
  python3 deliver_log.py <file> [<file> ...] --note "用途说明"
  python3 deliver_log.py --self-test
"""
import argparse
import datetime as dt
import hashlib
import os
import shutil
import sys
import tempfile

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../workspace/cfo
DELIV_ROOT = os.path.expanduser("~/Documents/cfo-deliverables")
TZ = dt.timezone(dt.timedelta(hours=8))


def md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def today():
    return dt.datetime.now(TZ).strftime("%Y-%m-%d")


def log_line(day, note, names, memory_dir=None):
    path = os.path.join(memory_dir or os.path.join(AGENT_DIR, "memory"), f"{day}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    stamp = dt.datetime.now(TZ).strftime("%H:%M")
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"# {day}\n\n")
        f.write(f"- {stamp} 交付：{'、'.join(names)}（{note}）\n")
    return path


def deliver(files, note, deliv_root=None, memory_dir=None):
    day = today()
    outdir = os.path.join(deliv_root or DELIV_ROOT, day)
    os.makedirs(outdir, exist_ok=True)
    done = []
    for src in files:
        src = os.path.abspath(os.path.expanduser(src))
        if not os.path.isfile(src):
            print(f"FAIL: 文件不存在 {src}")
            return 1
        size = os.path.getsize(src)
        if size == 0:
            print(f"FAIL: 空文件 {src}")
            return 1
        dst = os.path.join(outdir, os.path.basename(src))
        if os.path.abspath(dst) != src:
            shutil.copy(src, dst)
        if os.path.getsize(dst) != size or md5(dst) != md5(src):
            print(f"FAIL: 复制校验不一致 {dst}")
            return 1
        done.append((os.path.basename(src), size, md5(src)))
    log = log_line(day, note, [d[0] for d in done], memory_dir=memory_dir)
    for name, size, digest in done:
        print(f"OK {name} {size}B md5={digest[:12]} -> {outdir}")
    print(f"LOGGED {log}")
    return 0


def self_test():
    """自测全程走临时目录，绝不触碰真实 memory/ 与 cfo-deliverables/。
    （10/20 修复：旧版直接调 deliver() 写真实路径，只删日志行不删文件，
      留下 `# <date>` 空壳，使「当日 memory 存在」这一存在性信号失真。）"""
    tmp = tempfile.mkdtemp()
    deliv_root = os.path.join(tmp, "deliverables")
    mem_dir = os.path.join(tmp, "memory")
    os.makedirs(mem_dir, exist_ok=True)
    src = os.path.join(tmp, "自测样张.txt")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write("deliver_log self test\n")
    rc = deliver([src], "自测，勿当交付", deliv_root=deliv_root, memory_dir=mem_dir)
    if rc != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        return rc
    day = today()
    log = os.path.join(mem_dir, f"{day}.md")
    body = open(log, encoding="utf-8").read()
    dst = os.path.join(deliv_root, day, "自测样张.txt")
    ok = ("自测，勿当交付" in body) and os.path.exists(dst) and md5(dst) == md5(src)
    shutil.rmtree(tmp, ignore_errors=True)
    if not ok:
        print("FAIL: 自测校验不通过（日志行或副本缺失/不一致）")
        return 1
    real_log = os.path.join(AGENT_DIR, "memory", f"{day}.md")
    if os.path.exists(real_log):
        print(f"WARN: 真实日志已存在且未被触碰 {real_log}")
    print("SELFTEST OK（全程临时目录，真实 memory/ 与 cfo-deliverables/ 未被写入）")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--note", default="交付")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    sys.exit(self_test() if a.self_test else deliver(a.files, a.note))
