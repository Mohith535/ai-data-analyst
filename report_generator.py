"""
report_generator.py — Executive PDF Report Exporter (Perfect Multi-page Flow)
=============================================================================
Architecture:
  - Clean 2-Page Executive Briefing Flow:
      * Page 1: Executive Title, Metadata, AI Takeaway card, Executed SQL, Sample Records Table
      * Page 2: High-Resolution Embedded Visual Chart (Centered, Zero overlapping)
  - Full Unicode Sanitization for standard PDF fonts
"""

import os
from fpdf import FPDF
from datetime import datetime


def clean_unicode_for_pdf(text):
    """Sanitize text to prevent FPDF latin-1 font crashes."""
    if not text:
        return ""
    replacements = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "*", "…": "...", "💡": "[Insight]", "●": "*", "⚡": "[Engine]",
        "📋": "[Data]", "📈": "[Chart]", "🤖": "[AI]"
    }
    clean = str(text)
    for char, rep in replacements.items():
        clean = clean.replace(char, rep)
    return clean.encode('latin-1', 'replace').decode('latin-1')


class ExecutiveReportPDF(FPDF):
    def header(self):
        self.set_fill_color(18, 19, 22)  # Obsidian header
        self.rect(0, 0, 210, 18, 'F')
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(14, 4)
        self.cell(0, 10, 'AI DATA ANALYST | EXECUTIVE DOSSIER', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(161, 161, 170)
        self.set_xy(-70, 4)
        self.cell(0, 10, datetime.now().strftime("%b %d, %Y - %H:%M"), 0, 0, 'R')
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Confidential Analytics Briefing  |  Page {self.page_no()}', 0, 0, 'C')


def generate_executive_pdf(filepath, question, sql, text_summary, df, fig=None):
    """
    Build and save a clean, professional multi-page PDF report with zero overlap.
    """
    pdf = ExecutiveReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ================= PAGE 1: EXECUTIVE BRIEF & DATA =================
    pdf.add_page()
    
    # 1. Title & Question Section
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, 'EXECUTIVE ANALYTICS BRIEF', ln=True)
    
    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 5, f'Query Prompt: "{clean_unicode_for_pdf(question)}"')
    pdf.ln(3)
    
    # 2. AI Executive Takeaway Box (Dynamic height calculation)
    safe_summary = clean_unicode_for_pdf(text_summary) or "Direct query execution result."
    
    start_y = pdf.get_y()
    pdf.set_fill_color(248, 250, 252)  # Crisp card background
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    
    # Calculate text height for the box
    pdf.set_font('Helvetica', '', 9.5)
    # Estimate height based on length
    box_height = max(26, 12 + (len(safe_summary) // 85) * 5)
    pdf.rect(14, start_y, 182, box_height, 'DF')
    
    pdf.set_xy(18, start_y + 3)
    pdf.set_font('Helvetica', 'B', 9.5)
    pdf.set_text_color(94, 106, 210)  # Linear Indigo
    pdf.cell(0, 5, 'AI Plain-English Takeaway:', ln=True)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(30, 41, 59)
    pdf.set_x(18)
    pdf.multi_cell(174, 4.5, safe_summary)
    
    pdf.set_y(start_y + box_height + 5)
    
    # 3. Executed SQL Codebox
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, 'Executed MySQL Statement:', ln=True)
    
    pdf.set_font('Courier', '', 8.5)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(15, 23, 42)
    safe_sql = clean_unicode_for_pdf(sql)
    pdf.multi_cell(0, 5, f'  {safe_sql}  ', fill=True)
    pdf.ln(5)
    
    # 4. Output Data Table
    if df is not None and not df.empty:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(15, 23, 42)
        display_rows = min(10, len(df))
        pdf.cell(0, 6, f'Query Results Preview ({display_rows} of {len(df)} records):', ln=True)
        pdf.ln(1)
        
        display_df = df.head(display_rows)
        cols = list(display_df.columns)
        col_w = 182 / max(1, len(cols))
        
        # Table Header
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        for col in cols:
            safe_col = clean_unicode_for_pdf(str(col))[:16]
            pdf.cell(col_w, 6, safe_col, border=1, fill=True, align='C')
        pdf.ln()
        
        # Table Body
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(30, 41, 59)
        pdf.set_fill_color(248, 250, 252)
        fill = False
        for _, row in display_df.iterrows():
            for col in cols:
                val = clean_unicode_for_pdf(str(row[col]))[:18]
                pdf.cell(col_w, 5.5, val, border=1, fill=fill, align='C')
            pdf.ln()
            fill = not fill

    # ================= PAGE 2: VISUAL ANALYTICS CANVAS =================
    temp_img_path = None
    if fig is not None:
        pdf.add_page()
        
        pdf.set_font('Helvetica', 'B', 13)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, 'AUTOMATED VISUAL ANALYTICS', ln=True)
        
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 5, 'High-resolution visualization generated directly from query result dimensions.', ln=True)
        pdf.ln(6)
        
        try:
            temp_img_path = os.path.join(os.path.dirname(filepath), "_temp_report_chart.png")
            fig.savefig(temp_img_path, dpi=200, facecolor=fig.get_facecolor(), bbox_inches='tight')
            # Center image cleanly on Page 2 with ample margins
            pdf.image(temp_img_path, x=15, y=pdf.get_y(), w=180)
        except Exception:
            pass

    pdf.output(filepath)
    
    # Cleanup temp file
    if temp_img_path and os.path.exists(temp_img_path):
        try:
            os.remove(temp_img_path)
        except Exception:
            pass
            
    return True
