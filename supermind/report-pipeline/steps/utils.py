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


def _project_subdir(project_config) -> str:
    """
    解析项目隔离子目录名（稳定，不重复创建空目录）。

    优先级：
    1. config 显式配置的 output_subdir
    2. config 显式配置的 output_dir（取其 basename）
    3. output/ 下已存在的同名项目目录（最新一个，复用而非新建）
    4. 都没有时生成新的时间戳目录

    修复：之前每次调用都生成新时间戳，导致重复运行步骤时不断创建空目录，
    而 docx 生成按 mtime 取最新目录时会选中空占位目录。
    """
    if project_config is None:
        return ""
    raw = getattr(project_config, "_raw", None) or {}
    # 1. 显式 output_subdir
    subdir = raw.get("output_subdir", "")
    if subdir:
        return subdir
    # 2. 显式 output_dir → 取 basename
    od = raw.get("output_dir", "")
    if od:
        return Path(od).name
    # 3. 复用 output/ 下已存在的同名项目目录（最新一个）
    pname = project_config.project_name.replace(" ", "_")
    root = BASE_DIR / "output"
    if root.exists():
        existing = sorted(
            (d for d in root.iterdir()
             if d.is_dir() and d.name.startswith(pname)),
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if existing:
            return existing[0].name
    # 4. 新时间戳目录
    return pname + "_" + __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M")


def output_dir(sub: str = "", project_config=None) -> Path:
    """
    output/ 基础目录。带 project_config 时使用 output_subdir 隔离，
    否则兼容旧路径（无隔离）。
    """
    if project_config:
        subdir = _project_subdir(project_config)
        d = ensure_dir(BASE_DIR / "output" / subdir / sub)
    else:
        d = ensure_dir(BASE_DIR / "output" / sub)
    return d


def data_raw_dir(project_config=None) -> Path:
    if project_config:
        subdir = _project_subdir(project_config)
        return ensure_dir(BASE_DIR / "output" / subdir / "data" / "raw")
    return ensure_dir(BASE_DIR / "output" / "data" / "raw")


def data_dispatched_dir(project_config=None) -> Path:
    if project_config:
        subdir = _project_subdir(project_config)
        return ensure_dir(BASE_DIR / "output" / subdir / "data" / "dispatched")
    return ensure_dir(BASE_DIR / "output" / "data" / "dispatched")


def content_dir(project_config=None) -> Path:
    if project_config:
        subdir = _project_subdir(project_config)
        return ensure_dir(BASE_DIR / "output" / subdir / "content")
    return ensure_dir(BASE_DIR / "output" / "content")


def charts_dir(project_config=None) -> Path:
    if project_config:
        subdir = _project_subdir(project_config)
        return ensure_dir(BASE_DIR / "output" / subdir / "charts")
    return ensure_dir(BASE_DIR / "output" / "charts")


def reports_dir(project_config=None) -> Path:
    if project_config:
        subdir = _project_subdir(project_config)
        return ensure_dir(BASE_DIR / "output" / subdir / "reports")
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


def validate_brand_content(filepath: Union[str, Path], project_config) -> bool:
    """
    品牌白名单校验：检查某个内容文件中是否出现白名单外的已知无关品牌名。
    返回 True=通过（无无关品牌），False=有问题。
    """
    from pathlib import Path as _Path
    p = _Path(filepath)
    if not p.exists():
        print(f"  ⚠ [validate_content] 文件不存在: {p}")
        return True  # can't check, skip

    try:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return True

    # 从 project_config 提取品牌白名单
    focus = project_config.focus_brand if project_config.focus_brand else ""
    deep = set(project_config.deep_brands) if hasattr(project_config, "deep_brands") else set()
    summary = set(project_config.summary_brands) if hasattr(project_config, "summary_brands") else set()
    industry_terms = set(project_config.industry.split("/")) if project_config.industry else set()

    # 行业通用词（视行业而定，这里是家纺/床上用品白名单）
    generic_allowed = {
        "康尔馨", "亚朵", "罗莱", "梦百合", "水星", "网易严选", "富安娜",
        "睡眠博士", "野兽派", "躺岛", "京东京造", "梦洁", "宜家",
        "床品", "家纺", "四件套", "枕头", "睡眠", "酒店", "羽绒",
        "记忆棉", "被芯", "毛巾", "浴巾", "面料", "棉", "丝", "床"
    }
    allowed = deep | summary | {focus} | industry_terms | generic_allowed

    # 已知无关品牌黑名单
    suspicious = {
        "三棵树", "立邦", "多乐士", "卡百利", "嘉宝莉", "菲玛",
        "亚士漆", "榴莲", "玉米", "汽车", "新能源汽车", "涂料", "墙面漆",
        "艺术漆", "乳胶漆", "防水涂料", "油漆"
    }

    found = []
    for kw in suspicious:
        if kw in content and kw not in allowed:
            found.append(kw)

    if found:
        print(f"  ⚠ WARN: {p.name} 中发现白名单外无关品牌名: {', '.join(found)}")
        return False
    return True


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
