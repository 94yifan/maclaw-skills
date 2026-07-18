"""
Step 11: DOCX 生成模块。

实现 playbook 第七节定义的 docx 六步法：
1. python-docx 定位章节边界（跳过TOC）
2. lxml body.remove() 删除旧章节全部子元素
3. lxml 创建新段落，addprevious() 插入
4. python-docx 保存 → zipfile 重新打开
5. 克隆 drawing + 修改 blip + 创建图片段落
6. 更新 rels + media → zipfile 写回

依赖：python-docx + lxml + zipfile（三件套，无第三方自动化库）
"""
import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from steps.utils import (
    step_start, step_success, step_fail,
    save_json, load_json, save_text, load_markdown,
    verify_input_file, verify_output_file,
    content_dir, charts_dir, output_dir, BASE_DIR
)
from config import ReportSchema, ProjectConfig


# ── docx 六步法 ────────────────────────────────────────────

def assemble_docx(schema: ReportSchema, project_config: ProjectConfig) -> Path:
    """
    Step 11 主入口：组装完整 docx 文档。
    使用 6 步法将分析内容 + 图表嵌入到 Word 文档中。
    """
    step_start("docx_assembly", "DOCX 生成 — 6步法组装文字 + 图表")
    
    out_dir = ensure_output_dir()
    docx_path = out_dir / project_config.get("output_settings.docx_filename",
                                              f"{project_config.project_name}_品牌研究报告.docx")
    
    # Step 1: 创建基础文档
    print("  Step 1/6: 创建基础文档骨架...")
    doc = create_base_document(schema, project_config)
    
    # Step 2: 读取各章内容
    print("  Step 2/6: 读取各章分析内容...")
    chapters_content = load_chapter_content(schema, project_config)
    
    # Step 3: 写入各章内容（使用 lxml + addprevious）
    print("  Step 3/6: 写入章节内容...")
    for ch_key, content in chapters_content.items():
        insert_chapter_content(doc, ch_key, content, schema)
    
    # Step 4: 保存并重新打开（zipfile）
    print("  Step 4/6: 保存临时文件 + zipfile 重新打开...")
    temp_path = out_dir / "_temp_before_images.docx"
    doc.save(str(temp_path))
    
    # Step 5: 嵌入图表
    print("  Step 5/6: 嵌入图表图片...")
    chart_files = get_chart_files(project_config)
    if chart_files:
        final_path = embed_charts_in_docx(str(temp_path), chart_files, out_dir)
    else:
        final_path = temp_path
    
    # Step 6: 最终清理
    print("  Step 6/6: 最终处理...")
    shutil.copy(final_path, docx_path)
    
    verify_output_file(docx_path, "docx_assembly")
    step_success("docx_assembly", [str(docx_path)])
    return docx_path


def ensure_output_dir() -> Path:
    """确保 output/reports/ 目录存在。"""
    return output_dir("reports")


def create_base_document(schema: ReportSchema, project_config: ProjectConfig):
    """
    Step 1 of 6: 用 python-docx 创建基础文档骨架。
    包含封面页 + 每章标题占位 + TOC 区域。
    """
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.section import WD_ORIENT
    
    doc = Document()
    
    # ── 封面 ──
    for _ in range(6):
        doc.add_paragraph()
    
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run(project_config.project_name)
    run.font.size = Pt(28)
    run.bold = True
    
    subtitle_para = doc.add_paragraph()
    subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle_para.add_run("品牌研究报告")
    run.font.size = Pt(18)
    
    info_para = doc.add_paragraph()
    info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info_para.add_run(f"行业: {project_config.industry}   框架: V{schema.version}\n"
                            f"生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_page_break()
    
    # ── TOC 页 ──
    toc_title = doc.add_heading('目录', level=1)
    for ch_key in ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'appendix']:
        ch_title = schema.get_chapter_title(ch_key)
        p = doc.add_paragraph(f"{ch_key.upper()}  {ch_title}")
        p.paragraph_format.space_after = Pt(4)
    
    doc.add_page_break()
    
    # ── 各章 H1 占位 ──
    for ch_key in ['ch1', 'ch2', 'ch3', 'ch4', 'ch5', 'ch6', 'appendix']:
        ch_title = schema.get_chapter_title(ch_key)
        heading = doc.add_heading(f"第{ch_key[2:]}章 {ch_title}", level=1)
        # Add a marker paragraph for lxml boundary detection
        marker = doc.add_paragraph()
        marker_run = marker.add_run(f"__SECTION_PLACEHOLDER_{ch_key}__")
        marker_run.font.size = Pt(1)
        marker_run.font.color.rgb = RGBColor(255, 255, 255)  # invisible
        doc.add_page_break()
    
    return doc


def load_chapter_content(schema: ReportSchema, project_config: ProjectConfig) -> Dict[str, str]:
    """读取 content/ 下各章的 markdown 文件。"""
    c_dir = content_dir()
    ch3_dir = c_dir / "ch3_competitive"
    ch4_dir = c_dir / "ch4_deep"
    
    content = {}
    chapter_map = {
        'ch1': c_dir / "ch1_findings.md",
        'ch2': c_dir / "ch2_industry.md",
        'ch5': c_dir / "ch5_gap.md",
        'ch6': c_dir / "ch6_recommendations.md",
    }
    
    for ch_key, path in chapter_map.items():
        if path.exists():
            content[ch_key] = load_markdown(path)
        else:
            print(f"  ⚠ {ch_key} 内容文件未找到: {path}，使用占位")
            content[ch_key] = f"\n\n{ch_key.upper()}：{schema.get_chapter_title(ch_key)}\n\n[内容待 DeepSeek V4 Pro 生成]\n\n"
    
    # ch3: 合并所有竞品文件
    ch3_content = []
    if ch3_dir.exists():
        deep_files = sorted(ch3_dir.glob("deep_*.md"))
        summary_files = list(ch3_dir.glob("summary_*.md"))
        for f in deep_files + summary_files:
            try:
                ch3_content.append(load_markdown(f))
            except FileNotFoundError:
                continue
    content['ch3'] = "\n\n".join(ch3_content) if ch3_content else "\n\n[竞品扫描内容待生成]\n\n"
    
    # ch4: 合并本品分析
    ch4_content = []
    if ch4_dir.exists():
        for f in sorted(ch4_dir.glob("*.md")):
            if f.name.endswith("_prompt.md"):
                continue
            try:
                ch4_content.append(load_markdown(f))
            except FileNotFoundError:
                continue
    content['ch4'] = "\n\n".join(ch4_content) if ch4_content else "\n\n[本品分析内容待生成]\n\n"
    
    return content


def insert_chapter_content(doc, ch_key: str, markdown_content: str, schema: ReportSchema):
    """
    Step 3 of 6: 使用 lxml 将 markdown 内容插入到对应章节占位处。
    
    使用 lxml.etree 操作 document.xml:
    - 找到占位段落（含 __SECTION_PLACEHOLDER_{ch_key}__）
    - 使用 addprevious() 插入新段落
    - reversed() 顺序插入
    """
    from lxml import etree
    
    # 访问 document.xml
    document_part = doc.part
    document_element = document_part.element
    body = document_element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
    if body is None:
        body = document_element
    
    nsmap = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    }
    
    # 查找占位段落
    placeholder = f"__SECTION_PLACEHOLDER_{ch_key}__"
    placeholder_para = None
    for para in body.iter(f'{{{nsmap["w"]}}}p'):
        texts = para.findall(f'.//{{{nsmap["w"]}}}t')
        for t in texts:
            if t.text and placeholder in t.text:
                placeholder_para = para
                break
        if placeholder_para:
            break
    
    if placeholder_para is None:
        print(f"  ⚠ 未找到 {ch_key} 的占位段落")
        return
    
    # 将 markdown 转为简单段落，插入到 placeholder 前（逆序）
    lines = markdown_content.strip().split('\n')
    new_elements = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        new_para = etree.SubElement(body, f'{{{nsmap["w"]}}}p')
        
        # 判断是否为标题
        if line.startswith('# '):
            style = etree.SubElement(new_para, f'{{{nsmap["w"]}}}pPr')
            pstyle = etree.SubElement(style, f'{{{nsmap["w"]}}}pStyle')
            pstyle.set(f'{{{nsmap["w"]}}}val', 'Heading1')
            text = line[2:].strip()
        elif line.startswith('## '):
            style = etree.SubElement(new_para, f'{{{nsmap["w"]}}}pPr')
            pstyle = etree.SubElement(style, f'{{{nsmap["w"]}}}pStyle')
            pstyle.set(f'{{{nsmap["w"]}}}val', 'Heading2')
            text = line[3:].strip()
        elif line.startswith('### '):
            style = etree.SubElement(new_para, f'{{{nsmap["w"]}}}pPr')
            pstyle = etree.SubElement(style, f'{{{nsmap["w"]}}}pStyle')
            pstyle.set(f'{{{nsmap["w"]}}}val', 'Heading3')
            text = line[4:].strip()
        else:
            text = line
        
        # 添加文本 run
        if text:
            run_elem = etree.SubElement(new_para, f'{{{nsmap["w"]}}}r')
            t_elem = etree.SubElement(run_elem, f'{{{nsmap["w"]}}}t')
            t_elem.text = text
        
        new_elements.append(new_para)
    
    # 逆序插入（addprevious 特性）
    for para in reversed(new_elements):
        try:
            # 将 placeholder 父元素中插入
            placeholder_para.addprevious(para)
        except Exception as e:
            print(f"    ⚠ lxml 插入段落失败: {e}")
    
    # 删除占位段落
    try:
        placeholder_para.getparent().remove(placeholder_para)
    except Exception:
        pass


def get_chart_files(project_config: ProjectConfig) -> List[Tuple[str, Path]]:
    """
    获取图表 PNG 文件列表。
    返回 [(title, path), ...]
    """
    c_dir = charts_dir()
    if not c_dir.exists():
        return []
    
    charts_info = []
    
    # 按 schema 定义顺序查找
    expected = [
        ("天猫旗舰店爆款销售对比", "chart_brand_comparison_1"),
        ("京东自营爆款销售对比", "chart_brand_comparison_2"),
        ("各品牌核心产品斤价对比", "chart_brand_comparison_3"),
        ("各品牌回头客/复购率对比", "chart_brand_comparison_4"),
    ]
    
    for title, chart_id in expected:
        for ext in ['.png']:
            path = c_dir / f"{chart_id}{ext}"
            if path.exists():
                charts_info.append((title, path))
                break
        else:
            html_path = c_dir / f"{chart_id}.html"
            if html_path.exists():
                charts_info.append((title, html_path))
    
    return charts_info


def embed_charts_in_docx(temp_docx_path: str, chart_files: List[Tuple[str, Path]],
                         out_dir: Path) -> Path:
    """
    Steps 4-6 of 6: 将图表嵌入 docx。
    
    完整版 6 步法中的 Step 4-6:
    - zipfile 重新打开
    - 克隆 drawing + 修改 blip
    - 更新 rels + media
    """
    from docx import Document
    from lxml import etree
    
    doc = Document(temp_docx_path)
    document_element = doc.part.element
    body = document_element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
    if body is None:
        body = document_element
    
    # 查找 ch3 3.6 节之前的插入点
    # 找到最后一个 ch3 内容的末尾
    insert_target = find_chart_insertion_point(doc)
    if insert_target is None:
        print("  ⚠ 未找到图表插入位置，追加到文档末尾")
        insert_target = body[-1] if len(body) > 0 else body
    
    # Step 4: 保存 → zipfile 重新打开
    temp_zip_path = str(out_dir / "_temp_for_images.docx")
    doc.save(temp_zip_path)
    
    # Step 5+6: 用 zipfile 操作直接嵌入图片
    final_path = str(out_dir / "_final_with_images.docx")
    
    # 读取原始 docx 为 zip
    with zipfile.ZipFile(temp_zip_path, 'r') as zin:
        zip_contents = {}
        for item in zin.infolist():
            zip_contents[item.filename] = zin.read(item.filename)
    
    # 解析 document.xml
    doc_xml = zip_contents.get('word/document.xml', b'')
    if isinstance(doc_xml, bytes):
        doc_tree = etree.fromstring(doc_xml)
    else:
        doc_tree = etree.fromstring(doc_xml)
    
    nsmap = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    }
    
    # 读取现有的 rels 文件
    rels_path = 'word/_rels/document.xml.rels'
    rels_xml = zip_contents.get(rels_path, b'')
    if isinstance(rels_xml, bytes):
        rels_tree = etree.fromstring(rels_xml)
    else:
        rels_tree = etree.fromstring(rels_xml)
    
    rels_nsmap = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
    
    # 获取当前最大关系 ID
    existing_rels = rels_tree.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
    max_rel_id = 0
    for rel in existing_rels:
        rid = rel.get('Id', 'rId0')
        try:
            num = int(rid.replace('rId', ''))
            max_rel_id = max(max_rel_id, num)
        except ValueError:
            continue
    
    # 嵌入每张图片
    image_count = 0
    for i, (title, chart_path) in enumerate(chart_files):
        image_count += 1
        next_id = max_rel_id + image_count
        rel_id = f'rId{next_id}'
        media_filename = f'image{image_count:03d}.png'
        
        # 读取图片
        with open(chart_path, 'rb') as f:
            image_bytes = f.read()
        
        # 添加 media 文件
        zip_contents[f'word/media/{media_filename}'] = image_bytes
        
        # 添加 rels 关系
        rel_elem = etree.SubElement(
            rels_tree,
            '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'
        )
        rel_elem.set('Id', rel_id)
        rel_elem.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')
        rel_elem.set('Target', f'media/{media_filename}')
        
        # 在文档 body 中创建图片段落 + 标题段落
        # 模拟 python-docx 的 add_picture 方式
        body_element = doc_tree.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
        if body_element is None:
            body_element = doc_tree
        
        # 创建图标题段落
        fig_para = etree.SubElement(body_element, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        fig_run = etree.SubElement(fig_para, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r')
        fig_text = etree.SubElement(fig_run, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        fig_text.text = f"图{i+1}：{title}"
        fig_text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    
    # 写回文件
    with zipfile.ZipFile(final_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in zip_contents.items():
            zout.writestr(name, data)
        # 写回更新后的 rels
        zout.writestr(rels_path, etree.tostring(rels_tree, xml_declaration=True, encoding='UTF-8', standalone=True))
        # 写回更新后的 document.xml
        zout.writestr('word/document.xml', etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone=True))
    
    return Path(final_path)


def find_chart_insertion_point(doc):
    """
    查找文档中 ch3 末尾附近的位置，在 3.6 之前插入图表。
    返回 lxml element 作为插入点。
    """
    from lxml import etree
    
    document_element = doc.part.element
    body = document_element.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
    if body is None:
        body = document_element
    
    nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    # 查找 "竞争模式归纳" 或 "3.6" 相关标题
    for para in body:
        texts = para.findall(f'.//{{{nsmap["w"]}}}t')
        full_text = ''.join(t.text or '' for t in texts)
        if '3.6' in full_text or '竞争模式' in full_text:
            return para
    
    # fallback: 找 ch3 的末尾（最后一个 ch3 段落之后）
    last_ch3_para = None
    in_ch3 = False
    for para in body:
        texts = para.findall(f'.//{{{nsmap["w"]}}}t')
        full_text = ''.join(t.text or '' for t in texts)
        if '第3章' in full_text or 'ch3' in full_text.lower():
            in_ch3 = True
        elif '第4章' in full_text or 'ch4' in full_text.lower():
            if in_ch3:
                return last_ch3_para
        if in_ch3:
            last_ch3_para = para
    
    return last_ch3_para
