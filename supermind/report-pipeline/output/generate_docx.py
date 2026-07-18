#!/usr/bin/env python3
"""Generate DOCX from the markdown report for 北纬47度 brand research."""

import re
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

INPUT_MD = os.path.join(os.path.dirname(__file__), "content", "report_final_beiwei47.md")
OUTPUT_DOCX = os.path.join(os.path.dirname(__file__), "reports", "beiwei47_final.docx")

# ─── helpers ──────────────────────────────────────────────────

def set_cell_shading(cell, color="D9D9D9"):
    """Set cell background color."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_table_borders(table):
    """Set all borders on a table."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders = parse_xml(
        '<w:tblBorders %s>'
        '  <w:top w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '  <w:left w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '  <w:right w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        '</w:tblBorders>' % nsdecls("w")
    )
    tblPr.append(borders)

def style_header_row(row):
    """Style the header row: bold text, gray background."""
    for cell in row.cells:
        set_cell_shading(cell, "D9D9D9")
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10)
                run.font.name = "等线"

def set_paragraph_spacing(paragraph, line_spacing=1.5, space_after=Pt(4)):
    """Set paragraph spacing."""
    pf = paragraph.paragraph_format
    pf.line_spacing = line_spacing
    pf.space_after = space_after

def add_styled_paragraph(doc, text, style="Normal", bold=False, size=10.5, alignment=None, color=None):
    """Add a paragraph with consistent styling."""
    p = doc.add_paragraph(style=style)
    run = p.add_run(text)
    run.font.name = "等线"
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color
    if alignment is not None:
        p.alignment = alignment
    set_paragraph_spacing(p)
    return p

def add_heading_styled(doc, text, level=1):
    """Add a heading with proper font."""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "等线"
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    return h

def parse_markdown_table(md_text_block):
    """Parse a markdown table into list of lists (rows of cells)."""
    lines = md_text_block.strip().split('\n')
    # Filter out empty lines and separator lines
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^[\|\-\s\:]+$', stripped):  # separator line
            continue
        if stripped.startswith('|') and stripped.endswith('|'):
            data_lines.append(stripped)
    
    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        rows.append(cells)
    return rows

def add_table_from_md(doc, md_text_block):
    """Add a formatted docx table from a markdown table block."""
    rows_data = parse_markdown_table(md_text_block)
    if not rows_data:
        return None
    
    max_cols = max(len(row) for row in rows_data)
    table = doc.add_table(rows=len(rows_data), cols=max_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    for i, row_data in enumerate(rows_data):
        row = table.rows[i]
        # Pad row_data if shorter
        while len(row_data) < max_cols:
            row_data.append("")
        for j, cell_text in enumerate(row_data):
            cell = row.cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(cell_text)
            run.font.name = "等线"
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
            run.font.size = Pt(9)
            set_paragraph_spacing(p, line_spacing=1.2, space_after=Pt(2))
            if i == 0:
                run.bold = True
                set_cell_shading(cell, "D9D9D9")
    
    # Add blank para after table
    doc.add_paragraph()
    return table

def process_markdown_to_docx(md_path, docx_path):
    """Convert the markdown report to a styled DOCX."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    doc = Document()
    
    # ── Page setup ──
    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.18)
        section.right_margin = Cm(3.18)
    
    # ── Default style ──
    style = doc.styles['Normal']
    font = style.font
    font.name = "等线"
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
    font.size = Pt(10.5)
    pf = style.paragraph_format
    pf.line_spacing = 1.5
    
    # ── COVER PAGE ──
    # Add empty paragraphs for spacing
    for _ in range(6):
        doc.add_paragraph()
    
    add_styled_paragraph(doc, "北纬47度", bold=True, size=28, 
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, 
                         color=RGBColor(0x1B, 0x3A, 0x2A))
    
    add_styled_paragraph(doc, "品牌竞品研究咨询报告", bold=True, size=22,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER,
                         color=RGBColor(0x1B, 0x3A, 0x2A))
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    add_styled_paragraph(doc, "行业：鲜食玉米 / 农产品品牌化", size=12,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_styled_paragraph(doc, "框架版本：V5 五维模型", size=12,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_styled_paragraph(doc, "出品：燃创咨询 BreaC Lab", size=12,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    add_styled_paragraph(doc, "日期：2026年7月", size=12,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)
    
    # Page break after cover
    doc.add_page_break()
    
    # ── MAIN CONTENT ──
    # Strategy: parse the markdown line by line
    lines = content.split('\n')
    i = 0
    in_table = False
    table_buffer = []
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Handle table blocks
        if stripped.startswith('|') and stripped.endswith('|'):
            in_table = True
            table_buffer.append(line)
            i += 1
            continue
        elif in_table:
            # Check if next line is still part of table
            if stripped.startswith('|') or re.match(r'^[\|\-\s\:]+$', stripped):
                table_buffer.append(line)
                i += 1
                continue
            else:
                # Flush table
                table_md = '\n'.join(table_buffer)
                add_table_from_md(doc, table_md)
                table_buffer = []
                in_table = False
                # continue processing current line
        
        # Horizontal rule -> page break before major sections
        if stripped == '---':
            # Check if near a major section (Chapter start)
            doc.add_paragraph()
            i += 1
            continue
        
        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            # Clean heading text - remove markdown bold/italic markers
            heading_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', heading_text)
            heading_text = re.sub(r'\*([^*]+)\*', r'\1', heading_text)
            heading_text = re.sub(r'__([^_]+)__', r'\1', heading_text)
            heading_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', heading_text)
            
            # Add page break before chapter headings (level 1)
            if level == 1 and i > 10:  # not first heading
                doc.add_page_break()
            
            add_heading_styled(doc, heading_text, level=min(level, 4))
            i += 1
            continue
        
        # Bold text paragraphs (starting with **)
        bold_p_match = re.match(r'^\*\*(.+?)\*\*[：:]?\s*(.*)', stripped)
        if bold_p_match:
            p = doc.add_paragraph()
            run1 = p.add_run(bold_p_match.group(1))
            run1.bold = True
            run1.font.name = "等线"
            run1._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
            run1.font.size = Pt(10.5)
            if bold_p_match.group(2):
                run2 = p.add_run(bold_p_match.group(2))
                run2.font.name = "等线"
                run2._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
                run2.font.size = Pt(10.5)
            set_paragraph_spacing(p)
            i += 1
            continue
        
        # Regular paragraph (skip empty lines, metadata lines)
        if stripped and not stripped.startswith('>'):
            # Clean inline markdown
            para_text = stripped
            para_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', para_text)
            para_text = re.sub(r'__([^_]+)__', r'\1', para_text)
            para_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', para_text)
            para_text = re.sub(r'`([^`]+)`', r'\1', para_text)
            
            if para_text:
                p = doc.add_paragraph()
                run = p.add_run(para_text)
                run.font.name = "等线"
                run._element.rPr.rFonts.set(qn('w:eastAsia'), '等线')
                run.font.size = Pt(10.5)
                set_paragraph_spacing(p)
        
        i += 1
    
    # Flush remaining table
    if table_buffer:
        table_md = '\n'.join(table_buffer)
        add_table_from_md(doc, table_md)
    
    # ── Save ──
    os.makedirs(os.path.dirname(docx_path), exist_ok=True)
    doc.save(docx_path)
    return docx_path

if __name__ == "__main__":
    path = process_markdown_to_docx(INPUT_MD, OUTPUT_DOCX)
    size_kb = os.path.getsize(path) / 1024
    print(f"DOCX saved to: {path}")
    print(f"File size: {size_kb:.1f} KB")
    if size_kb > 50:
        print("✓ File size > 50KB — PASS")
    else:
        print(f"⚠ File size {size_kb:.1f} KB < 50KB — check content")
