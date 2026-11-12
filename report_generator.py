"""
report_generator.py — Executive PDF Report Exporter
=====================================================
Generates modern, professional PDF analytics dossiers combining:
  - Header branding & execution timestamp
  - Plain-English AI executive takeaway
  - Executed MySQL query
  - Embedded high-res visual chart
  - Tabular summary of top query records
"""

import os
import pandas as pd
from fpdf import FPDF
from datetime import datetime


class ExecutiveReportPDF(FPDF):
    def header(self):
        # Top branding header
        self.set_fill_color(24, 25, 30)  # #18191E
        self.rect(0, 0, 210, 22, 'F')
        
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.set_xy(12, 6)
        self.cell(0, 10, 'AI DATA ANALYST — EXECUTIVE DOSSIER', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 9)
        self.set_text_color(148, 163, 184)
        self.set_xy(-65, 6)
        self.cell(0, 10, datetime.now().strftime("%b %d, %Y - %H:%M"), 0, 0, 'R')
        self.ln(18)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Confidential & Proprietary  |  Page {self.page_no()}', 0, 0, 'C')


def generate_executive_pdf(filepath, question, sql, text_summary, df, fig=None):
    """
    Build and save a clean PDF report.
    """
    pdf = ExecutiveReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # --- 1. Query Title & Meta ---
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(18, 19, 22)
    pdf.cell(0, 8, 'ANALYTICS QUERY BRIEF', ln=True)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(0, 6, f'Prompt: "{question}"')
    pdf.ln(3)
    
    # --- 2. AI Executive Summary Callout Box ---
    pdf.set_fill_color(240, 249, 255)  # Soft ice blue
    pdf.set_draw_color(186, 230, 253)
    pdf.set_line_width(0.4)
    
    # Measure box height
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(3, 105, 161)
    
    start_y = pdf.get_y()
    pdf.rect(12, start_y, 186, 30, 'DF')
    pdf.set_xy(16, start_y + 2)
    pdf.cell(0, 6, 'AI Natural Language Insight:', ln=True)
    
    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.set_x(16)
    summary_clean = text_summary.replace("💡", "").strip() if text_summary else "Direct query execution result."
    pdf.multi_cell(178, 5, summary_clean)
    
    pdf.set_y(start_y + 34)
    
    # --- 3. SQL Query Snippet ---
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, 'Executed MySQL 8.0 Statement:', ln=True)
    
    pdf.set_font('Courier', '', 8.5)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(30, 41, 59)
    pdf.multi_cell(0, 5, f' {sql} ', fill=True)
    pdf.ln(4)
    
    # --- 4. Embedded Chart (if available) ---
    temp_img_path = None
    if fig is not None:
        try:
            temp_img_path = os.path.join(os.path.dirname(filepath), "_temp_report_chart.png")
            fig.savefig(temp_img_path, dpi=180, facecolor=fig.get_facecolor(), bbox_inches='tight')
            pdf.image(temp_img_path, x=22, y=pdf.get_y(), w=166)
            pdf.ln(92)
        except Exception:
            pass
            
    # --- 5. Data Records Table ---
    if df is not None and not df.empty:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(18, 19, 22)
        pdf.cell(0, 6, f'Sample Output Records ({min(8, len(df))} of {len(df)} rows):', ln=True)
        pdf.ln(1)
        
        display_df = df.head(8)
        cols = list(display_df.columns)
        col_w = 186 / max(1, len(cols))
        
        # Table Header
        pdf.set_fill_color(30, 41, 59)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        for col in cols:
            pdf.cell(col_w, 6, str(col)[:16], border=1, fill=True, align='C')
        pdf.ln()
        
        # Table Rows
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(30, 41, 59)
        pdf.set_fill_color(248, 250, 252)
        fill = False
        for _, row in display_df.iterrows():
            for col in cols:
                val = str(row[col])[:18]
                pdf.cell(col_w, 5.5, val, border=1, fill=fill, align='C')
            pdf.ln()
            fill = not fill
            
    pdf.output(filepath)
    
    # Clean up temp image
    if temp_img_path and os.path.exists(temp_img_path):
        try:
            os.remove(temp_img_path)
        except Exception:
            pass
            
    return True
