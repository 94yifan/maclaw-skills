"""
通用工具函数：文件I/O、JSON序列化、状态日志、步骤契约验证。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

BASE_DIR = Path(__file__).resolve().parent.parent  # report-pipeline/
SCHEMA_PATH = BASE_DIR / "report_schema.json"

# ── 路径工具 ─────────────────────────────────────────────

def ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def output_dir(sub: str = "") -> Path:
    d = ensure_dir(BASE_DIR / "output" / sub)
    return d


def data_raw_dir() -> Path:
    return ensure_dir(BASE_DIR / "output" / "data" / "raw")


def data_dispatched_dir() -> Path:
    return ensure_dir(BASE_DIR / "output" / "data" / "dispatched")


def content_dir() -> Path:
    return ensure_dir(BASE_DIR / "output" / "content")


def charts_dir() -> Path:
    return ensure_dir(BASE_DIR / "output" / "charts")


def reports_dir() -> Path:
    return ensure_dir(BASE_DIR / "output" / "reports")


# ── JSON I/O ──────────────────────────────────────────────

def load_json(path: Union[str, Path]) -> dict:
    """Load JSON file. Raises FileNotFoundError with clear message."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"[utils] 找不到文件: {p}")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"[utils] JSON 解析失败: {p}\n  {e}")


def save_json(data: Any, path: Union[str, Path], indent: int = 2) -> Path:
    """Save data to JSON file, creating parent dirs."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    return p


def load_markdown(path: Union[str, Path]) -> str:
    """Load markdown text file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"[utils] 找不到文件: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def save_text(text: str, path: Union[str, Path]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


# ── Schema Loader ─────────────────────────────────────────

_schema_cache: Optional[dict] = None

def get_schema(path: Optional[Union[str, Path]] = None) -> dict:
    """Load and cache report_schema.json."""
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    p = Path(path) if path else SCHEMA_PATH
    _schema_cache = load_json(p)
    return _schema_cache


# ── Pipeline 状态管理 ─────────────────────────────────────

STATUS_FILE = BASE_DIR / "pipeline_status.json"

def init_status() -> dict:
    """初始化/重置 pipeline 状态文件。"""
    status = {
        "project": "",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "steps": {},
        "current_step": None,
        "overall": "idle",
        "errors": []
    }
    save_json(status, STATUS_FILE)
    return status


def load_status() -> dict:
    try:
        return load_json(STATUS_FILE)
    except FileNotFoundError:
        return init_status()


def save_status(status: dict):
    save_json(status, STATUS_FILE)


def step_start(step_name: str, description: str):
    status = load_status()
    status["current_step"] = step_name
    status["steps"][step_name] = {
        "description": description,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None
    }
    save_status(status)
    print(f"\n{'='*60}")
    print(f"▶ Step {step_name}: {description}")
    print(f"{'='*60}")


def step_success(step_name: str, outputs: List[str]):
    status = load_status()
    if step_name in status["steps"]:
        status["steps"][step_name]["status"] = "success"
        status["steps"][step_name]["completed_at"] = datetime.now().isoformat()
        status["steps"][step_name]["outputs"] = outputs
    save_status(status)
    for o in outputs:
        print(f"  ✓ 产出: {o}")
    print(f"  ✓ Step {step_name} 完成\n")


def step_fail(step_name: str, error_msg: str, unexpected: bool = False):
    status = load_status()
    if step_name in status["steps"]:
        status["steps"][step_name]["status"] = "failed"
        status["steps"][step_name]["completed_at"] = datetime.now().isoformat()
        status["steps"][step_name]["error"] = error_msg
    status["errors"].append({"step": step_name, "error": error_msg})
    status["current_step"] = None
    status["overall"] = "failed"
    save_status(status)
    print(f"\n  ✗ Step {step_name} 失败: {error_msg}")
    
    # 写入详细错误文件，供 AI session 读取并汇报给逸凡
    error_file = BASE_DIR / "pipeline_error.md"
    tag = "未预期异常" if unexpected else "步骤执行失败"
    error_content = f"""# Pipeline 失败报告

**时间**: {datetime.now().isoformat()}
**失败步骤**: {step_name}
**类型**: {tag}
**错误信息**: {error_msg}

## 已完成步骤
"""
    for sn, sd in status["steps"].items():
        if sd.get("status") == "success":
            error_content += f"- ✅ {sn}: {sd.get('description', '')}\n"
    error_content += f"\n## 失败步骤\n- ❌ {step_name}: {error_msg}\n\n## 待执行步骤\n"
    for sn, sd in status["steps"].items():
        if sd.get("status") not in ("success", "failed"):
            error_content += f"- ⏳ {sn}: {sd.get('description', '')}\n"
    error_content += "\n---\n**请及时通知逸凡：Pipeline 已中止，需要检查错误。**\n"
    with open(error_file, "w", encoding="utf-8") as f:
        f.write(error_content)
    print(f"  📄 详细错误报告: {error_file}")
    sys.exit(1)  # hard stop


def step_skip(step_name: str, reason: str):
    status = load_status()
    status["steps"][step_name] = {
        "description": reason,
        "status": "skipped",
        "started_at": None,
        "completed_at": datetime.now().isoformat(),
        "reason": reason
    }
    save_status(status)
    print(f"  - Step {step_name} 跳过: {reason}")


def mark_complete():
    status = load_status()
    status["current_step"] = None
    status["overall"] = "completed"
    status["completed_at"] = datetime.now().isoformat()
    save_status(status)
    print(f"\n{'='*60}")
    print(f"✅ Pipeline 全部完成")
    print(f"{'='*60}")


# ── 输入输出契约验证 ────────────────────────────────────

def verify_input_file(path: Union[str, Path], step_name: str, label: str = "输入") -> Path:
    """Verify a required input file exists. Exit with error if not."""
    p = Path(path)
    if not p.exists():
        step_fail(step_name, f"{label}文件不存在: {p}")
    return p


def verify_output_file(path: Union[str, Path], step_name: str, label: str = "输出") -> Path:
    """Verify a required output file was created."""
    p = Path(path)
    if not p.exists():
        step_fail(step_name, f"{label}文件未生成: {p}")
    return p


def verify_output_dir(path: Union[str, Path], step_name: str, label: str = "输出目录") -> Path:
    p = Path(path)
    if not p.exists() or not p.is_dir():
        step_fail(step_name, f"{label}目录未生成: {p}")
    # check non-empty
    if not any(p.iterdir()):
        step_fail(step_name, f"{label}目录为空: {p}")
    return p


# ── Pipeline 配置管理 ────────────────────────────────────

def load_project_config(config_path: Union[str, Path]) -> dict:
    """Load and validate project_config.json against schema."""
    config = load_json(config_path)
    required_fields = ["project_name", "industry", "brands", "depth_config"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"project_config.json 缺少必填字段: {field}")
    if "focus" not in config.get("brands", {}) and "deep" not in config.get("brands", {}):
        raise ValueError("project_config.json 需设置 brands.focus 和/或 brands.deep")
    return config
