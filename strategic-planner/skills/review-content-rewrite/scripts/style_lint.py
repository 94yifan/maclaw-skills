#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
style_lint.py — 输出风格检查器（零AI味检测）

用法:
  python3 style_lint.py <文件路径>
  python3 style_lint.py --text "文本内容"
  echo "文本" | python3 style_lint.py

检查规则:
  ERROR — 概念性引号字符: 「 」 『 』 " " ' '
  ERROR — 装饰性破折号: ——（连续两个 em dash U+2014）
  WARN  — AI高频词: 整体而言 / 从某种意义上说 / 本质上 / 一以蔽之 / 撬动 / 赋能 / 抓手 / 放大器 / 核心是 / 闭环
"""

import sys
import re

# ── 违规字符表 ──────────────────────────────────────────
# 概念性引号（Unicode 各种引号，出现在强调语境即违规）
ERROR_QUOTES = [
    '\u300c',  # 「
    '\u300d',  # 」
    '\u300e',  # 『
    '\u300f',  # 』
    '\u201c',  # "
    '\u201d',  # "
    '\u2018',  # '
    '\u2019',  # '
]

# 装饰性破折号：连续两个 em dash
EM_DASH = '\u2014'  # —

# ── AI 高频词表 ──────────────────────────────────────────
AI_WORDS = [
    '整体而言',
    '从某种意义上说',
    '本质上',
    '一以蔽之',
    '撬动',
    '赋能',
    '抓手',
    '放大器',
    '核心是',
    '闭环',
]


def lint(text: str) -> list:
    """返回违规列表，每项格式: (行号, 级别, 类型, 片段)"""
    violations = []
    lines = text.split('\n')

    for i, line in enumerate(lines, start=1):
        # ── ERROR: 概念性引号 ──
        for ch in ERROR_QUOTES:
            if ch in line:
                idx = line.index(ch)
                snippet = _snippet(line, idx)
                violations.append((i, 'ERROR', '概念性引号', snippet))

        # ── ERROR: 装饰性破折号（连续两个 em dash）──
        double_dash = EM_DASH + EM_DASH
        pos = 0
        while double_dash in line[pos:]:
            idx = line.index(double_dash, pos)
            snippet = _snippet(line, idx)
            violations.append((i, 'ERROR', '装饰性破折号', snippet))
            pos = idx + 2

        # ── WARN: AI 高频词 ──
        for word in AI_WORDS:
            if word in line:
                idx = line.index(word)
                snippet = _snippet(line, idx)
                violations.append((i, 'WARN', f'AI高频词「{word}」', snippet))

    return violations


def _snippet(line: str, idx: int, pad: int = 15) -> str:
    """截取违规位置附近的文本片段"""
    start = max(0, idx - pad)
    end = min(len(line), idx + pad + 5)
    s = line[start:end]
    if start > 0:
        s = '…' + s
    if end < len(line):
        s = s + '…'
    return s.strip()


def format_report(violations: list) -> str:
    """格式化输出报告"""
    if not violations:
        return 'PASS: 未检测到AI味违规'

    lines_out = []
    for line_no, level, vtype, snippet in violations:
        tag = f'[{level}]'
        lines_out.append(f'{tag} 行{line_no} {vtype} | {snippet}')

    n_err = sum(1 for v in violations if v[1] == 'ERROR')
    n_warn = sum(1 for v in violations if v[1] == 'WARN')
    lines_out.append(f'\n汇总: ERROR {n_err} 项 / WARN {n_warn} 项')
    return '\n'.join(lines_out)


def main():
    # 解析参数
    args = sys.argv[1:]

    if not args:
        # 从 stdin 读取
        text = sys.stdin.read()
    elif args[0] == '--text':
        # 命令行直接传文本
        text = ' '.join(args[1:]) if len(args) > 1 else ''
    else:
        # 文件路径
        filepath = args[0]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f'错误: 文件不存在 — {filepath}')
            sys.exit(1)
        except Exception as e:
            print(f'错误: 读取文件失败 — {e}')
            sys.exit(1)

    if not text.strip():
        print('PASS: 未检测到AI味违规（输入为空）')
        return

    violations = lint(text)
    report = format_report(violations)
    print(report)


if __name__ == '__main__':
    main()
