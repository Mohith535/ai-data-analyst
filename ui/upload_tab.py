"""
upload_tab.py — Dataset Ingestion Tab with Persistent Treeview & Data Profiling
================================================================================
Fix:
  - Re-uses a single permanent Treeview container.
  - Clears existing items and reconfigures column headings on every CSV load
    instead of destroying/re-packing frames, guaranteeing that sequential file
    loading always displays immediately.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import pandas as pd
import os
import db
import data_quality


class UploadTab:
    """Manages the Upload & Data Quality tab of the application."""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_df = None
        self.current_filename = None
        
        # --- Top Action Card ---
        self.top_frame = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        self.top_frame.pack(fill="x", padx=16, pady=(10, 6))
        
        btn_row = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=10)
        
        # Select CSV Button
        self.btn_select = ctk.CTkButton(
            btn_row,
            text="📂  Choose CSV File",
            command=self.select_file,
            width=175,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#5E6AD2",
            hover_color="#4F58B8",
            corner_radius=8
        )
        self.btn_select.pack(side="left", padx=(0, 10))
        
        # Save to MySQL Button
        self.btn_save = ctk.CTkButton(
            btn_row,
            text="💾  Save to MySQL",
            command=self.save_to_mysql,
            width=175,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            state="disabled",
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=8
        )
        self.btn_save.pack(side="left", padx=(0, 15))
        
        # Status Label
        self.lbl_status = ctk.CTkLabel(
            btn_row,
            text="Select any dataset to begin inspection & database ingestion",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8"
        )
        self.lbl_status.pack(side="left", padx=5)
        
        # --- Metadata & Quality Audit Banner ---
        self.audit_frame = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        self.audit_frame.pack(fill="x", padx=16, pady=4)
        
        audit_inner = ctk.CTkFrame(self.audit_frame, fg_color="transparent")
        audit_inner.pack(fill="x", padx=14, pady=8)
        
        ctk.CTkLabel(
            audit_inner,
            text="🛡️ Dataset Hygiene & Quality Audit:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#818CF8"
        ).pack(side="left", padx=(0, 10))
        
        self.lbl_audit_stats = ctk.CTkLabel(
            audit_inner,
            text="Completeness: --  |  Missing Values: --  |  Duplicates: --  |  Outliers: --",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#E2E8F0"
        )
        self.lbl_audit_stats.pack(side="left")
        
        # --- Table Preview Frame ---
        self.table_frame = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=12)
        self.table_frame.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        
        # Permanent inner frame
        self.inner_table_box = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        self.inner_table_box.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.tree = None
        self.tree_scroll_y = None
        self.tree_scroll_x = None
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.inner_table_box,
            text="📊 Dataset Preview Canvas\n\nClick 'Choose CSV File' to inspect rows, schema & data quality.",
            font=ctk.CTkFont(family="Segoe UI", size=15),
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
            # Handle potential encoding issues & varied delimiters (UTF-8, Latin-1 fallback)
            try:
                df = pd.read_csv(filepath)
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='latin-1')
            except Exception:
                try:
                    df = pd.read_csv(filepath, sep=None, engine='python')
                except Exception:
                    df = pd.read_csv(filepath, encoding='latin-1', sep=None, engine='python')
                
            if df.empty:
                messagebox.showwarning("Empty File", "This CSV file contains 0 rows.")
                return
            if len(df.columns) < 1:
                messagebox.showwarning("Notice", "Dataset has 0 columns.")
                return
                
            self.current_df = df
            self.current_filename = os.path.basename(filepath)
            
            self.lbl_status.configure(
                text=f"Loaded: {self.current_filename}",
                text_color="#34D399"
            )
            
            # Run Automated Data Quality Audit
            audit = data_quality.profile_dataset(df)
            if audit:
                total_outliers = sum(c["outliers"] for c in audit["columns"])
                audit_str = (
                    f"Completeness: {audit['completeness']}%  |  "
                    f"Missing: {audit['total_missing']} cells  |  "
                    f"Duplicates: {audit['duplicates']} rows  |  "
                    f"IQR Outliers: {total_outliers}"
                )
                self.lbl_audit_stats.configure(text=audit_str)
                
            self.btn_save.configure(state="normal")
            self._display_dataframe(df)
            
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to load file:\n{e}")
            
    def _display_dataframe(self, df, max_rows=500):
        # Hide placeholder
        self.placeholder.pack_forget()
        
        # If treeview and scrollbars don't exist yet, construct them permanently
        if self.tree is None:
            style = ttk.Style()
            style.theme_use("default")
            style.configure(
                "Treeview",
                background="#16181D",
                foreground="#E2E8F0",
                fieldbackground="#16181D",
                rowheight=26,
                font=('Segoe UI', 9)
            )
            style.configure(
                "Treeview.Heading",
                background="#22252C",
                foreground="#F8FAFC",
                font=('Segoe UI', 10, 'bold')
            )
            style.map("Treeview", background=[("selected", "#5E6AD2")])
            
            self.tree_scroll_y = ttk.Scrollbar(self.inner_table_box, orient="vertical")
            self.tree_scroll_x = ttk.Scrollbar(self.inner_table_box, orient="horizontal")
            
            self.tree = ttk.Treeview(
                self.inner_table_box,
                show="headings",
                height=18,
                yscrollcommand=self.tree_scroll_y.set,
                xscrollcommand=self.tree_scroll_x.set
            )
            
            self.tree_scroll_y.configure(command=self.tree.yview)
            self.tree_scroll_x.configure(command=self.tree.xview)
            
            self.tree_scroll_y.pack(side="right", fill="y")
            self.tree_scroll_x.pack(side="bottom", fill="x")
            self.tree.pack(fill="both", expand=True)
            
        # Clear any existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Re-map columns dynamically
        columns = list(df.columns)
        self.tree["columns"] = columns
        
        for col in columns:
            self.tree.heading(col, text=str(col), anchor="w")
            width = max(90, min(240, len(str(col)) * 11 + 25))
            self.tree.column(col, width=width, minwidth=80, anchor="w")
            
        # Populate rows
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
            "Existing table with same name will be replaced."
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
