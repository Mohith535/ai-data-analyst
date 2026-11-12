"""
chat_tab.py — AI Chat Tab UI (macOS Glass Polish)
===================================================
"""

import threading
import customtkinter as ctk
from tkinter import messagebox
import tkinter.ttk as ttk
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import db
import charts
import ai_chat


class ChatTab:
    """Manages the AI Chat tab with threading, auto-visualization, and text summary toggle."""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_canvas = None
        self.tree = None
        
        # --- Top Controls Card ---
        self.top_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.top_frame.pack(fill="x", padx=16, pady=(12, 6))
        
        row1 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 6))
        
        ctk.CTkLabel(row1, text="Active Context:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.table_var = ctk.StringVar(value="Select a table")
        self.table_dropdown = ctk.CTkOptionMenu(
            row1, variable=self.table_var, values=["Select a table"],
            width=200, fg_color="#262A34"
        )
        self.table_dropdown.pack(side="left", padx=(0, 10))
        
        self.btn_refresh = ctk.CTkButton(
            row1, text="🔄 Refresh", command=self._refresh_tables,
            width=90, height=30, fg_color="#2E3442", hover_color="#3B4254"
        )
        self.btn_refresh.pack(side="left", padx=(0, 20))
        
        # AI Text Summary Switch
        self.summary_mode_var = ctk.BooleanVar(value=True)
        self.switch_summary = ctk.CTkSwitch(
            row1,
            text="💡 Natural Language Insight Mode",
            variable=self.summary_mode_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color="#10B981"
        )
        self.switch_summary.pack(side="left", padx=(0, 15))
        
        # Row 2: Prompt bar
        row2 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(4, 10))
        
        self.entry_question = ctk.CTkEntry(
            row2,
            placeholder_text="Ask any question in English (e.g. 'Show total sales by category' or 'Explain customer risk counts')...",
            font=ctk.CTkFont(size=13),
            height=42,
            fg_color="#22252D",
            border_color="#2E3442"
        )
        self.entry_question.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_question.bind("<Return>", lambda event: self.ask_ai())
        
        self.btn_ask = ctk.CTkButton(
            row2,
            text="✨ Ask Analyst",
            command=self.ask_ai,
            width=150,
            height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.btn_ask.pack(side="left")
        
        # --- AI Insights & SQL Output Card ---
        self.response_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.response_frame.pack(fill="x", padx=16, pady=4)
        
        resp_header = ctk.CTkFrame(self.response_frame, fg_color="transparent")
        resp_header.pack(fill="x", padx=12, pady=(6, 2))
        
        ctk.CTkLabel(
            resp_header,
            text="🤖 AI Analyst Insight & Synthesized SQL",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#60A5FA"
        ).pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(
            resp_header, text="Ready", font=ctk.CTkFont(size=11), text_color="#94A3B8"
        )
        self.lbl_status.pack(side="right")
        
        # Summary Box
        self.txt_summary = ctk.CTkTextbox(
            self.response_frame,
            height=54,
            font=ctk.CTkFont(size=12),
            fg_color="#141820",
            text_color="#F1F5F9",
            wrap="word",
            corner_radius=8
        )
        self.txt_summary.pack(fill="x", padx=12, pady=(0, 4))
        self.txt_summary.insert("1.0", "💡 Type a question above to receive instant conversational insights.")
        self.txt_summary.configure(state="disabled")
        
        # SQL Box
        self.txt_sql = ctk.CTkTextbox(
            self.response_frame,
            height=36,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#0F1115",
            text_color="#34D399",
            corner_radius=8
        )
        self.txt_sql.pack(fill="x", padx=12, pady=(0, 8))
        self.txt_sql.insert("1.0", "-- Generated MySQL query will appear here...")
        self.txt_sql.configure(state="disabled")
        
        # --- Split Result Canvas Card ---
        self.output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.output_frame.pack(fill="both", expand=True, padx=16, pady=(4, 14))
        
        # Left Pane: Table
        self.table_box = ctk.CTkFrame(self.output_frame, fg_color="#18191E", corner_radius=12)
        self.table_box.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        ctk.CTkLabel(
            self.table_box, text="📋 Query Output",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0"
        ).pack(anchor="w", padx=12, pady=6)
        
        self.tree_container = ctk.CTkFrame(self.table_box, fg_color="transparent")
        self.tree_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        self.table_placeholder = ctk.CTkLabel(
            self.tree_container, text="Data records will populate here.", text_color="#64748B"
        )
        self.table_placeholder.pack(expand=True)
        
        # Right Pane: Auto-Chart
        self.chart_box = ctk.CTkFrame(self.output_frame, fg_color="#18191E", corner_radius=12)
        self.chart_box.pack(side="right", fill="both", expand=True, padx=(6, 0))
        
        ctk.CTkLabel(
            self.chart_box, text="📈 Automated Visualization",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#E2E8F0"
        ).pack(anchor="w", padx=12, pady=6)
        
        self.chart_container = ctk.CTkFrame(self.chart_box, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        self.chart_placeholder = ctk.CTkLabel(
            self.chart_container, text="Chart will auto-render from result dimensions.", text_color="#64748B"
        )
        self.chart_placeholder.pack(expand=True)
        
        self._refresh_tables()
        
    def _refresh_tables(self):
        tables = db.list_tables()
        if tables:
            self.table_dropdown.configure(values=tables)
            if self.table_var.get() not in tables:
                self.table_var.set(tables[0])
        else:
            self.table_dropdown.configure(values=["No tables found"])
            self.table_var.set("No tables found")
            
    def ask_ai(self):
        table = self.table_var.get()
        question = self.entry_question.get().strip()
        do_summary = self.summary_mode_var.get()
        
        if table in ("Select a table", "No tables found") or not question:
            messagebox.showwarning("Notice", "Select table context and type a query.")
            return
            
        self.btn_ask.configure(state="disabled", text="⏳ Synthesizing...")
        self.lbl_status.configure(text="Translating to SQL...", text_color="#F59E0B")
        
        worker = threading.Thread(
            target=self._process_ai_query,
            args=(table, question, do_summary),
            daemon=True
        )
        worker.start()
        
    def _process_ai_query(self, table, question, do_summary):
        schema = db.get_table_schema(table)
        sql, err = ai_chat.generate_sql(table, schema, question)
        if err:
            self.parent.after(0, self._handle_error, err)
            return
            
        df, db_err = db.run_query(sql)
        if db_err:
            self.parent.after(0, self._handle_error, f"SQL Execution Failed:\n{db_err}\n\nQuery:\n{sql}")
            return
            
        text_summary = None
        if do_summary:
            self.parent.after(0, lambda: self.lbl_status.configure(text="Generating Natural Language Takeaway...", text_color="#38BDF8"))
            text_summary = ai_chat.summarize_results(question, df)
            
        self.parent.after(0, self._update_ui_with_results, sql, df, text_summary)
        
    def _handle_error(self, error_message):
        self.btn_ask.configure(state="normal", text="✨ Ask Analyst")
        self.lbl_status.configure(text="Error", text_color="#EF4444")
        messagebox.showerror("AI Query Error", error_message)
        
    def _update_ui_with_results(self, sql, df, text_summary):
        self.btn_ask.configure(state="normal", text="✨ Ask Analyst")
        self.lbl_status.configure(text=f"Completed: {len(df)} row(s)", text_color="#10B981")
        
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("1.0", "end")
        if text_summary:
            self.txt_summary.insert("1.0", f"💡 {text_summary}")
        else:
            self.txt_summary.insert("1.0", "(Insight Mode is OFF. Toggle switch to view plain English summaries.)")
        self.txt_summary.configure(state="disabled")
        
        self.txt_sql.configure(state="normal")
        self.txt_sql.delete("1.0", "end")
        self.txt_sql.insert("1.0", sql)
        self.txt_sql.configure(state="disabled")
        
        self._display_table(df)
        self._display_chart(df)
        
    def _display_table(self, df):
        if self.tree is not None:
            self.tree.destroy()
        self.table_placeholder.pack_forget()
        
        if df is None or df.empty:
            self.table_placeholder.configure(text="Query returned 0 rows.")
            self.table_placeholder.pack(expand=True)
            return
            
        columns = list(df.columns)
        self.tree = ttk.Treeview(self.tree_container, columns=columns, show="headings", height=12)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#1E2026",
            foreground="#E2E8F0",
            fieldbackground="#1E2026",
            rowheight=26,
            font=('Segoe UI', 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#282D37",
            foreground="#F8FAFC",
            font=('Segoe UI', 10, 'bold')
        )
        style.map("Treeview", background=[("selected", "#3B82F6")])
        
        scroll_y = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self.tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w")
            self.tree.column(col, width=max(80, min(180, len(str(col)) * 11 + 20)), anchor="w")
            
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
        for _, row in df.head(100).iterrows():
            vals = [str(v) if v is not None else "" for v in row]
            self.tree.insert("", "end", values=vals)
            
    def _display_chart(self, df):
        if self.current_canvas is not None:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None
            
        self.chart_placeholder.pack_forget()
        
        fig = charts.create_auto_chart(df, title="AI Analysis Result")
        if fig is None:
            self.chart_placeholder.configure(text="No suitable columns found for auto-charting.")
            self.chart_placeholder.pack(expand=True)
            return
            
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
