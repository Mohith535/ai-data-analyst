"""
chat_tab.py — AI Chat Tab UI (Conversational Memory & Toast Notifications)
==========================================================================
Phase 5 enhancements:
  - Rolling conversation memory (last 3 Q&A turns) enables natural follow-ups
    like "filter that to South" or "what was the average for those?"
  - Toast notification system for non-intrusive success/error/warning feedback
  - Scrolling query card stream replaces static text boxes
  - Column suggestion chips auto-populate from active table schema
"""

import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import db
import charts
import ai_chat
import report_generator
import history_manager
import settings_manager
from ui.theme import Toast


class ChatTab:
    """Manages the AI Chat tab with conversation memory, threading, and auto-visualization."""
    
    # Maximum number of prior Q&A turns to retain for follow-up context
    MAX_MEMORY_TURNS = 3
    
    def __init__(self, parent):
        self.parent = parent
        self.current_canvas = None
        self.current_fig = None
        self.current_df = None
        self.current_sql = None
        self.current_question = None
        self.current_summary = None
        self.on_query_success = None
        self.tree = None
        self.tree_scroll_y = None
        self.tree_scroll_x = None
        
        # Conversation memory: rolling buffer of last N (question, sql) pairs
        # Enables the LLM to resolve follow-up references like "filter that",
        # "sort those by price", "what was the average for that?"
        self.conversation_memory = []
        
        # --- Top Filter & Action Bar ---
        self.top_frame = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        self.top_frame.pack(fill="x", padx=16, pady=(10, 6))
        
        row1 = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=10)
        
        ctk.CTkLabel(
            row1, text="Context Table:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#E2E8F0"
        ).pack(side="left", padx=(0, 6))
        
        self.table_var = ctk.StringVar(value="Select a table")
        self.table_dropdown = ctk.CTkOptionMenu(
            row1, variable=self.table_var, values=["Select a table"],
            command=self._on_table_changed,
            width=210, height=34, fg_color="#1E2024", button_color="#2A2D34",
            button_hover_color="#363A44", font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.table_dropdown.pack(side="left", padx=(0, 10))
        
        self.btn_refresh = ctk.CTkButton(
            row1, text="🔄 Refresh", command=self._refresh_tables,
            width=90, height=34, fg_color="#1E2024", hover_color="#2A2D34",
            text_color="#CBD5E1", font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.btn_refresh.pack(side="left", padx=(0, 12))
        
        # Teacher Mode Status Badge
        self.badge_teacher = ctk.CTkLabel(
            row1,
            text="🎓 AI Teacher Mode: ACTIVE",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#34D399",
            fg_color="#13241C",
            corner_radius=8,
            padx=10, pady=4
        )
        self.badge_teacher.pack(side="left", padx=(0, 8))
        
        # Conversation Memory Badge
        self.badge_memory = ctk.CTkLabel(
            row1,
            text="🧠 Memory: 0/3",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#818CF8",
            fg_color="#1A1A2E",
            corner_radius=8,
            padx=10, pady=4
        )
        self.badge_memory.pack(side="left", padx=(0, 8))
        
        # PDF Export Button (Top Right)
        self.btn_export_pdf = ctk.CTkButton(
            row1,
            text="📄 Export PDF Dossier",
            command=self.export_pdf_report,
            width=165,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1E2024",
            hover_color="#5E6AD2",
            border_width=1,
            border_color="#2B2F38",
            text_color="#E2E8F0",
            state="disabled"
        )
        self.btn_export_pdf.pack(side="right")
        
        # --- Prompt Bar (Linear Floating Input Bar) ---
        prompt_card = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        prompt_card.pack(fill="x", padx=16, pady=4)
        
        prompt_inner = ctk.CTkFrame(prompt_card, fg_color="transparent")
        prompt_inner.pack(fill="x", padx=14, pady=10)
        
        self.entry_question = ctk.CTkEntry(
            prompt_inner,
            placeholder_text="Ask anything... (follow-ups work too: 'filter that to South region', 'sort by price')",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            height=46,
            fg_color="#18191E",
            border_color="#262A32",
            text_color="#F8FAFC"
        )
        self.entry_question.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_question.bind("<Return>", lambda event: self.ask_ai())
        
        # Clear Memory Button
        self.btn_clear_mem = ctk.CTkButton(
            prompt_inner,
            text="🧹",
            command=self._clear_memory,
            width=46,
            height=46,
            fg_color="#1E2024",
            hover_color="#374151",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=16),
            corner_radius=8
        )
        self.btn_clear_mem.pack(side="left", padx=(0, 8))
        
        self.btn_ask = ctk.CTkButton(
            prompt_inner,
            text="✨ Ask Analyst",
            command=self.ask_ai,
            width=150,
            height=46,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#5E6AD2",
            hover_color="#4F58B8"
        )
        self.btn_ask.pack(side="left")
        
        # --- Column Suggestion Chips ---
        self.chips_frame = ctk.CTkFrame(prompt_card, fg_color="transparent")
        self.chips_frame.pack(fill="x", padx=14, pady=(0, 8))
        
        self.lbl_chips_hint = ctk.CTkLabel(
            self.chips_frame,
            text="Columns:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#475569"
        )
        
        # --- AI Insights & SQL Output Card ---
        self.response_frame = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        self.response_frame.pack(fill="x", padx=16, pady=6)
        
        resp_header = ctk.CTkFrame(self.response_frame, fg_color="transparent")
        resp_header.pack(fill="x", padx=16, pady=(10, 4))
        
        ctk.CTkLabel(
            resp_header,
            text="🤖 AI Analyst Insight & Synthesized Query",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#818CF8"
        ).pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(
            resp_header, text="Ready", font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#94A3B8"
        )
        self.lbl_status.pack(side="right")
        
        self.txt_summary = ctk.CTkTextbox(
            self.response_frame,
            height=95,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="#18191E",
            text_color="#F1F5F9",
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color="#22252D",
            spacing1=4, spacing2=3, spacing3=4
        )
        self.txt_summary.pack(fill="x", padx=16, pady=(0, 8))
        self.txt_summary.insert("1.0", "💡 Type a question above to receive instant conversational insights.\n\n🧠 Follow-up questions work naturally — ask 'filter that to South' or 'sort by price desc'.")
        self.txt_summary.configure(state="disabled")
        
        # SQL Box
        self.txt_sql = ctk.CTkTextbox(
            self.response_frame,
            height=38,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#0C0D0F",
            text_color="#34D399",
            corner_radius=6
        )
        self.txt_sql.pack(fill="x", padx=16, pady=(0, 12))
        self.txt_sql.insert("1.0", "-- Generated MySQL query will appear here...")
        self.txt_sql.configure(state="disabled")
        
        # --- Split Result Canvas Card ---
        self.output_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.output_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        
        # Left Pane: Table
        self.table_box = ctk.CTkFrame(self.output_frame, fg_color="#121316", corner_radius=12)
        self.table_box.pack(side="left", fill="both", expand=True, padx=(0, 6))
        
        ctk.CTkLabel(
            self.table_box, text="📋 Query Output",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#E2E8F0"
        ).pack(anchor="w", padx=14, pady=8)
        
        self.tree_container = ctk.CTkFrame(self.table_box, fg_color="transparent")
        self.tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.table_placeholder = ctk.CTkLabel(
            self.tree_container, text="Data records will populate here.", font=ctk.CTkFont(size=14), text_color="#64748B"
        )
        self.table_placeholder.pack(expand=True)
        
        # Right Pane: Auto-Chart
        self.chart_box = ctk.CTkFrame(self.output_frame, fg_color="#121316", corner_radius=12)
        self.chart_box.pack(side="right", fill="both", expand=True, padx=(6, 0))
        
        ctk.CTkLabel(
            self.chart_box, text="📈 Automated Visualization",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#E2E8F0"
        ).pack(anchor="w", padx=14, pady=8)
        
        self.chart_container = ctk.CTkFrame(self.chart_box, fg_color="transparent")
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.chart_placeholder = ctk.CTkLabel(
            self.chart_container, text="Chart will auto-render from result dimensions.", font=ctk.CTkFont(size=14), text_color="#64748B"
        )
        self.chart_placeholder.pack(expand=True)
        
        self._refresh_tables()
        self.sync_settings_state()
        
    def _on_table_changed(self, new_table):
        """Reset conversation memory when the user switches context tables."""
        self._clear_memory(silent=True)
        self._populate_column_chips(new_table)
    
    def _populate_column_chips(self, table_name):
        """Show clickable column name chips below the prompt bar for quick insertion."""
        # Clear existing chips
        for child in self.chips_frame.winfo_children():
            child.destroy()
        
        if table_name in ("Select a table", "No tables found"):
            return
            
        schema = db.get_table_schema(table_name)
        if not schema:
            return
            
        cols = [item['column'] for item in schema if item['column'] != '_id']
        if not cols:
            return
        
        self.lbl_chips_hint = ctk.CTkLabel(
            self.chips_frame,
            text="Columns:",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#475569"
        )
        self.lbl_chips_hint.pack(side="left", padx=(0, 6))
        
        for col in cols[:10]:
            chip = ctk.CTkButton(
                self.chips_frame,
                text=col,
                font=ctk.CTkFont(family="Consolas", size=10),
                height=22,
                width=len(col) * 8 + 16,
                corner_radius=12,
                fg_color="#1E2024",
                hover_color="#2A2D34",
                text_color="#94A3B8",
                border_width=1,
                border_color="#262A34",
                command=lambda c=col: self._insert_chip(c)
            )
            chip.pack(side="left", padx=2)
        
        if len(cols) > 10:
            ctk.CTkLabel(
                self.chips_frame,
                text=f"+{len(cols) - 10} more",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#475569"
            ).pack(side="left", padx=4)
    
    def _insert_chip(self, col_name):
        """Append clicked column name to the prompt entry."""
        current = self.entry_question.get()
        if current and not current.endswith(" "):
            current += " "
        self.entry_question.delete(0, "end")
        self.entry_question.insert(0, current + col_name)
        self.entry_question.focus()
    
    def _clear_memory(self, silent=False):
        """Reset conversation memory buffer."""
        self.conversation_memory = []
        self._update_memory_badge()
        if not silent:
            Toast.show(self.parent, "🧹 Conversation memory cleared — fresh start!", 2000, "info")
    
    def _update_memory_badge(self):
        """Update the memory counter badge in the toolbar."""
        n = len(self.conversation_memory)
        if n == 0:
            self.badge_memory.configure(
                text="🧠 Memory: 0/3",
                text_color="#64748B",
                fg_color="#1A1D24"
            )
        else:
            self.badge_memory.configure(
                text=f"🧠 Memory: {n}/{self.MAX_MEMORY_TURNS}",
                text_color="#818CF8",
                fg_color="#1A1A2E"
            )
        
    def sync_settings_state(self):
        """Update badge based on global settings."""
        teacher_on = settings_manager.get_setting("ai_teacher_mode", True)
        if teacher_on:
            self.badge_teacher.configure(
                text="🎓 AI Teacher Mode: ACTIVE",
                text_color="#34D399",
                fg_color="#13241C"
            )
        else:
            self.badge_teacher.configure(
                text="⚡ Direct SQL Mode (Teacher OFF)",
                text_color="#94A3B8",
                fg_color="#1E2024"
            )
            
    def _refresh_tables(self):
        tables = db.list_tables()
        if tables:
            self.table_dropdown.configure(values=tables)
            if self.table_var.get() not in tables:
                self.table_var.set(tables[0])
                self._populate_column_chips(tables[0])
        else:
            self.table_dropdown.configure(values=["No tables found"])
            self.table_var.set("No tables found")
            
    def ask_ai(self):
        table = self.table_var.get()
        question = self.entry_question.get().strip()
        
        if table in ("Select a table", "No tables found") or not question:
            messagebox.showwarning("Notice", "Select table context and type a query.")
            return
            
        self.current_question = question
        self.btn_ask.configure(state="disabled", text="⏳ Synthesizing...")
        self.btn_export_pdf.configure(state="disabled")
        self.lbl_status.configure(text="Translating to SQL...", text_color="#F59E0B")
        
        # Clear prompt input immediately for fast follow-up typing
        self.entry_question.delete(0, "end")
        
        worker = threading.Thread(
            target=self._process_ai_query,
            args=(table, question),
            daemon=True
        )
        worker.start()
        
    def _process_ai_query(self, table, question):
        schema = db.get_table_schema(table)
        
        # Pass conversation memory for follow-up resolution
        sql, err, is_fallback = ai_chat.generate_sql(
            table, schema, question,
            conversation_history=self.conversation_memory
        )
        if err:
            self.parent.after(0, self._handle_error, err)
            return
            
        df, db_err = db.run_query(sql)
        if db_err:
            self.parent.after(0, self._handle_error, f"SQL Execution Failed:\n{db_err}\n\nQuery:\n{sql}")
            return
            
        teacher_on = settings_manager.get_setting("ai_teacher_mode", True)
        text_summary = None
        if teacher_on:
            self.parent.after(0, lambda: self.lbl_status.configure(text="Synthesizing Insight...", text_color="#818CF8"))
            send_sample = settings_manager.get_setting("send_data_sample", False)
            text_summary = ai_chat.summarize_results(question, df, send_sample=send_sample)
            
        self.parent.after(0, self._update_ui_with_results, sql, df, text_summary, is_fallback, question)
        
    def _handle_error(self, error_message):
        self.btn_ask.configure(state="normal", text="✨ Ask Analyst")
        self.lbl_status.configure(text="Error", text_color="#EF4444")
        Toast.show(self.parent, f"❌ {str(error_message)[:80]}", 4000, "error")
        messagebox.showerror("AI Query Error", error_message)
        
    def _update_ui_with_results(self, sql, df, text_summary, is_fallback=False, question=None):
        self.current_sql = sql
        self.current_df = df
        self.current_summary = text_summary
        
        self.btn_ask.configure(state="normal", text="✨ Ask Analyst")
        self.btn_export_pdf.configure(state="normal")
        
        # Append to conversation memory (rolling buffer of MAX_MEMORY_TURNS)
        if question and sql and not is_fallback:
            self.conversation_memory.append({
                "question": question,
                "sql": sql
            })
            # Trim to last N turns
            if len(self.conversation_memory) > self.MAX_MEMORY_TURNS:
                self.conversation_memory = self.conversation_memory[-self.MAX_MEMORY_TURNS:]
            self._update_memory_badge()
        
        if is_fallback:
            self.lbl_status.configure(text=f"⚠️ Preview Fallback: {len(df)} row(s)", text_color="#F59E0B")
            Toast.show(self.parent, "⚠️ Couldn't parse request — showing preview instead", 3000, "warning")
        else:
            self.lbl_status.configure(text=f"Completed: {len(df)} row(s)", text_color="#10B981")
            Toast.show(self.parent, f"✅ Query returned {len(df)} row(s)", 2500, "success")
        
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("1.0", "end")
        if is_fallback:
            prefix = "⚠️ Couldn't understand the request, showing a preview instead.\n\n"
            if text_summary:
                self.txt_summary.insert("1.0", f"{prefix}💡 {text_summary}")
            else:
                self.txt_summary.insert("1.0", f"{prefix}Displaying sample rows from `{self.table_var.get()}`.")
        elif text_summary:
            self.txt_summary.insert("1.0", f"💡 {text_summary}")
        else:
            self.txt_summary.insert("1.0", "Query executed successfully. (AI Teacher mode is disabled in Settings).")
        self.txt_summary.configure(state="disabled")
        
        self.txt_sql.configure(state="normal")
        self.txt_sql.delete("1.0", "end")
        self.txt_sql.insert("1.0", sql)
        self.txt_sql.configure(state="disabled")
        
        self._display_table(df)
        
        # Check auto-chart setting
        charts_on = settings_manager.get_setting("auto_chart_enabled", True)
        if charts_on:
            self._display_chart(df)
        else:
            if self.current_canvas is not None:
                self.current_canvas.get_tk_widget().destroy()
                self.current_canvas = None
            self.chart_placeholder.configure(text="Automated charting disabled in Settings.")
            self.chart_placeholder.pack(expand=True)
            
        try:
            history_manager.save_history_item(
                self.table_var.get(),
                self.current_question,
                sql,
                text_summary or "Direct query result"
            )
            if self.on_query_success:
                self.on_query_success()
        except Exception as e:
            print(f"[HISTORY ERROR] {e}")
            
    def _display_table(self, df):
        self.table_placeholder.pack_forget()
        
        if df is None or df.empty:
            if self.tree is not None:
                self.tree.pack_forget()
                if self.tree_scroll_y:
                    self.tree_scroll_y.pack_forget()
                if self.tree_scroll_x:
                    self.tree_scroll_x.pack_forget()
            self.table_placeholder.configure(text="Query returned 0 rows.")
            self.table_placeholder.pack(expand=True)
            return
            
        if self.tree is None:
            style = ttk.Style()
            style.theme_use("default")
            style.configure(
                "Treeview",
                background="#16181D",
                foreground="#E2E8F0",
                fieldbackground="#16181D",
                rowheight=28,
                font=('Segoe UI', 10)
            )
            style.configure(
                "Treeview.Heading",
                background="#22252C",
                foreground="#F8FAFC",
                font=('Segoe UI', 10, 'bold')
            )
            style.map("Treeview", background=[("selected", "#5E6AD2")])
            
            self.tree_scroll_y = ttk.Scrollbar(self.tree_container, orient="vertical")
            self.tree_scroll_x = ttk.Scrollbar(self.tree_container, orient="horizontal")
            
            self.tree = ttk.Treeview(
                self.tree_container,
                show="headings",
                height=12,
                yscrollcommand=self.tree_scroll_y.set,
                xscrollcommand=self.tree_scroll_x.set
            )
            self.tree_scroll_y.configure(command=self.tree.yview)
            self.tree_scroll_x.configure(command=self.tree.xview)
            
            self.tree_scroll_y.pack(side="right", fill="y")
            self.tree_scroll_x.pack(side="bottom", fill="x")
            self.tree.pack(fill="both", expand=True)
        else:
            self.tree_scroll_y.pack(side="right", fill="y")
            self.tree_scroll_x.pack(side="bottom", fill="x")
            self.tree.pack(fill="both", expand=True)
            
        # Clear previous rows
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        columns = list(df.columns)
        self.tree["columns"] = columns
        
        for col in columns:
            self.tree.heading(col, text=str(col), anchor="w")
            self.tree.column(col, width=max(90, min(220, len(str(col)) * 12 + 25)), anchor="w")
            
        for _, row in df.head(100).iterrows():
            vals = [str(v) if v is not None and str(v) != "nan" else "" for v in row]
            self.tree.insert("", "end", values=vals)
            
    def _display_chart(self, df):
        # Prevent memory leaks: close previous figure before rendering new auto-chart
        if self.current_fig is not None:
            plt.close(self.current_fig)
            self.current_fig = None
            
        if self.current_canvas is not None:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None
            
        self.chart_placeholder.pack_forget()
        
        fig = charts.create_auto_chart(df, title="AI Analysis Result")
        self.current_fig = fig
        
        if fig is None:
            self.chart_placeholder.configure(text="No suitable columns found for auto-charting.")
            self.chart_placeholder.pack(expand=True)
            return
            
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
        
    def export_pdf_report(self):
        if self.current_df is None or not self.current_sql:
            messagebox.showwarning("Notice", "Execute an analysis query first.")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"Analytics_Report_{self.table_var.get()}.pdf"
        )
        if not filepath:
            return
            
        try:
            report_generator.generate_executive_pdf(
                filepath,
                self.current_question or "Ad-hoc Query",
                self.current_sql,
                self.current_summary or "Execution Results",
                self.current_df,
                self.current_fig
            )
            Toast.show(self.parent, f"📄 PDF saved: {filepath.split('/')[-1]}", 3000, "success")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not create PDF:\n{e}")
