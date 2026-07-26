#!/usr/bin/env python3
"""
品牌研究报告生产 Pipeline 主控脚本。

使用：
    python pipeline.py --config project_config.json              # 全流程执行
    python pipeline.py --config project_config.json --step 3     # 从 Step 3 开始
    python pipeline.py --config project_config.json --dry-run    # 预览流程

Pipeline 流程（18步，Schema v1.6）：
  Step  1 [手动] Init — 确认行业/品牌范围/深度/框架版本/数据平台
  Step  2 [手动] 前置调研 — 赛道框定+竞品筛选+创始人背景挖掘
  Step  3 [半自动] 数据采集 — 财报/电商/行业研报/社交（含电商必采+证据层级标注）
  Step  4 [自动]  数据分发 — 按 mapping 自动路由
  Step  5 [AI-Pro] 行业分析 — 行业总览+品类趋势
  Step  5b [AI-Pro] 产业链地图 — 产业链价值流向+卡口识别（v2.0新增）
  Step  6 [AI-Pro] 竞品五维扫描 — 深度品牌+汇总品牌（五维强制）
  Step  7 [AI-Pro] 本品五维扫描 — 本品五维深度诊断（市场渠道含非上市规模推算）
  Step  7b [AI-Pro] 内容类型分析 — 深度品牌五分类（曝光/涨粉/收藏/转化/人设）（v2.0新增）
  Step  8 [AI-Pro] 差距对比 — 本品vs竞品差距定位
  Step  8b [AI-Pro] 量化粗算 — BOM/收入/类比/错配（上市公司适用）（v2.0新增）
  Step  9 [AI-Pro] 策略建议 — 战略评估+路径判断
  Step  9b [AI-Pro] 机会地图 — 四维扫描→2×2矩阵→排序（v2.0新增）
  Step 10 [AI-Pro] 创品策略 — 跨界借鉴+原创创品+养生归经研究
  Step 11 [AI-Pro] 创始人研究 — 成长历程+理念+原生稿件索引
  Step 11b [AI-3票] 对抗式审查 — 3票制关键声称验证（查对错）（v2.0新增）
  Step 12 [自动]  图表生成 — 4张mandatory+按需optional
  Step 12b [自动]  附录生成 — 附录B（用户痛点库）+附录C（内容类型分析）（v2.0新增）
  Step 13 [自动]  docx生成 — 封面+正文+图表嵌入到Word
  Step 14 [自动]  QA检查 — 机械QA（全不全）+证据层级一致性
  Step 15 [AI-5V] 截图审查
  Step 16 [手动]  最终交付

v2.0 (2026-07-26): 融入Codex对抗式审查+evidence tier系统+产业链地图+卡口识别+
  内容五分类+用户痛点库+量化粗算+机会地图。pipeline从16步扩展至18步。

注意：Steps 5-11 实际调用 DeepSeek V4 Pro 去写分析内容。
      本脚本生成 Prompt 文件（content/*_prompt.md），与 DeepSeek Pro 协作。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 确保本目录在路径中
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from steps.utils import (
    init_status, load_status, save_status,
    step_start, step_success, step_fail, step_skip, mark_complete,
    save_json, load_json, verify_input_file, verify_output_file,
    BASE_DIR as UTILS_BASE_DIR,
)
from config import ReportSchema, ProjectConfig


# ── 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="品牌研究报告生产 Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
流程步骤：
  1    Init（手动）
  2    前置调研（手动+AI）：赛道框定+竞品筛选+创始人挖掘
  3    数据采集（半自动）：财报/电商/行业研报/社交 + evidence tier标注
  4    数据分发（自动）
  5    行业分析（AI-Pro）
  5.1  产业链地图（AI-Pro）：产业链价值流向+卡口识别（三问）
  6    竞品五维扫描（AI-Pro）
  7    本品五维扫描（AI-Pro）
  7.1  内容类型分析（AI-Pro）：五分类（曝光/涨粉/收藏/转化/人设）
  8    差距对比（AI-Pro）
  8.1  量化粗算（AI-Pro）：BOM/收入/类比/错配（上市公司适用）
  9    策略建议（AI-Pro）
  9.1  机会地图（AI-Pro）：四维扫描→2×2矩阵
  10   创品策略（AI-Pro）
  11   创始人研究（AI-Pro）
  11.1 对抗式审查（AI-3票）：3票制关键声称验证
  12   图表生成（自动）
  12.1 附录生成（自动）：附录B（用户痛点库）+附录C（内容类型分析）
  13   docx生成（自动）
  14   QA检查（自动）：机械QA + 证据层级一致性
  15   截图审查（AI-5V）
  16   最终交付（手动）

示例：
  python pipeline.py --config project_config.json
  python pipeline.py --config project_config.json --step 3
  python pipeline.py --config project_config.json --dry-run
  python pipeline.py --config project_config.json --step 10 --step 14
        """
    )
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="项目配置文件路径 (project_config.json)"
    )
    parser.add_argument(
        "--step", "-s",
        type=int,
        action="append",
        help="指定执行步骤编号（可多次使用）。不指定则全流程执行。"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="预览模式：只打印将执行哪些步骤，不实际执行"
    )
    parser.add_argument(
        "--from-step", "-f",
        type=int,
        default=1,
        help="从指定步骤开始执行（默认从头开始）"
    )
    parser.add_argument(
        "--skip-steps",
        type=str,
        default="",
        help="跳过指定步骤（逗号分隔，如 '1,2,13'）"
    )
    
    args = parser.parse_args()
    
    # ── 加载配置 ──
    config_path = Path(args.config)
    verify_input_file(config_path, "init", "项目配置")
    
    try:
        project_config = ProjectConfig(config_path)
        schema = ReportSchema()
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  品牌研究报告生产 Pipeline")
    print(f"  项目: {project_config.project_name}")
    print(f"  行业: {project_config.industry}")
    print(f"  Schema 版本: {schema.version}")
    print(f"  生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # ── 生成步骤列表 ──
    all_steps = [
        (1, "Init", "确认行业/品牌范围/深度/框架版本", False, "手动"),
        (2, "前置调研", "赛道框定+竞品筛选+创始人背景挖掘", False, "手动+AI"),
        (3, "数据采集", "财报/电商/行业研报/社交（电商必采：天猫+京东+抖音）+evidence tier标注", False, "半自动"),
        (4, "数据分发", "按 schema.mapping 自动分发", True, "自动"),
        (5, "行业分析", "行业总览+品类趋势+竞品总矩阵", False, "AI-Pro"),
        (5.1, "产业链地图", "产业链价值流向+卡口识别（三问）", False, "AI-Pro"),
        (6, "竞品五维扫描", "深度品牌五维+汇总品牌各一段+竞争模式（五维强制）", False, "AI-Pro"),
        (7, "本品五维扫描", "本品五维深度诊断（市场渠道含非上市规模推算）+趋势人群", False, "AI-Pro"),
        (7.1, "内容类型分析", "深度品牌内容五分类（曝光/涨粉/收藏/转化/人设）", False, "AI-Pro"),
        (8, "差距对比", "本品vs竞品差距定位", False, "AI-Pro"),
        (8.1, "量化粗算", "BOM拆解/收入拆分/历史类比/市值错配（上市公司适用）", False, "AI-Pro"),
        (9, "策略建议", "战略评估+路径判断+关键战略问题", False, "AI-Pro"),
        (9.1, "机会地图", "四维扫描→2×2矩阵→机会排序", False, "AI-Pro"),
        (10, "创品策略", "跨界借鉴+原创创品+养生归经研究", False, "AI-Pro"),
        (11, "创始人研究", "成长历程+关键节点+经营理念+原生稿件索引", False, "AI-Pro"),
        (11.1, "对抗式审查", "3票制关键声称验证（查对错）+证据层级一致性", False, "AI-3票"),
        (12, "图表生成", "4张mandatory+按需optional", True, "自动"),
        (12.1, "附录生成", "附录B（用户痛点库）+附录C（内容类型分析）", True, "自动"),
        (13, "docx生成", "封面+正文+图表嵌入到Word", True, "自动"),
        (14, "QA检查", "结构/内容/图表/交付四层 + 完本检查 + 五维完整性 + 证据层级一致性", True, "自动"),
        (15, "截图审查", "GLM 5V Turbo截图验证图表标签+文档效果", False, "AI-5V"),
        (16, "最终交付", "docx+QA报告+核验表", False, "手动"),
    ]
    
    # ── 确定执行步骤 ──
    skip_set = set()
    if args.skip_steps:
        skip_set = set(int(s.strip()) for s in args.skip_steps.split(",") if s.strip())
    
    if args.step:
        # 指定步骤
        target_steps = set(args.step)
        steps_to_run = [
            s for s in all_steps
            if s[0] in target_steps and s[0] not in skip_set
        ]
    else:
        # 从指定步骤开始
        steps_to_run = [
            s for s in all_steps
            if s[0] >= args.from_step and s[0] not in skip_set
        ]
    
    if not steps_to_run:
        print("⚠ 没有要执行的步骤（检查 --step / --skip-steps / --from-step 参数）")
        sys.exit(0)
    
    # ── Dry-run 预览 ──
    if args.dry_run:
        print("\n📋 Pipeline 执行预览（dry-run）:\n")
        print(f"{'步骤':<6} {'名称':<12} {'类型':<8} {'自动':<6} {'描述'}")
        print("-" * 70)
        for num, name, desc, automated, agent in steps_to_run:
            auto_str = "✅" if automated else "❌"
            print(f"  {num:<4} {name:<12} {agent:<8} {auto_str:<6} {desc}")
        print(f"\n  共 {len(steps_to_run)} 步")
        print(f"  配置文件: {config_path}")
        print(f"  Schema: {schema.version}")
        return
    
    # ── 初始化状态 -- 找到之前的状态 ──
    try:
        status = load_status()
        if status.get("overall") != "idle":
            print("⚠ 检测到已有 pipeline 状态")
            status = init_status()
    except (FileNotFoundError, json.JSONDecodeError):
        status = init_status()
    
    status["project"] = project_config.project_name
    save_status(status)
    
    # ── 逐步骤执行 ──
    print(f"\n  📋 将执行 {len(steps_to_run)} 个步骤:\n")
    # ── P0-1: 自动清理 output/content/ 下 .md 文件和 output/charts/ 下 .html/.png 文件 ──
    # 仅在从 Step 2 开始（完整运行）时清理，避免误删已填充的内容
    if not args.dry_run and args.from_step <= 2:
        import shutil
        content_dir_path = BASE_DIR / "output" / "content"
        charts_dir_path = BASE_DIR / "output" / "charts"
        if content_dir_path.exists():
            # 先删除旧命名文件（pipeline handler可能生成过旧名）
            old_names = ["founder_research.md", "innovation_strategy.md", "ch6_recommendations.md"]
            for old_name in old_names:
                old_path = content_dir_path / old_name
                if old_path.exists():
                    old_path.unlink()
                    print(f"   清理旧命名文件: {old_name}")
            # 再清理标准文件
            for f in content_dir_path.glob("*.md"):
                if f.name not in ("_FILL_COMPLETE.md", "_ECOMMERCE_DONE.md", "_CONTENT_REWRITE_DONE.md"):
                    f.unlink()
            for subdir in content_dir_path.glob("*/"):
                if subdir.is_dir():
                    shutil.rmtree(subdir)
        if charts_dir_path.exists():
            for f in charts_dir_path.glob("*.html"):
                f.unlink()
            for f in charts_dir_path.glob("*.png"):
                f.unlink()
        print("  ✓ 已清理 output/content/ (.md) 和 output/charts/ (.html/.png)")

    for num, name, desc, automated, agent in steps_to_run:
        print(f"    Step {num}: {name} — {desc}")
    
    print()
    
    for num, name, desc, automated, agent in steps_to_run:
        try:
            _execute_step(num, name, desc, automated, agent, schema, project_config)
        except SystemExit:
            # step_fail 会调用 sys.exit(1)
            print(f"\n❌ Pipeline 在 Step {num} ({name}) 处中止")
            print(f"   详细错误请查看: {Path(project_config.output_dir) / 'pipeline_error.md'}")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Pipeline 在 Step {num} ({name}) 处发生未预期异常")
            step_fail(f"step_{num}", f"未预期异常: {e}", unexpected=True)
    
    # ── 完成 ──
    mark_complete()
    
    # 打印输出摘要
    print(f"\n  📦 输出目录:")
    print(f"     data/raw/          — 原始采集数据")
    print(f"     data/dispatched/   — 已分发数据")
    print(f"     content/           — 分析内容 markdown")
    print(f"     charts/            — 图表文件")
    print(f"     reports/           — QA报告 + 最终交付")
    print(f"\n  📋 详细状态: pipeline_status.json")
    print()


def _execute_step(num: int, name: str, desc: str, automated: bool,
                  agent: str, schema: ReportSchema, project_config: ProjectConfig):
    """
    执行单个步骤的调度逻辑。
    将步骤编号映射到实际的模块函数调用。
    """
    step_name = f"step_{num}"
    step_label = f"Step {num}: {name}"
    
    # ── Step 1: Init（手动） ──
    if num == 1:
        step_start(step_name, desc)
        step_success(step_name, [f"项目配置: {project_config.project_name}"])
        return
    
    # ── Step 2: 前置调研 ──
    if num == 2:
        step_start(step_name, desc)
        research_path = BASE_DIR / "output" / "content" / "pre_research.md"
        research_content = f"""# 前置调研框架

项目: {project_config.project_name}
行业: {project_config.industry}

## 模块A: 赛道框定与竞品筛选
- 场景: 客户赛道和竞品不明确时
- 流程: 搜索品牌定位 → 提取2-3个赛道框架(含推荐理由) → 逸凡确认 → 深度调研竞品
- 竞品名单: {', '.join(project_config.all_brands)}

## 模块B: 创始人深度挖掘
- 流程: 搜索创始人生平 → 抓取深度稿件 → 提炼经营理念+成长历程+个人特质
- 产出: 成长历程+关键节点时间线+理念提炼+原生稿件索引(链接+关键摘录)
- 触发条件: 创始人风格明显的企业

## 模块C: 未上市品牌规模推算
- 流程: 搜索营收线索 → 收集侧面证据链(认证/渠道层级/产能/用户数/季节性品类) → 交叉去伪
- 产出: 锚点数字+侧面证据链+修正区间判断
- 注意: 标注AI幻觉交叉验证结果
- 触发条件: 非上市公司

## 模块D: 创品设想建议
- 流程: 趋势扫描 → (归经配伍研究) → 跨界借鉴型创品(标借鉴来源) → 原创型创品(标原因) → 味道评估 → 优先级排序
- 产出: 创品谱系+优先级+风险边界
- 触发条件: 燃创咨询切入时
"""
        with open(research_path, "w", encoding="utf-8") as f:
            f.write(research_content)
        step_success(step_name, [str(research_path)])
        return
    
    # ── Step 3: 数据采集 ──
    if num == 3:
        from steps.data_collection import collect_all
        collect_all(schema, project_config)
        return
    
    # ── Step 4: 数据分发 ──
    if num == 4:
        from steps.data_dispatch import dispatch_all
        dispatch_all(schema, project_config)
        return
    
    # ── Step 5: 行业分析 ──
    if num == 5:
        from steps.content_gen import generate_ch2
        generate_ch2(schema, project_config)
        return
    
    # ── Step 5.1: 产业链地图 ──
    if num == 5.1:
        step_start(step_name, desc)
        chain_path = BASE_DIR / "output" / "content" / "industry_chain_map.md"
        chain_content = f"""# 产业链地图与卡口识别

项目: {project_config.project_name}
行业: {project_config.industry}

## 一、产业链价值流向图
在第二章 Porter五力分析基础上，画出行业产业链的价值流向：
- 各环节做什么事、谁赚走了最多的钱
- 每个segment标注：角色/瓶颈风险(high/medium/low)/主要玩家/议价力关系
- 至少3个segments，最多7个

## 二、关键卡口识别
对产业链各环节进行chokepoint三问：
1. 供给紧不紧？（tight/loose/unknown）
2. 替代难不难？（hard/moderate/easy）
3. 市场理解了没有？（yes/partially/no）

三者同时成立→P0高信念卡口。二者→P1。一者或无→P2。

## 输出格式
- 产业链地图（segments数组）
- 卡口候选列表（按priority排序，P0→P1→P2）
- 每candidate标注evidence_tier
"""
        with open(chain_path, "w", encoding="utf-8") as f:
            f.write(chain_content)
        step_success(step_name, [str(chain_path)])
        return
    
    # ── Step 6: 竞品扫描 ──
    if num == 6:
        from steps.content_gen import generate_ch3
        generate_ch3(schema, project_config)
        return
    
    # ── Step 7: 本品分析 ──
    if num == 7:
        from steps.content_gen import generate_ch4
        generate_ch4(schema, project_config)
        return
    
    # ── Step 7.1: 内容类型分析 ──
    if num == 7.1:
        step_start(step_name, desc)
        content_path = BASE_DIR / "output" / "content" / "content_type_analysis.md"
        content_text = f"""# 内容类型五分类分析

项目: {project_config.project_name}

## 分析框架
对每个深度品牌，扫描各社媒平台（抖音/小红书/B站/微博）内容，按五类型归类：

1. 曝光型：观点强、争议大、易传播
2. 涨粉型：资源型/推荐型
3. 收藏型：步骤/SOP/模板，生命周期长
4. 转化型：展示结果/案例/收益，直接驱动购买
5. 人设型：故事/经历/踩坑复盘，建立人格认知

## 核心洞察
一次爆可能是运气，十次爆一定是规律。
判断品牌内容增长系统的主导类型。

## 输出格式
每深度品牌输出：主导类型+占比估计+增长系统判断+重复爆款倾向
每条判断标注evidence_tier
"""
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(content_text)
        step_success(step_name, [str(content_path)])
        return
    
    # ── Step 8: 差距对比 ──
    if num == 8:
        from steps.content_gen import generate_ch5
        generate_ch5(schema, project_config)
        return
    
    # ── Step 8.1: 量化粗算 ──
    if num == 8.1:
        step_start(step_name, desc)
        quant_path = BASE_DIR / "output" / "content" / "quantitative_modeling.md"
        quant_content = f"""# 量化粗算对比

项目: {project_config.project_name}
适用: 上市公司竞品

## 四件套方法（挑适用的）
1. BOM拆解估值：单产品价值量×出货量×haircut→收入→forward P/E情景
2. 收入分拆搭建：按产品线逐项加总（参照公司guidance/产能口径）
3. 历史类比锚定：找已验证赢家的重估路径做锚
4. 市值错配识别：上游卡口市值vs整条下游依赖度

## 核心纪律
- 每条假设标注evidence_tier
- 建立在mapped/speculation级假设上的model必须自首
- 目标：数量级判断（万/十万/百万/千万/亿），不是精确估值
- 输出范围，不给点估计
"""
        with open(quant_path, "w", encoding="utf-8") as f:
            f.write(quant_content)
        step_success(step_name, [str(quant_path)])
        return
    
    # ── Step 9: 策略建议 ──
    if num == 9:
        from steps.content_gen import generate_ch6
        generate_ch6(schema, project_config)
        return
    
    # ── Step 9.1: 机会地图 ──
    if num == 9.1:
        step_start(step_name, desc)
        opp_path = BASE_DIR / "output" / "content" / "opportunity_map.md"
        opp_content = f"""# 机会地图

项目: {project_config.project_name}

## 四维扫描
1. 竞争激烈度（high/medium/low）：玩家密度+投放密度+价格战程度+差异化空间
2. 赛道增速（high/medium/low/declining）：品类CAGR+新品牌涌入+品类渗透率提升空间
3. 创业/介入机会（high/medium/low）：未被满足需求+定价带空白+渠道覆盖gap+品类创新空间
4. 内容供给缺口：内容生产密度vs用户内容需求量的gap

## 输出
- 2×2矩阵：X轴=竞争激烈度（低→高），Y轴=赛道增速（低→高）
  - 高增速+低竞争=金矿 / 高增速+高竞争=红海
  - 低增速+低竞争=鸡肋 / 低增速+高竞争=陷阱
- 机会排序表（含评分+优先建议+进入条件）
- 每个机会标注evidence_tier
"""
        with open(opp_path, "w", encoding="utf-8") as f:
            f.write(opp_content)
        step_success(step_name, [str(opp_path)])
        return
    
    # ── Step 10: 创品策略 ──
    if num == 10:
        step_start(step_name, desc)
        innovation_path = BASE_DIR / "output" / "content" / "ch10_innovation.md"
        innovation_content = f"""# 创品策略框架

项目: {project_config.project_name}

## 三类创品方向
1. 跨界借鉴型：行业已验证品类 + 标志借鉴来源 → 榴莲化平移
2. 原创型：市面无先例 + 标"为什么没人做过但值得赌"
3. 养生归经型（如适用）：归经配伍 + 味道评估(自然融合/冲突风险) + 优先级排序

## 味道评估维度
- 第一档: 食材无味/淡味，榴莲做风味主角（推荐优先推进）
- 第二档: 归经合理但味道有冲突风险（备选，需打样盲测30-50人）

## 输出格式
每个方向标注: 味道评分(⭐1-5) | 归经协同(⭐1-5) | 趋势契合(⭐1-5) | 能力匹配(⭐1-5)
"""
        with open(innovation_path, "w", encoding="utf-8") as f:
            f.write(innovation_content)
        step_success(step_name, [str(innovation_path)])
        return

    # ── Step 11: 创始人研究 ──
    if num == 11:
        step_start(step_name, desc)
        founder_path = BASE_DIR / "output" / "content" / "ch11_founder.md"
        founder_content = f"""# 创始人研究框架

项目: {project_config.project_name}
创始人: {project_config.get('founder_name', '待确认')}

## 研究模块
1. 成长历程: 籍贯/教育/早期经历 → 创业触发点
2. 关键节点时间线: 品牌发展里程碑+创始人决策节点
3. 经营理念提炼: 从公开言论/决策记录中提取核心理念
4. 个人特质: 决策风格/风险偏好/领导风格

## 原生稿件索引
- 按重要性排序的深度报道列表
- 每篇标注: URL + 发布时间 + 关键内容摘要
- 逸凡可直接阅读原始素材了解创始人特性
"""
        with open(founder_path, "w", encoding="utf-8") as f:
            f.write(founder_content)
        step_success(step_name, [str(founder_path)])
        return

    # ── Step 11.1: 对抗式审查（CoT增强版） ──
    if num == 11.1:
        from steps.adversarial_verify import run_adversarial_review
        run_adversarial_review(schema, project_config)
        return

    # ── Step 12: 图表生成 ──
    if num == 12:
        from steps.charts import generate_all_charts
        generate_all_charts(schema, project_config)
        return
    
    # ── Step 12.1: 附录生成 ──
    if num == 12.1:
        step_start(step_name, desc)
        
        # 附录B: 用户痛点数据库
        app_b_path = BASE_DIR / "output" / "content" / "appendix_b_pain_points.md"
        app_b_content = f"""# 附录B：用户痛点数据库

项目: {project_config.project_name}

## 数据来源
天猫评价/小红书吐槽帖/微博评论/抖音评论区/天猫问大家

## 痛点列表
| 痛点主题 | 关键词 | 频度 | 代表性quote | 产品/策略机会 | evidence_tier |
|---------|-------|------|-----------|------------|-------------|
| (由ch4用户痛点挖掘填充) | | | | | |
"""
        with open(app_b_path, "w", encoding="utf-8") as f:
            f.write(app_b_content)
        
        # 附录C: 竞品内容类型分析
        app_c_path = BASE_DIR / "output" / "content" / "appendix_c_content_types.md"
        app_c_content = f"""# 附录C：竞品内容类型分析

项目: {project_config.project_name}

## 内容类型分布
| 品牌名 | 主导内容类型 | 各类型占比估计 | 内容增长系统判断 | 重复爆款倾向 | evidence_tier |
|-------|------------|-------------|--------------|------------|-------------|
| (由ch3内容类型五分类填充) | | | | | |
"""
        with open(app_c_path, "w", encoding="utf-8") as f:
            f.write(app_c_content)
        
        step_success(step_name, [str(app_b_path), str(app_c_path)])
        return
    
    # ── Step 13: docx 生成 ──
    if num == 13:
        from steps.docx_builder import assemble_docx
        assemble_docx(schema, project_config)
        return
    
    # ── Step 14: QA 检查 ──
    if num == 14:
        from steps.qa_check import run_full_qc
        run_full_qc(schema, project_config)
        return
    
    # ── Step 15: 截图审查 ──
    if num == 15:
        step_start(step_name, desc)
        review_path = BASE_DIR / "output" / "reports" / "screenshot_review.txt"
        review_text = f"""# 截图审查报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
项目: {project_config.project_name}

## 审查说明
本步骤由 GLM 5V Turbo 执行截图审查：
1. 对生成的 docx 进行截图
2. 验证图表标签完整性
3. 验证文档整体效果
4. 发现错误 → 回退到对应步骤修复

## 审查计划
- 图表1（天猫爆款销售对比）：标签是否中文、数据是否正确
- 图表2（京东自营爆款销售对比）：标签是否中文、数据是否正确
- 图表3（各品牌斤价对比）：标签是否中文、数据是否正确
- 图表4（回头客率对比）：标签是否中文、数据是否正确
- 文档整体效果：排版、标题层级、导航

## 状态
待 GLM 5V Turbo 执行截图与分析。
"""
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(review_text)
        
        step_success(step_name, [str(review_path)])
        return
    
    # ── Step 16: 最终交付（手动） ──
    if num == 16:
        step_start(step_name, desc)
        
        # 列出所有交付物
        deliverables = []
        
        # docx
        docx_files = list((BASE_DIR / "output" / "reports").glob("*.docx"))
        if not docx_files:
            docx_files = list((BASE_DIR / "output" / "reports").glob("*研究报告*"))
        deliverables.extend([str(f) for f in docx_files])
        
        # QA 报告
        qa_files = list((BASE_DIR / "output" / "reports").glob("qa_report*"))
        deliverables.extend([str(f) for f in qa_files])
        
        # 状态
        deliverables.append(str(BASE_DIR / "pipeline_status.json"))
        
        if not deliverables:
            step_fail(step_name, "未找到任何交付物文件")
        
        print(f"\n  📦 交付物清单:")
        for d in deliverables:
            print(f"     {d}")
        
        step_success(step_name, deliverables)
        return


if __name__ == "__main__":
    main()
