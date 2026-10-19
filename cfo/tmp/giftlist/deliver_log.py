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


def log_line(day, note, names):
    path = os.path.join(AGENT_DIR, "memory", f"{day}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    stamp = dt.datetime.now(TZ).strftime("%H:%M")
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"# {day}\n\n")
        f.write(f"- {stamp} 交付：{'、'.join(names)}（{note}）\n")
    return path


def deliver(files, note):
    day = today()
    outdir = os.path.join(DELIV_ROOT, day)
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
    log = log_line(day, note, [d[0] for d in done])
    for name, size, digest in done:
        print(f"OK {name} {size}B md5={digest[:12]} -> {outdir}")
    print(f"LOGGED {log}")
    return 0


def self_test():
    tmp = tempfile.mkdtemp()
    f = os.path.join(tmp, "自测样张.txt")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("deliver_log self test\n")
    rc = deliver([f], "自测，勿当交付")
    if rc != 0:
        return rc
    day = today()
    log = os.path.join(AGENT_DIR, "memory", f"{day}.md")
    lines = [l for l in open(log, encoding="utf-8") if "自测，勿当交付" not in l]
    open(log, "w", encoding="utf-8").writelines(lines)
    shutil.rmtree(os.path.join(DELIV_ROOT, day, ""), ignore_errors=False) if False else None
    dst = os.path.join(DELIV_ROOT, day, "自测样张.txt")
    if os.path.exists(dst):
        os.remove(dst)
    print("SELFTEST OK（日志行与样张已回收）")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--note", default="交付")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    sys.exit(self_test() if a.self_test else deliver(a.files, a.note))
