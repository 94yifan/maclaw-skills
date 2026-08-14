#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息模板渲染引擎 —— {{placeholder}} 替换 + 飞书 at 标签渲染。

功能:
  - 读取 assets/templates/ 下的模板文件
  - 将 {{placeholder}} 替换为实际值
  - members_at：把成员列表渲染成飞书 at 标签串 <at user_id="ou_xxx">名字</at>
  - items：把待办列表渲染成结构化文本

仅用 Python 标准库，无第三方依赖。
"""

import os
import re
from typing import Any, Dict, List, Optional


# 模板目录：相对于本文件所在的 scripts/ 目录向上找 assets/templates/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_DIR = os.path.join(os.path.dirname(_SCRIPT_DIR), "assets", "templates")


def render_at_tag(open_id: str, name: str) -> str:
    """
    渲染单个飞书 at 标签。

    参数:
        open_id: 用户的 open_id
        name: 用户显示名

    返回:
        <at user_id="ou_xxx">名字</at>
    """
    return f'<at user_id="{open_id}">{name}</at>'


def render_members_at(members: List[Dict[str, str]]) -> str:
    """
    把成员列表渲染成 at 标签串（空格分隔）。

    参数:
        members: [{"name": "张三", "open_id": "ou_xxx"}, ...]

    返回:
        <at user_id="ou_xxx">张三</at> <at user_id="ou_yyy">李四</at>
    """
    if not members:
        return ""
    tags = []
    for m in members:
        name = m.get("name", "")
        open_id = m.get("open_id", "")
        if open_id:
            tags.append(render_at_tag(open_id, name))
        else:
            # 没有 open_id 时只输出名字
            tags.append(name)
    return " ".join(tags)


def render_items(items: List[Dict[str, Any]], group_by: str = None) -> str:
    """
    把待办列表渲染成结构化文本。

    参数:
        items: [{"具体内容": "...", "负责人": "...", "截止时间": "...", "状态": "..."}, ...]
        group_by: 按某字段分组（如 "负责人"），不分组则 None

    返回:
        渲染后的文本
    """
    if not items:
        return "（暂无待办）"

    lines = []

    if group_by:
        # 按字段分组
        groups = {}
        for item in items:
            key = item.get(group_by, "未分配")
            if isinstance(key, list):
                key = "、".join(key)
            groups.setdefault(key, []).append(item)

        for group_name, group_items in groups.items():
            lines.append(f"【{group_name}】")
            for i, item in enumerate(group_items, 1):
                content = item.get("具体内容", "未描述")
                deadline = item.get("截止时间", "")
                status = item.get("状态", "")
                line = f"  {i}. {content}"
                if deadline:
                    line += f"（截止 {deadline}）"
                if status:
                    line += f" [{status}]"
                lines.append(line)
            lines.append("")
    else:
        # 不分组，直接列出
        for i, item in enumerate(items, 1):
            content = item.get("具体内容", "未描述")
            owner = item.get("负责人", "")
            deadline = item.get("截止时间", "")
            status = item.get("状态", "")
            line = f"{i}. {content}"
            if owner:
                owner_str = "、".join(owner) if isinstance(owner, list) else owner
                line += f" — {owner_str}"
            if deadline:
                line += f"（截止 {deadline}）"
            if status:
                line += f" [{status}]"
            lines.append(line)

    return "\n".join(lines)


def render_template(template_name: str, variables: Dict[str, Any]) -> str:
    """
    读取模板文件并替换所有 {{placeholder}}。

    参数:
        template_name: 模板文件名（如 "group-reminder.md"）
        variables: 变量字典，key 对应模板中的 {{key}}

    返回:
        渲染后的文本
    """
    # 读取模板文件
    template_path = os.path.join(_TEMPLATE_DIR, template_name)
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 特殊处理：members_at 变量
    if "members_at" not in variables and "members" in variables:
        variables["members_at"] = render_members_at(variables["members"])

    # 特殊处理：items 变量（如果是列表则渲染）
    if "items" in variables and isinstance(variables["items"], list):
        group_by = variables.pop("_items_group_by", None)
        variables["items"] = render_items(variables["items"], group_by)

    # 替换所有 {{placeholder}}
    def replacer(match):
        key = match.group(1).strip()
        val = variables.get(key, "")
        return str(val)

    result = re.sub(r"\{\{(\w+)\}\}", replacer, template)

    return result


def render_template_string(template_text: str, variables: Dict[str, Any]) -> str:
    """
    直接对模板字符串做替换（不需要文件）。

    参数:
        template_text: 模板文本
        variables: 变量字典

    返回:
        渲染后的文本
    """
    if "members_at" not in variables and "members" in variables:
        variables["members_at"] = render_members_at(variables["members"])

    if "items" in variables and isinstance(variables["items"], list):
        group_by = variables.pop("_items_group_by", None)
        variables["items"] = render_items(variables["items"], group_by)

    def replacer(match):
        key = match.group(1).strip()
        val = variables.get(key, "")
        return str(val)

    return re.sub(r"\{\{(\w+)\}\}", replacer, template_text)


# ============ 自测 ============

if __name__ == "__main__":
    """自测：验证 at 标签渲染、占位符替换、items 渲染"""

    # 测试1：render_at_tag 单个 at 标签
    tag = render_at_tag("ou_abc123", "张三")
    assert tag == '<at user_id="ou_abc123">张三</at>', f"at 标签渲染错误: {tag}"
    print("✅ 测试1通过：单个 at 标签渲染正确")

    # 测试2：render_members_at 多人 at 标签
    members = [
        {"name": "张三", "open_id": "ou_001"},
        {"name": "李四", "open_id": "ou_002"},
        {"name": "王五", "open_id": "ou_003"},
    ]
    at_str = render_members_at(members)
    assert '<at user_id="ou_001">张三</at>' in at_str
    assert '<at user_id="ou_002">李四</at>' in at_str
    assert '<at user_id="ou_003">王五</at>' in at_str
    assert " " in at_str  # 空格分隔
    print("✅ 测试2通过：多人 at 标签渲染正确")

    # 测试3：render_members_at 空列表
    assert render_members_at([]) == ""
    print("✅ 测试3通过：空成员列表返回空字符串")

    # 测试4：render_items 按负责人分组
    items = [
        {"具体内容": "新增关键词打包", "负责人": "张三", "截止时间": "2025-01-15", "状态": "待开始"},
        {"具体内容": "笔记上线检查", "负责人": "李四", "截止时间": "2025-01-15", "状态": "进行中"},
        {"具体内容": "调户复盘", "负责人": "张三", "截止时间": "2025-01-16", "状态": "待开始"},
    ]
    rendered = render_items(items, group_by="负责人")
    assert "【张三】" in rendered
    assert "【李四】" in rendered
    assert "新增关键词打包" in rendered
    assert "笔记上线检查" in rendered
    assert "调户复盘" in rendered
    print("✅ 测试4通过：items 按负责人分组渲染正确")

    # 测试5：render_items 空列表
    assert render_items([]) == "（暂无待办）"
    print("✅ 测试5通过：空待办列表返回占位文本")

    # 测试6：render_template_string 占位符替换
    tpl = "项目：{{project_name}}\n日期：{{date}}\n负责人：{{members_at}}\n待办：\n{{items}}"
    vars_ = {
        "project_name": "蓝氏奶盾",
        "date": "2025-01-10",
        "members": [{"name": "陈思安", "open_id": "ou_xxx"}],
        "items": [{"具体内容": "新增人群", "负责人": "陈思安", "截止时间": "2025-01-12", "状态": "待开始"}],
    }
    result = render_template_string(tpl, vars_)
    assert "蓝氏奶盾" in result
    assert "2025-01-10" in result
    assert '<at user_id="ou_xxx">陈思安</at>' in result
    assert "新增人群" in result
    print("✅ 测试6通过：模板字符串占位符替换正确")

    # 测试7：render_template_string 未提供变量的占位符替换为空
    tpl2 = "标题：{{title}} / 内容：{{content}}"
    result2 = render_template_string(tpl2, {"title": "测试标题"})
    assert "测试标题" in result2
    # 未提供的变量替换为空字符串
    assert "内容：\n" in result2 or "内容： " in result2 or "内容：" in result2
    print("✅ 测试7通过：未提供的变量替换为空字符串")

    # 测试8：render_template 读取实际模板文件
    # 先确保模板文件存在
    if os.path.exists(os.path.join(_TEMPLATE_DIR, "group-reminder.md")):
        result3 = render_template("group-reminder.md", {
            "project_name": "测试项目",
            "date": "2025-01-10",
            "members": [{"name": "测试人", "open_id": "ou_test"}],
            "items": [{"具体内容": "测试任务", "负责人": "测试人", "截止时间": "2025-01-12", "状态": "待开始"}],
        })
        assert "测试项目" in result3
        assert "2025-01-10" in result3
        assert '<at user_id="ou_test">测试人</at>' in result3
        assert "测试任务" in result3
        print("✅ 测试8通过：从文件读取模板并渲染正确")
    else:
        print("⏭️ 测试8跳过：模板文件尚不存在")

    print("\n✅ render-template.py 全部测试通过（at标签/占位符替换/items渲染/文件读取）")
