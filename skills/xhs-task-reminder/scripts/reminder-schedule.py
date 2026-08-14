#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提醒节点计算 —— 纯函数，无副作用，可直接 import 测试。

提醒节奏：记录当天为第1天，day_diff = (today - record_date).days
  day_diff=1 → 第2天：问开始了吗
  day_diff=2 → 第3天：跟进进展
  day_diff=3 → 第4天：确认状态
  day_diff=6 → 第7天：升级（私聊+群里标记延期+通知逸凡）
  其他 → 跳过（day_diff=0 当天不算提醒）
"""

from datetime import datetime


def compute_reminder_stage(record_date: str, today: str, special_reminder: str = None) -> dict:
    """
    根据记录日期和当前日期计算提醒阶段。

    参数:
        record_date: 记录日期，格式 YYYY-MM-DD
        today: 今天日期，格式 YYYY-MM-DD
        special_reminder: 特殊提醒文本（备注中含「特殊提醒：」的内容），为空则走默认节奏

    返回:
        dict，包含 mode/stage/message 等字段
    """
    # 特殊提醒优先，不走默认节奏
    if special_reminder and special_reminder.strip():
        return {"mode": "special", "message": special_reminder.strip()}

    # 解析日期
    rd = datetime.strptime(record_date, "%Y-%m-%d")
    td = datetime.strptime(today, "%Y-%m-%d")
    day_diff = (td - rd).days

    # 按差值匹配提醒阶段
    if day_diff == 1:
        return {"mode": "remind", "stage": 2, "message": "问开始了吗"}
    elif day_diff == 2:
        return {"mode": "remind", "stage": 3, "message": "跟进进展"}
    elif day_diff == 3:
        return {"mode": "remind", "stage": 4, "message": "确认状态"}
    elif day_diff == 6:
        return {"mode": "escalate", "stage": 7, "message": "私聊负责人+群里标记延期+通知逸凡"}
    else:
        return {"mode": "skip"}


if __name__ == "__main__":
    """自测：验证 day_diff 1/2/3/6 和特殊提醒场景"""

    base = "2025-01-10"  # 记录日期

    # 测试 day_diff=0（当天）→ 跳过
    r = compute_reminder_stage(base, "2025-01-10")
    assert r["mode"] == "skip", f"day_diff=0 应跳过，得到 {r}"

    # 测试 day_diff=1 → 第2天
    r = compute_reminder_stage(base, "2025-01-11")
    assert r == {"mode": "remind", "stage": 2, "message": "问开始了吗"}, f"day_diff=1 结果错误: {r}"

    # 测试 day_diff=2 → 第3天
    r = compute_reminder_stage(base, "2025-01-12")
    assert r == {"mode": "remind", "stage": 3, "message": "跟进进展"}, f"day_diff=2 结果错误: {r}"

    # 测试 day_diff=3 → 第4天
    r = compute_reminder_stage(base, "2025-01-13")
    assert r == {"mode": "remind", "stage": 4, "message": "确认状态"}, f"day_diff=3 结果错误: {r}"

    # 测试 day_diff=6 → 第7天升级
    r = compute_reminder_stage(base, "2025-01-16")
    assert r == {"mode": "escalate", "stage": 7, "message": "私聊负责人+群里标记延期+通知逸凡"}, f"day_diff=6 结果错误: {r}"

    # 测试 day_diff=4（非提醒节点）→ 跳过
    r = compute_reminder_stage(base, "2025-01-14")
    assert r["mode"] == "skip", f"day_diff=4 应跳过，得到 {r}"

    # 测试 day_diff=5（非提醒节点）→ 跳过
    r = compute_reminder_stage(base, "2025-01-15")
    assert r["mode"] == "skip", f"day_diff=5 应跳过，得到 {r}"

    # 测试特殊提醒
    r = compute_reminder_stage(base, "2025-01-11", special_reminder="每天跟进一次直到完成")
    assert r == {"mode": "special", "message": "每天跟进一次直到完成"}, f"特殊提醒结果错误: {r}"

    # 测试特殊提醒（空白字符串应走默认节奏）
    r = compute_reminder_stage(base, "2025-01-11", special_reminder="   ")
    assert r["mode"] == "remind", f"空白特殊提醒应走默认节奏，得到 {r}"

    # 测试特殊提醒（None 应走默认节奏）
    r = compute_reminder_stage(base, "2025-01-11", special_reminder=None)
    assert r["mode"] == "remind", f"None 特殊提醒应走默认节奏，得到 {r}"

    print("✅ reminder-schedule.py 全部测试通过（day_diff 0/1/2/3/4/5/6 + 特殊提醒）")
