#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容壳：多关键字一次遍历查询已并入 rec_api.py 的 findmany 命令。
保留此文件是为了让 9/17 之前的调用方式
`python3 tmp/giftlist/findmany.py kw1 kw2` 继续可用，避免两份实现漂移。
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call(
    [sys.executable, os.path.join(HERE, "rec_api.py"), "findmany"] + sys.argv[1:]))
