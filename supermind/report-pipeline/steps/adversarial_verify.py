"""
Step 11.1: 对抗式审查模块（CoT增强版）

源自 Codex deep-research-extracted 的 Verify Phase：
- 从已生成的content/*.md中提取关键声称
- 每条声称→3票CoT审查（每票输出推理链，不只是布尔值）
- 汇总→存活/否决/未裁决→生成审查报告

与传统机械QA的分工：
- 对抗审查：查「对不对」（事实正确性、证据充分性）
- 机械QA：查「全不全」（结构完整性、格式规范性）
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from steps.utils import (
    step_start, step_success, step_fail,
    save_json, save_text, load_markdown,
    content_dir, reports_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


# ── CoT审查清单（每票审查必须走完5步推理） ──

COT_CHECKLIST = [
    {
        "step": 1,
        "label": "来源核对",
        "question": "这个声称的原始来源是什么？我是否实际检索了来源来核对原文？来源真的支持这个声称吗，还是过度引申？",
        "required_action": "必须搜索或抓取来源URL/出处，引述原文中支持或矛盾的具体文字。不能仅凭印象回答。"
    },
    {
        "step": 2,
        "label": "反证搜索",
        "question": "有没有可信来源反驳或大幅限定这个声称？搜索相反立场的证据。",
        "required_action": "必须执行至少一次反向搜索（搜相反结论的关键词）。找到反证→引述；没找到→说明搜索了什么、为什么没找到。"
    },
    {
        "step": 3,
        "label": "层级审计",
        "question": "这个声称申报的evidence_tier配得上它的证据吗？是confirmed/reported/mapped/speculation哪一层？",
        "required_action": "必须给出tier_audit_result（只能降级不能升级）。pipeline≠orders、qualification≠volume ramp、生态相邻≠量产订单。给出理由。"
    },
    {
        "step": 4,
        "label": "时效检查",
        "question": "这个信息还新鲜吗？快速变化的领域里，旧数据要打折。",
        "required_action": "检查信息来源的发布时间。过期标记（>18个月在快变行业、>36个月在慢变行业）→降级处理。"
    },
    {
        "step": 5,
        "label": "意图判断",
        "question": "这是营销稿？PR软文？品牌官方宣传？独立第三方？论坛猜测？",
        "required_action": "判断信息来源的性质和动机。营销/PR/论坛猜测→置信度打折扣。"
    }
]

# ── 声称提取正则 ──
# 匹配包含数字的判断句（"XX达/超过/增长/约/已售/年/亿/万/百"等）
CLAIM_PATTERNS = [
    re.compile(r'(?:[^。！？\n]{2,80}(?:已售|营收|销量|市占|规模|增速|增长|下降|下降|超过|达到|突破)[^。！？\n]*?[。\n])'),
    re.compile(r'(?:[^。！？\n]{2,80}(?:约|近|大约|估计)[^。！？\n]*?(?:亿|万|百|%|倍|千)[^。！？\n]*?[。\n])'),
    re.compile(r'(?:[^。！？\n]{2,80}(?:第[一二三]|排名|位列|仅次于|领先于|位居)[^。！？\n]*?[。\n])'),
    re.compile(r'(?:\d+[万亿千百]*(?:元|美金|美元|%|倍|年|家|个|条|款|种)[^。！？\n]{0,50}[。\n])'),
    re.compile(r'(?:[^。！？\n]{2,80}(?:毛利率|净利率|复购|回头客|客单价|粉丝数)[^。！？\n]*?[。\n])'),
]


def extract_key_claims(content_dir_path: Path) -> List[Dict]:
    """
    从content/*.md文件中提取关键声称。
    返回格式：[{claim_id, chapter, section, brand, claim_text, data_numbers, tier, source_url}]
    """
    claims = []
    md_files = sorted(content_dir_path.glob("*.md"))
    
    for mf in md_files:
        if mf.name.startswith("appendix_") or mf.name.startswith("pre_research"):
            continue
        
        try:
            text = mf.read_text(encoding="utf-8")
        except Exception:
            continue
        
        chapter = _guess_chapter(mf.name)
        lines = text.split("\n")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 15:
                continue
            # 跳过标题行和表格行
            if line.startswith("#") or line.startswith("|"):
                continue
            
            for pat in CLAIM_PATTERNS:
                matches = pat.findall(line)
                for m in matches:
                    claim_text = m.strip().rstrip("。！？") + "。"
                    if len(claim_text) < 20:
                        continue
                    # 去重：相同文本只保留一次
                    if any(c["claim_text"][:40] == claim_text[:40] for c in claims):
                        continue
                    
                    # 提取数字
                    numbers = re.findall(r'[\d,.]+[万亿千百%倍]*', claim_text)
                    
                    # 推断证据层级（基于来源标记）
                    tier = _infer_tier(claim_text, mf.name, text)
                    
                    claims.append({
                        "claim_id": f"CLAIM-{len(claims)+1:03d}",
                        "chapter": chapter,
                        "brand": _guess_brand(mf.name),
                        "claim_text": claim_text,
                        "data_numbers": numbers[:5],  # top 5 numbers
                        "estimated_tier": tier,
                        "source_file": str(mf.relative_to(content_dir_path)),
                        "source_url": f"content/{mf.relative_to(content_dir_path)}",
                        "context": _get_context(lines, i),
                    })
                    
                    if len(claims) >= 30:
                        break
                if len(claims) >= 30:
                    break
            if len(claims) >= 30:
                break
    
    return claims


def _guess_chapter(filename: str) -> str:
    name = filename.lower()
    if "ch2" in name or "industry" in name: return "ch2-行业格局"
    if "ch3" in name or "competitive" in name: return "ch3-竞品扫描"
    if "ch4" in name or "deep" in name: return "ch4-本品分析"
    if "ch5" in name or "gap" in name: return "ch5-差距对比"
    if "ch6" in name or "recommendation" in name: return "ch6-策略建议"
    if "innovation" in name: return "ch10-创品策略"
    if "founder" in name: return "ch11-创始人研究"
    return "unknown"


def _guess_brand(filename: str) -> str:
    """从文件名猜测品牌名"""
    return filename.replace(".md", "").replace("ch2_", "").replace("ch3_", "").replace("ch4_", "").replace("ch5_", "").replace("ch6_", "").replace("_", " ").strip() or "未知"


def _infer_tier(claim_text: str, filename: str, full_text: str) -> str:
    """
    推断声称的证据层级，基于文本中的标记和上下文。
    """
    # 检查显式tier标记
    tier_match = re.search(r'\[(confirmed|reported|mapped|speculation)\]', claim_text)
    if tier_match:
        return tier_match.group(1)
    
    # 基于语言模式推断
    indicators = {
        "confirmed": ["公开披露", "财报显示", "年报显示", "招股书", "官方公告", "旗舰店显示", "已售", "回头客率", "综合评分"],
        "reported": ["据报道", "据.*报道", "行业研报", "第三方数据", "欧睿", "尚普", "艾媒", "券商"],
        "mapped": ["推断", "映射", "推测", "可能", "估计", "预期", "约为", "大约", "约"],
        "speculation": ["猜测", "个人认为", "有待验证", "未证实", "信息来源不明"]
    }
    
    for tier, keywords in indicators.items():
        for kw in keywords:
            if re.search(kw, claim_text):
                return tier
    
    # 默认：未标注的视为speculation
    return "speculation"


def _get_context(lines: List[str], claim_line_idx: int, window: int = 2) -> str:
    """获取声称的上下文（前后各window行）"""
    start = max(0, claim_line_idx - window)
    end = min(len(lines), claim_line_idx + window + 1)
    return "\n".join(lines[start:end])


def build_cot_verification_prompt(claim: Dict, voter_index: int, total_voters: int = 3) -> str:
    """
    为一条声称构造CoT审查prompt。
    
    输出要求：必须显式走完5步推理链，每步输出推理过程+结论。
    最终给出：refuted(bool) + confidence(high/medium/low) + evidence_summary + tier_audit
    """
    voter_label = f"审查员{voter_index+1}/{total_voters}"
    checklist_text = "\n\n".join([
        f"### Step {s['step']}: {s['label']}\n**问题**：{s['question']}\n**必须执行**：{s['required_action']}"
        for s in COT_CHECKLIST
    ])
    
    return f"""## 对抗式审查 — {voter_label}

你是第 {voter_index+1} 位独立审查员。你的任务是**尝试反驳**下面的声称。默认怀疑——不确定时标记refuted=true。

### 待审声称
- **Claim ID**: {claim['claim_id']}
- **声称内容**: "{claim['claim_text']}"
- **涉及数字**: {', '.join(claim['data_numbers']) if claim['data_numbers'] else '无'}
- **来源文件**: {claim['source_file']}
- **来源URL**: {claim.get('source_url', claim['source_file'])}
- **当前tier**: {claim['estimated_tier']}
- **所属章节**: {claim.get('chapter', '未知')}
- **涉及品牌**: {claim.get('brand', '未知')}

### 上下文
```
{claim.get('context', '无上下文')}
```

### 审查清单（必须逐步走完并输出推理）

{checklist_text}

### 输出格式（必须严格遵循）
请按以下JSON格式输出，每个字段都必须填写：

```json
{{
  "refuted": true/false,
  "confidence": "high/medium/low",
  "tier_audit": {{
    "original_tier": "{claim['estimated_tier']}",
    "audited_tier": "confirmed/reported/mapped/speculation",
    "downgraded": true/false,
    "downgrade_reason": "如果降级，说明原因；否则写'维持原级'"
  }},
  "reasoning_chain": {{
    "step1_source_check": "来源核对的推理过程和结论（50-200字）",
    "step2_counter_evidence": "反证搜索的推理过程和结论（50-200字）",
    "step3_tier_audit": "层级审计的推理过程和结论（50-200字）",
    "step4_timeliness": "时效检查的推理过程和结论（50-200字）",
    "step5_intent_judgment": "意图判断的推理过程和结论（50-200字）"
  }},
  "evidence_summary": "一句话总结支撑或反驳的关键证据（20-50字）",
  "counter_source": "如果有反证，提供来源URL或出处；否则写null"
}}
```

**重要提醒**：
- reasoning_chain中每步必须写具体的推理内容，不能只写"通过"/"无问题"/"OK"
- refuted=true的默认理由：如果找不到可验证的来源支撑这个声称
- 如果你的审查结果是不确定（无法验证），默认refuted=true
- 信息不完整≠声称错误，但信息不完整也≠声称正确"""


def build_vote_summary_prompt(claim: Dict, verdicts: List[Dict]) -> str:
    """构建投票汇总prompt"""
    refuted_count = sum(1 for v in verdicts if v.get("refuted", True))
    survived = refuted_count < 2  # 需要至少2票否决才剔除
    
    voters_summary = "\n\n".join([
        f"### 审查员{i+1}\n"
        f"- refuted: {v.get('refuted', '?')}\n"
        f"- confidence: {v.get('confidence', '?')}\n"
        f"- audited_tier: {v.get('tier_audit', {}).get('audited_tier', '?')}\n"
        f"- 关键证据: {v.get('evidence_summary', '无')}"
        for i, v in enumerate(verdicts)
    ])
    
    return f"""## 投票汇总

**Claim**: {claim['claim_text']}
**结果**: {refuted_count}/{len(verdicts)} 票否决 → {'✗ 剔除' if not survived else '✓ 存活'}

{voters_summary}

### 汇总结论
状态: {'SURVIVE' if survived else 'KILLED'}
理由: {"至少2票认为声称有据、当前信息支持" if survived else "至少2票否决" if refuted_count >= 2 else "票数不足以裁决"}
"""


def run_adversarial_review(schema: ReportSchema, project_config: ProjectConfig) -> str:
    """
    Step 11.1 主入口：执行对抗式审查（准备阶段）。
    
    实际流程：
    1. 扫描content/目录，提取关键声称（≤30条）
    2. 为每条声称构建CoT审查prompt（3票）
    3. 输出审查任务JSON → 由orchestrator执行 → 汇总结果
    
    本阶段产出：审查任务定义 + 审查prompt文件
    执行阶段：由openclaw agent读取任务JSON，通过sessions_spawn 3票并行审查
    """
    step_start("adversarial_review", "对抗式审查（CoT增强版）— 提取声称 + 构建审查任务")
    
    ct_dir = content_dir()
    rp_dir = reports_dir()
    
    # Phase 1: 提取关键声称
    print("  📋 提取关键声称...")
    claims = extract_key_claims(ct_dir)
    
    if not claims:
        step_skip("adversarial_review", "未提取到任何关键声称（content/目录为空或无可提取的声称），跳过对抗式审查")
        return None
    
    print(f"  ✓ 提取到 {len(claims)} 条声称")
    
    # Phase 2: 构建审查任务
    tasks = []
    for claim in claims:
        for v in range(3):
            tasks.append({
                "task_id": f"{claim['claim_id']}-V{v+1}",
                "claim_id": claim["claim_id"],
                "voter_index": v,
                "total_voters": 3,
                "claim": claim,
                "prompt": build_cot_verification_prompt(claim, v, 3)
            })
    
    # Phase 3: 输出审查任务
    task_output = {
        "meta": {
            "pipeline": "BREAC Industry Brand Scan v2.0",
            "phase": "adversarial_review_cot",
            "project": project_config.project_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_claims": len(claims),
            "total_tasks": len(tasks),
            "voters_per_claim": 3,
            "refutation_threshold": 2,
            "methodology": "CoT 5-step checklist: 来源核对→反证搜索→层级审计→时效检查→意图判断"
        },
        "claims": claims,
        "tasks": tasks
    }
    
    # 保存任务JSON
    task_path = rp_dir / "adversarial_tasks.json"
    save_json(task_output, task_path)
    
    # 保存人类可读的审查brief
    brief_lines = [
        f"# 对抗式审查任务（CoT增强版）",
        f"",
        f"**项目**: {project_config.project_name}",
        f"**提取声称**: {len(claims)} 条",
        f"**总任务数**: {len(tasks)} 个（每声称3票）",
        f"**否决阈值**: ≥2/3票否决则剔除",
        f"**审查方法**: CoT 5步推理链",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## 执行说明",
        f"",
        f"审查任务已保存至 `{task_path}`。",
        f"",
        f"由 openclaw orchestrator 执行：",
        f"1. 读取 `adversarial_tasks.json`",
        f"2. 为每条声称 spawn 3个并行审查 session（每个使用对应task的prompt）",
        f"3. 收集各票 verdict JSON → 运行投票 → 汇总为审查报告",
        f"4. 被否决的声称记录在QA日志中，不进入最终报告",
        f"",
        f"## CoT审查清单（每票强制走完）",
    ]
    for s in COT_CHECKLIST:
        brief_lines.append(f"- **Step {s['step']}: {s['label']}** — {s['question']}")
    
    brief_lines.extend([
        f"",
        f"## 声称预览（前10条）",
    ])
    for c in claims[:10]:
        brief_lines.append(f"- [{c['claim_id']}] {c['claim_text'][:100]}... (tier:{c['estimated_tier']}, ch:{c['chapter']})")
    
    brief_path = rp_dir / "adversarial_review_brief.md"
    save_text("\n".join(brief_lines), brief_path)
    
    # Phase 4: 声称摘要
    summary_lines = [
        f"## 声称摘要",
        f"| ID | 声称 | Tier | 章节 | 品牌 |",
        f"|----|------|------|------|------|"
    ]
    for c in claims:
        summary_lines.append(
            f"| {c['claim_id']} | {c['claim_text'][:80]} | {c['estimated_tier']} | {c['chapter']} | {c.get('brand','')} |"
        )
    
    print(f"  ✓ 审查任务: {task_path}")
    print(f"  ✓ 审查brief: {brief_path}")
    print(f"  📊 待验证声称: {len(claims)} 条 × 3票 = {len(tasks)} 次审查调用")
    print(f"  📊 预估token: ~{len(tasks) * 3000:,} tokens (约${len(tasks) * 3000 / 1_000_000 * 0.5:.2f})")
    
    step_success("adversarial_review", [str(task_path), str(brief_path)])
    return str(task_path)
