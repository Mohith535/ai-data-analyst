"""
report_generator.py — Executive PDF Report Exporter (Unicode & Em-dash Safe)
=============================================================================
Fixes character encoding issues with standard fonts by sanitizing Unicode
punctuation (like em-dash '—', smart quotes, bullets) into clean Latin-1 equivalents.
"""

import os
import re
from fpdf import FPDF
from datetime import datetime


def clean_unicode_for_pdf(text):
    """
    Sanitize text to prevent FPDF latin-1 font crashes.
    Converts typographic quotes, em-dashes, and special symbols to ASCII.
    """
    if not text:
        return ""
    
    replacements = {
        "—": "-",    # Em dash
        "–": "-",    # En dash
        "“": '"',    # Left double quote
        "”": '"',    # Right double quote
        "‘": "'",    # Left single quote
        "’": "'",    # Right single quote
        "•": "*",    # Bullet
        "…": "...",  # Ellipsis
        "💡": "[Insight]",
        "●": "*",
        "⚡": "[Engine]",
        "📋": "[Data]",
        "📈": "[Chart]",
        "🤖": "[AI]"
    }
    
    clean = str(text)
    for char, rep in replacements.items():
        clean = clean.replace(char, rep)
        
    # Replace any other unsupported characters with standard ASCII
    clean = clean.encode('latin-1', 'replace').decode('latin-1')
    return clean


class ExecutiveReportPDF(FPDF):
    def header(self):
        self.set_fill_color(20, 20, 22)  # Linear obsidian
        self.rect(0, 0, 210, 20, 'F')
        
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 5)
        self.cell(0, 10, 'AI DATA ANALYST | EXECUTIVE DOSSIER', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(161, 161, 170)
        self.set_xy(-65, 5)
        self.cell(0, 10, datetime.now().strftime("%b %d, %Y - %H:%M"), 0, 0, 'R')
        self.ln(16)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(161, 161, 170)
        self.cell(0, 10, f'Confidential  |  Page {self.page_no()}', 0, 0, 'C')


def generate_executive_pdf(filepath, question, sql, text_summary, df, fig=None):
    """
    Build and save a clean PDF report with sanitized text.
    """
    pdf = ExecutiveReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Clean text inputs
    safe_question = clean_unicode_for_pdf(question)
    safe_sql = clean_unicode_for_pdf(sql)
    safe_summary = clean_unicode_for_pdf(text_summary)
    
    # 1. Title & Question
    pdf.set_font('Helvetica', 'B', 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, 'ANALYTICS QUERY BRIEF', ln=True)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 5.5, f'Prompt: "{safe_question}"')
    pdf.ln(3)
    
    # 2. Executive Insight Callout Box
    start_y = pdf.get_y()
    pdf.set_fill_color(244, 244, 245)  # Soft zinc card
    pdf.set_draw_color(228, 228, 231)
    pdf.set_line_width(0.3)
    pdf.rect(12, start_y, 186, 28, 'DF')
    
    pdf.set_xy(16, start_y + 2)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(94, 106, 210)  # Linear purple
    pdf.cell(0, 5.5, 'AI Plain-English Insight:', ln=True)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(24, 24, 27)
    pdf.set_x(16)
    pdf.multi_cell(178, 4.8, safe_summary if safe_summary else "Direct query execution result.")
    pdf.set_y(start_y + 32)
    
    # 3. SQL Query Snippet
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, 'Executed MySQL Statement:', ln=True)
    
    pdf.set_font('Courier', '', 8.5)
    pdf.set_fill_color(244, 244, 245)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 5, f' {safe_sql} ', fill=True)
    pdf.ln(4)
    
    # 4. Embedded Chart
    temp_img_path = None
    if fig is not None:
        try:
            temp_img_path = os.path.join(os.path.dirname(filepath), "_temp_report_chart.png")
            fig.savefig(temp_img_path, dpi=180, facecolor=fig.get_facecolor(), bbox_inches='tight')
            pdf.image(temp_img_path, x=20, y=pdf.get_y(), w=170)
            pdf.ln(92)
        except Exception:
            pass
            
    # 5. Output Table
    if df is not None and not df.empty:
        pdf.set_font('Helvetica', 'B', 9.5)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 6, f'Sample Data Records ({min(8, len(df))} of {len(df)} rows):', ln=True)
        pdf.ln(1)
        
        display_df = df.head(8)
        cols = list(display_df.columns)
        col_w = 186 / max(1, len(cols))
        
        # Header
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        for col in cols:
            safe_col = clean_unicode_for_pdf(str(col))[:16]
            pdf.cell(col_w, 6, safe_col, border=1, fill=True, align='C')
        pdf.ln()
        
        # Rows
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(30, 41, 59)
        pdf.set_fill_color(248, 250, 252)
        fill = False
        for _, row in display_df.iterrows():
            for col in cols:
                safe_val = clean_unicode_for_pdf(str(row[col]))[:18]
                pdf.cell(col_w, 5.5, safe_val, border=1, fill=fill, align='C')
            pdf.ln()
            fill = not fill
            
    pdf.output(filepath)
    
    if temp_img_path and os.path.exists(temp_img_path):
        try:
            os.remove(temp_img_path)
        except Exception:
            pass
            
    return True
