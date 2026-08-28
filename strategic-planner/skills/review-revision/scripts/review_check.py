#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_check.py — 小红书投放复盘检查器

用法:
  python3 review_check.py <文件路径>

检查项:
  1. 渠道完整性 — 检查是否覆盖 KOL/达人、信息流、视频流、搜索 四块
  2. 小红书口径 — 点击率=阅读率是同一指标，检测到相关词时给知识提醒
  3. 前置三问场景化 — 无搜索投放时输出提示
"""

import sys

# ── 渠道关键词 ──────────────────────────────────────────
CHANNELS = {
    'KOL/达人': ['KOL', 'kol', '达人', '博主'],
    '信息流':   ['信息流', 'feed', 'Feed'],
    '视频流':   ['视频流', '视频广告'],
    '搜索':     ['搜索', '搜索广告', '品牌词', 'SEM'],
}


def read_file(filepath: str) -> str:
    """读取文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'错误: 文件不存在 — {filepath}')
        sys.exit(1)
    except Exception as e:
        print(f'错误: 读取文件失败 — {e}')
        sys.exit(1)


def check_channels(text: str) -> list:
    """检查渠道完整性，返回 (状态, 消息) 列表"""
    results = []
    for ch_name, keywords in CHANNELS.items():
        found = any(kw in text for kw in keywords)
        if not found:
            results.append(('MISSING', f'渠道缺失：{ch_name}'))
    return results


def check_caliber(text: str) -> list:
    """小红书口径知识提醒：点击率=阅读率是同一指标"""
    results = []
    if '点击率' in text or '阅读率' in text:
        results.append((
            'INFO',
            '小红书口径：阅读=点击，点击率=阅读率是同一指标，CPC=每阅读成本=每点击成本，别把两者当两个指标对比'
        ))
    return results


def check_search_scenario(text: str) -> list:
    """检查搜索投放场景化"""
    results = []
    # 检查是否有搜索投放相关表述
    search_keywords = ['搜索投放', '搜索广告', '品牌词防守', 'SEM', '搜索卡位']
    has_search = any(kw in text for kw in search_keywords)
    if not has_search:
        results.append((
            'INFO',
            '本项目无搜索投放，品牌词防守不适用'
        ))
    return results


def format_report(channel_results, caliber_results, search_results) -> str:
    """格式化输出报告"""
    lines_out = []
    n_pass = 0
    n_warn = 0
    n_missing = 0
    n_info = 0

    # 渠道完整性
    lines_out.append('── 渠道完整性 ──')
    if not channel_results:
        lines_out.append('[PASS] 四大渠道均已覆盖：KOL/达人、信息流、视频流、搜索')
        n_pass += 1
    else:
        for status, msg in channel_results:
            lines_out.append(f'[{status}] {msg}')
            n_missing += 1

    # 小红书口径
    lines_out.append('')
    lines_out.append('── 小红书口径 ──')
    if not caliber_results:
        lines_out.append('[PASS] 未涉及点击率/阅读率指标')
        n_pass += 1
    else:
        for status, msg in caliber_results:
            lines_out.append(f'[{status}] {msg}')
            n_info += 1

    # 前置三问场景化
    lines_out.append('')
    lines_out.append('── 前置三问场景化 ──')
    if not search_results:
        lines_out.append('[PASS] 搜索投放场景已覆盖')
        n_pass += 1
    else:
        for status, msg in search_results:
            lines_out.append(f'[{status}] {msg}')
            n_info += 1

    # 汇总
    lines_out.append('')
    lines_out.append(
        f'汇总: PASS {n_pass} 项 / WARN {n_warn} 项 / MISSING {n_missing} 项'
        + (f' / INFO {n_info} 项' if n_info else '')
    )
    return '\n'.join(lines_out)


def main():
    args = sys.argv[1:]
    if not args:
        print('用法: python3 review_check.py <文件路径>')
        sys.exit(1)

    text = read_file(args[0])
    if not text.strip():
        print('错误: 文件内容为空')
        sys.exit(1)

    channel_results = check_channels(text)
    caliber_results = check_caliber(text)
    search_results = check_search_scenario(text)

    report = format_report(channel_results, caliber_results, search_results)
    print(report)


if __name__ == '__main__':
    main()
