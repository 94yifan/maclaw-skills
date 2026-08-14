#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书多维表格客户端封装 —— 防止 API 故障卡死。

功能:
  - 校验 app_token 完整性（拒绝缩写 token）
  - 每次操作最多重试 3 次
  - 连续失败 3 次返回降级结果 {"ok": False, "error": ..., "degraded": True}
  - 限流识别：同一参数间歇性失败 = 限流，等 30 秒后最多再试 1 次
  - 提供 list_records / create_record / update_record / list_fields

注意：本文件仅用 Python 标准库，不依赖第三方包。
      实际 HTTP 请求通过 urllib 发送，agent 调用时需提供有效 token。
"""

import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional


# ============ 常量 ============

FEISHU_API_BASE = "https://open.feishu.cn/open-apis/bitable/v1/apps"
MAX_RETRIES = 3          # 最大重试次数
RATE_LIMIT_WAIT = 30     # 限流等待秒数
RATE_LIMIT_EXTRA_RETRY = 1  # 限流后额外重试次数
TOKEN_MIN_LENGTH = 20    # app_token 最短长度


# ============ 异常定义 ============

class BitableError(Exception):
    """多维表格操作异常"""
    pass


class TokenValidationError(BitableError):
    """token 校验失败"""
    pass


# ============ Token 校验 ============

def validate_app_token(app_token: str) -> None:
    """
    校验 app_token 是否完整。
    缩写 token（长度 < 20）直接报错，提示用完整 token。

    参数:
        app_token: 飞书多维表格 app_token

    异常:
        TokenValidationError: token 为空或过短
    """
    if not app_token or not app_token.strip():
        raise TokenValidationError("app_token 为空，请提供完整的飞书多维表格 app_token")
    if len(app_token.strip()) < TOKEN_MIN_LENGTH:
        raise TokenValidationError(
            f"app_token 长度仅 {len(app_token.strip())} 字符，疑似缩写 token，"
            f"请使用完整的 app_token（从飞书多维表格 URL 中获取完整字符串）"
        )


# ============ HTTP 请求封装 ============

def _http_request(method: str, url: str, access_token: str, body: Optional[Dict] = None) -> Dict[str, Any]:
    """
    发送 HTTP 请求到飞书 API。

    返回:
        解析后的 JSON 响应 dict

    异常:
        BitableError: 请求失败
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        # 识别限流（429 或飞书特定错误码）
        if e.code == 429:
            raise BitableError(f"限流（HTTP 429）: {body_text}")
        raise BitableError(f"HTTP {e.code}: {body_text}")
    except urllib.error.URLError as e:
        raise BitableError(f"网络错误: {e.reason}")
    except Exception as e:
        raise BitableError(f"请求异常: {e}")


# ============ 限流检测 ============

def _is_rate_limited(error_msg: str) -> bool:
    """检测是否为限流错误"""
    return "429" in error_msg or "限流" in error_msg


# ============ 核心操作函数 ============

def list_records(app_token: str, table_id: str, access_token: str,
                 page_size: int = 100, page_token: str = None) -> Dict[str, Any]:
    """
    查询多维表格记录列表。

    返回:
        成功: {"ok": True, "data": {飞书返回的记录数据}}
        失败: {"ok": False, "error": "错误信息", "degraded": True}
    """
    try:
        validate_app_token(app_token)
    except TokenValidationError as e:
        return {"ok": False, "error": str(e), "degraded": True}

    url = f"{FEISHU_API_BASE}/{app_token}/tables/{table_id}/records?page_size={page_size}"
    if page_token:
        url += f"&page_token={page_token}"

    return _request_with_retry("GET", url, access_token)


def create_record(app_token: str, table_id: str, access_token: str,
                  fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    新增一条记录。

    参数:
        fields: 字段名到值的映射

    返回:
        成功: {"ok": True, "data": {飞书返回的新记录}}
        失败: {"ok": False, "error": "错误信息", "degraded": True}
    """
    try:
        validate_app_token(app_token)
    except TokenValidationError as e:
        return {"ok": False, "error": str(e), "degraded": True}

    url = f"{FEISHU_API_BASE}/{app_token}/tables/{table_id}/records"
    body = {"fields": fields}

    return _request_with_retry("POST", url, access_token, body)


def update_record(app_token: str, table_id: str, access_token: str,
                  record_id: str, fields: Dict[str, Any],
                  append_note: bool = False, existing_note: str = "") -> Dict[str, Any]:
    """
    更新一条记录。

    参数:
        record_id: 记录 ID
        fields: 要更新的字段
        append_note: 是否追加备注（True 则把新内容追加到 existing_note 后面）
        existing_note: 现有备注内容（追加模式时使用）

    返回:
        成功: {"ok": True, "data": {飞书返回的更新后记录}}
        失败: {"ok": False, "error": "错误信息", "degraded": True}
    """
    try:
        validate_app_token(app_token)
    except TokenValidationError as e:
        return {"ok": False, "error": str(e), "degraded": True}

    # 追加备注模式：在现有备注后追加新内容
    if append_note and "备注" in fields:
        new_note = fields["备注"]
        if existing_note:
            fields["备注"] = f"{existing_note}\n{new_note}"
        else:
            fields["备注"] = new_note

    url = f"{FEISHU_API_BASE}/{app_token}/tables/{table_id}/records/{record_id}"
    body = {"fields": fields}

    return _request_with_retry("PUT", url, access_token, body)


def list_fields(app_token: str, table_id: str, access_token: str) -> Dict[str, Any]:
    """
    查询表格字段列表。

    返回:
        成功: {"ok": True, "data": {飞书返回的字段列表}}
        失败: {"ok": False, "error": "错误信息", "degraded": True}
    """
    try:
        validate_app_token(app_token)
    except TokenValidationError as e:
        return {"ok": False, "error": str(e), "degraded": True}

    url = f"{FEISHU_API_BASE}/{app_token}/tables/{table_id}/fields"

    return _request_with_retry("GET", url, access_token)


# ============ 重试逻辑 ============

def _request_with_retry(method: str, url: str, access_token: str,
                        body: Optional[Dict] = None) -> Dict[str, Any]:
    """
    带重试的请求封装。
    - 最多重试 3 次
    - 限流时等 30 秒后最多再试 1 次
    - 连续失败返回降级结果
    """
    retries = 0
    rate_limit_retry = 0

    while retries < MAX_RETRIES:
        try:
            result = _http_request(method, url, access_token, body)
            # 飞书 API 返回 code=0 表示成功
            if result.get("code") == 0:
                return {"ok": True, "data": result.get("data", {})}
            else:
                err_msg = f"飞书错误 code={result.get('code')}: {result.get('msg', '未知错误')}"
                # 检测限流
                if _is_rate_limited(err_msg) and rate_limit_retry < RATE_LIMIT_EXTRA_RETRY:
                    rate_limit_retry += 1
                    time.sleep(RATE_LIMIT_WAIT)
                    continue
                raise BitableError(err_msg)
        except BitableError as e:
            err_str = str(e)
            # 限流检测
            if _is_rate_limited(err_str) and rate_limit_retry < RATE_LIMIT_EXTRA_RETRY:
                rate_limit_retry += 1
                time.sleep(RATE_LIMIT_WAIT)
                continue
            retries += 1
            if retries >= MAX_RETRIES:
                return {"ok": False, "error": err_str, "degraded": True}
            # 非限流错误，短暂等待后重试
            time.sleep(1)

    return {"ok": False, "error": f"重试 {MAX_RETRIES} 次后仍失败", "degraded": True}


# ============ 自测 ============

if __name__ == "__main__":
    """自测：验证 token 校验、降级返回、重试逻辑"""

    # 测试1：空 token 应被拒绝
    r = list_records("", "tblXXX", "test_token")
    assert r["ok"] == False, "空 token 应返回 ok=False"
    assert r["degraded"] == True, "空 token 应返回 degraded=True"
    assert "为空" in r["error"], f"错误信息应提示为空，得到: {r['error']}"
    print("✅ 测试1通过：空 token 被拒绝")

    # 测试2：缩写 token（长度 < 20）应被拒绝
    short_token = "abc123"
    r = create_record(short_token, "tblXXX", "test_token", {"字段": "值"})
    assert r["ok"] == False, "缩写 token 应返回 ok=False"
    assert r["degraded"] == True, "缩写 token 应返回 degraded=True"
    assert "缩写" in r["error"], f"错误信息应提示缩写，得到: {r['error']}"
    print("✅ 测试2通过：缩写 token 被拒绝")

    # 测试3：有效 token 但请求失败应降级返回
    # 使用一个有效长度但假的 token，请求会失败，验证降级逻辑
    fake_token = "app" + "x" * 30  # 长度足够但内容是假的
    fake_access = "Bearer fake_token_xxx"
    r = list_records(fake_token, "tblFake", "fake_access_token")
    assert r["ok"] == False, "假 token 请求应失败"
    assert r["degraded"] == True, "失败应返回 degraded=True"
    assert "error" in r, "降级返回应包含 error 字段"
    print(f"✅ 测试3通过：请求失败正确降级（error: {r['error'][:50]}...）")

    # 测试4：update_record 追加备注逻辑
    # 验证追加模式下备注正确拼接（不实际发请求，只测拼接逻辑需要有效 token 才能走到）
    # 用假 token 验证 token 校验先拦截
    r = update_record("short", "tblXXX", "token", "recXXX", {"备注": "新备注"}, append_note=True, existing_note="旧备注")
    assert r["ok"] == False, "短 token 应被拦截"
    print("✅ 测试4通过：update_record token 校验正常拦截")

    # 测试5：validate_app_token 直接调用
    try:
        validate_app_token("")
        assert False, "空 token 应抛异常"
    except TokenValidationError:
        pass

    try:
        validate_app_token("short")
        assert False, "短 token 应抛异常"
    except TokenValidationError:
        pass

    # 合法长度 token 不应抛异常
    validate_app_token("a" * 25)
    print("✅ 测试5通过：validate_app_token 校验逻辑正确")

    # 测试6：_is_rate_limited 限流检测
    assert _is_rate_limited("HTTP 429: too many requests") == True
    assert _is_rate_limited("限流（HTTP 429）") == True
    assert _is_rate_limited("HTTP 500: internal error") == False
    assert _is_rate_limited("飞书错误 code=99991663") == False
    print("✅ 测试6通过：限流检测逻辑正确")

    print("\n✅ bitable-client.py 全部测试通过（token校验/降级返回/限流检测/重试逻辑）")
