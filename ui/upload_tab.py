"""
upload_tab.py — Upload Tab UI (macOS Glass Polish)
===================================================
Modern card layout, rounded action buttons, enhanced preview table styling.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import pandas as pd
import os
import db


class UploadTab:
    """Manages the Upload tab of the application."""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_df = None
        self.current_filename = None
        
        # --- Top Action Card ---
        self.top_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.top_frame.pack(fill="x", padx=16, pady=(12, 6))
        
        btn_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=10)
        
        # Select CSV Button
        self.btn_select = ctk.CTkButton(
            btn_row,
            text="📂  Choose CSV File",
            command=self.select_file,
            width=170,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            corner_radius=8
        )
        self.btn_select.pack(side="left", padx=(0, 10))
        
        # Save to MySQL Button
        self.btn_save = ctk.CTkButton(
            btn_row,
            text="💾  Save to MySQL",
            command=self.save_to_mysql,
            width=170,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            state="disabled",
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=8
        )
        self.btn_save.pack(side="left", padx=(0, 15))
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(
            btn_row,
            text="Select any dataset to begin previewing",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.lbl_status.pack(side="left", padx=5)
        
        # --- Metadata Stats Pill Bar ---
        self.info_frame = ctk.CTkFrame(parent, fg_color="#22252D", corner_radius=8)
        self.info_frame.pack(fill="x", padx=16, pady=4)
        
        self.lbl_info = ctk.CTkLabel(
            self.info_frame,
            text="⚡ No dataset loaded into memory yet.",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#CBD5E1",
            justify="left"
        )
        self.lbl_info.pack(padx=14, pady=6, anchor="w")
        
        # --- Table Preview Frame ---
        self.table_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        
        self.tree = None
        self.tree_scroll_y = None
        self.tree_scroll_x = None
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.table_frame,
            text="📊 Dataset Preview Canvas\n\nClick 'Choose CSV File' to inspect rows, schema & types.",
            font=ctk.CTkFont(size=15),
            text_color="#64748B"
        )
        self.placeholder.pack(expand=True)
    
    def select_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a CSV dataset",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filepath:
            return
            
        try:
            df = pd.read_csv(filepath)
            if df.empty:
                messagebox.showwarning("Empty File", "This CSV file contains 0 rows.")
                return
            if len(df.columns) < 2:
                messagebox.showwarning("Notice", "Dataset has only 1 column.")
                return
                
            self.current_df = df
            self.current_filename = os.path.basename(filepath)
            
            self.lbl_status.configure(
                text=f"Loaded: {self.current_filename}",
                text_color="#34D399"
            )
            
            rows, cols = df.shape
            mem = df.memory_usage(deep=True).sum()
            mem_str = f"{mem / (1024*1024):.1f} MB" if mem > 1024 * 1024 else f"{mem / 1024:.1f} KB"
            target_table = db.sanitize_table_name(self.current_filename)
            
            info_text = f"📋 Rows: {rows:,}  |  Columns: {cols}  |  RAM: {mem_str}  |  Target Table: `{target_table}`"
            self.lbl_info.configure(text=info_text, text_color="#F8FAFC")
            
            self.btn_save.configure(state="normal")
            self._display_dataframe(df)
            
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to load file:\n{e}")
            
    def _display_dataframe(self, df, max_rows=500):
        if self.tree is not None:
            self.tree.destroy()
        if self.tree_scroll_y is not None:
            self.tree_scroll_y.destroy()
        if self.tree_scroll_x is not None:
            self.tree_scroll_x.destroy()
            
        self.placeholder.pack_forget()
        
        inner = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        
        columns = list(df.columns)
        self.tree = ttk.Treeview(inner, columns=columns, show="headings", height=18)
        
        # Modern Treeview Theme
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
        
        for col in columns:
            self.tree.heading(col, text=col, anchor="w")
            width = max(90, min(240, len(str(col)) * 11 + 25))
            self.tree.column(col, width=width, minwidth=80, anchor="w")
            
        self.tree_scroll_y = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree_scroll_x = ttk.Scrollbar(inner, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)
        
        display_df = df.head(max_rows)
        for _, row in display_df.iterrows():
            values = [str(v) if pd.notna(v) else "" for v in row]
            self.tree.insert("", "end", values=values)
            
    def save_to_mysql(self):
        if self.current_df is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return
            
        table_name = db.sanitize_table_name(self.current_filename)
        confirm = messagebox.askyesno(
            "Confirm Ingestion",
            f"Save dataset into MySQL table `{table_name}`?\n\n"
            f"Rows: {len(self.current_df):,}\nColumns: {len(self.current_df.columns)}\n\n"
            "Existing table with same name will be overwritten."
        )
        if not confirm:
            return
            
        self.btn_save.configure(state="disabled", text="⏳ Ingesting...")
        self.parent.update()
        
        success, message = db.load_dataframe_to_mysql(self.current_df, table_name)
        self.btn_save.configure(state="normal", text="💾  Save to MySQL")
        
        if success:
            messagebox.showinfo("Success", message)
            self.lbl_status.configure(text=f"Ingested into table `{table_name}`", text_color="#34D399")
        else:
            messagebox.showerror("Database Error", message)
