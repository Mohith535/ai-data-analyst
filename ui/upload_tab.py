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
from ui.async_helper import run_async
from ui.theme import populate_modern_treeview


class TableConflictModal(ctk.CTkToplevel):
    """
    Non-destructive modal dialog to resolve table collision in MySQL.
    Gives the user explicit control: Overwrite vs Rename vs Cancel.
    """
    def __init__(self, parent, base_name, next_name, row_count, col_count):
        super().__init__(parent)
        self.title("Table Conflict Detected")
        self.geometry("450x260")
        self.resizable(False, False)
        self.configure(fg_color="#18191E")
        self.result = "cancel"

        self.transient(parent)
        self.grab_set()

        lbl_head = ctk.CTkLabel(
            self,
            text=f"⚠️  Table `{base_name}` Already Exists",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#F59E0B"
        )
        lbl_head.pack(padx=20, pady=(18, 6), anchor="w")

        lbl_msg = ctk.CTkLabel(
            self,
            text=(
                f"A table named `{base_name}` already exists in your MySQL database.\n\n"
                f"Incoming Dataset: {row_count:,} rows, {col_count} columns.\n"
                f"Choose how you want to handle this upload:"
            ),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#CBD5E1",
            justify="left"
        )
        lbl_msg.pack(padx=20, pady=(0, 14), anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))

        def choose(val):
            self.result = val
            self.destroy()

        btn_replace = ctk.CTkButton(
            btn_frame,
            text=f"🔄 Overwrite Existing Table (`{base_name}`)",
            command=lambda: choose("replace"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34
        )
        btn_replace.pack(fill="x", pady=4)

        btn_rename = ctk.CTkButton(
            btn_frame,
            text=f"📋 Save as New Table (`{next_name}`)",
            command=lambda: choose("rename"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=34
        )
        btn_rename.pack(fill="x", pady=4)

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=lambda: choose("cancel"),
            fg_color="#2D3139",
            hover_color="#374151",
            text_color="#94A3B8",
            font=ctk.CTkFont(size=11),
            height=28
        )
        btn_cancel.pack(fill="x", pady=(4, 0))


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
        
        # --- Metadata & Quality Audit: 4 Linear-style KPI Cards ---
        # Why (Viva Defense):
        #   Instead of a single plain text string, modern enterprise data platforms
        #   (Linear, Datadog, Snowflake) use prominent executive KPI summary cards
        #   that highlight dataset dimensions, completeness ratio, and hygiene at a glance.
        self.kpi_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=16, pady=4)
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        def _make_kpi_card(col_idx, title, default_val, accent_color, subtext):
            card = ctk.CTkFrame(
                self.kpi_container,
                fg_color="#121316",
                border_color="#1E2024",
                border_width=1,
                corner_radius=10
            )
            card.grid(row=0, column=col_idx, padx=4, pady=2, sticky="nsew")

            lbl_title = ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#94A3B8"
            )
            lbl_title.pack(anchor="w", padx=12, pady=(8, 2))

            lbl_val = ctk.CTkLabel(
                card,
                text=default_val,
                font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                text_color=accent_color
            )
            lbl_val.pack(anchor="w", padx=12, pady=0)

            lbl_sub = ctk.CTkLabel(
                card,
                text=subtext,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#64748B"
            )
            lbl_sub.pack(anchor="w", padx=12, pady=(0, 8))

            return lbl_val, lbl_sub

        self.kpi_rows_val, self.kpi_rows_sub = _make_kpi_card(0, "TOTAL ROWS", "—", "#3B82F6", "Dataset records")
        self.kpi_cols_val, self.kpi_cols_sub = _make_kpi_card(1, "COLUMNS", "—", "#8B5CF6", "Features / fields")
        self.kpi_comp_val, self.kpi_comp_sub = _make_kpi_card(2, "COMPLETENESS", "—", "#10B981", "Data hygiene score")
        self.kpi_dups_val, self.kpi_dups_sub = _make_kpi_card(3, "DUPLICATES", "—", "#F59E0B", "Redundant entries")
        
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
            
        filename = os.path.basename(filepath)
        self.btn_select.configure(state="disabled")
        self.lbl_status.configure(
            text=f"⏳ Loading and auditing {filename}...",
            text_color="#60A5FA"
        )
        self.kpi_rows_val.configure(text="...")
        self.kpi_cols_val.configure(text="...")
        self.kpi_comp_val.configure(text="...")
        self.kpi_dups_val.configure(text="...")
        
        def worker():
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
                raise ValueError("This CSV file contains 0 rows.")
            if len(df.columns) < 1:
                raise ValueError("Dataset has 0 columns.")
                
            audit = data_quality.profile_dataset(df)
            return df, filename, audit

        def on_success(result):
            df, filename, audit = result
            self.current_df = df
            self.current_filename = filename
            self.btn_select.configure(state="normal")
            self.lbl_status.configure(
                text=f"Loaded: {self.current_filename}",
                text_color="#34D399"
            )
            
            # Populate KPI Metrics Cards
            total_rows = len(df)
            total_cols = len(df.columns)
            completeness = audit.get('completeness', 100.0) if audit else round((1 - df.isnull().sum().sum() / max(1, (len(df) * len(df.columns)))) * 100, 1)
            duplicates = audit.get('duplicates', 0) if audit else int(df.duplicated().sum())
            total_missing = audit.get('total_missing', 0) if audit else int(df.isnull().sum().sum())
            total_outliers = sum(c.get("outliers", 0) for c in audit.get("columns", [])) if audit else 0

            self.kpi_rows_val.configure(text=f"{total_rows:,}")
            self.kpi_rows_sub.configure(text="Total active records")

            self.kpi_cols_val.configure(text=f"{total_cols}")
            num_cols = len(df.select_dtypes(include='number').columns)
            self.kpi_cols_sub.configure(text=f"{num_cols} numeric features")

            self.kpi_comp_val.configure(text=f"{completeness}%")
            self.kpi_comp_sub.configure(
                text=f"{total_missing:,} missing cells",
                text_color="#10B981" if total_missing == 0 else "#F59E0B"
            )

            self.kpi_dups_val.configure(text=f"{duplicates:,}")
            self.kpi_dups_sub.configure(
                text=f"{total_outliers} IQR outliers",
                text_color="#10B981" if duplicates == 0 else "#EF4444"
            )
            
            self.btn_save.configure(state="normal")
            self._display_dataframe(df)

        def on_error(exc):
            self.btn_select.configure(state="normal")
            self.lbl_status.configure(text="Failed to load dataset", text_color="#EF4444")
            self.kpi_rows_val.configure(text="—")
            self.kpi_cols_val.configure(text="—")
            self.kpi_comp_val.configure(text="—")
            self.kpi_dups_val.configure(text="—")
            messagebox.showerror("File Error", f"Failed to load file:\n{exc}")

        run_async(worker, on_success=on_success, on_error=on_error, widget=self.parent)
            
    def _display_dataframe(self, df, max_rows=500):
        # Hide placeholder
        self.placeholder.pack_forget()
        
        # If treeview and scrollbars don't exist yet, construct them permanently
        if self.tree is None:
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
            
        populate_modern_treeview(self.tree, df, max_rows=max_rows)

    def save_to_mysql(self):
        if self.current_df is None:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        base_table = db.sanitize_table_name(self.current_filename)
        existing_tables = db.list_tables()
        target_table = base_table

        if base_table in existing_tables:
            # Find next free version name
            v = 2
            while f"{base_table}_v{v}" in existing_tables:
                v += 1
            next_name = f"{base_table}_v{v}"

            modal = TableConflictModal(
                self.parent,
                base_name=base_table,
                next_name=next_name,
                row_count=len(self.current_df),
                col_count=len(self.current_df.columns)
            )
            self.parent.wait_window(modal)

            if modal.result == "replace":
                target_table = base_table
            elif modal.result == "rename":
                target_table = next_name
            else:
                return  # User cancelled
        else:
            confirm = messagebox.askyesno(
                "Confirm Ingestion",
                f"Save dataset into new MySQL table `{base_table}`?\n\n"
                f"Rows: {len(self.current_df):,}\nColumns: {len(self.current_df.columns)}"
            )
            if not confirm:
                return

        self.btn_save.configure(state="disabled", text="⏳ Ingesting...")
        self.lbl_status.configure(text=f"⏳ Ingesting {len(self.current_df):,} rows into `{target_table}`...", text_color="#60A5FA")

        def worker():
            return db.load_dataframe_to_mysql(self.current_df, target_table)

        def on_success(result):
            success, message = result
            self.btn_save.configure(state="normal", text="💾  Save to MySQL")
            if success:
                messagebox.showinfo("Success", message)
                self.lbl_status.configure(text=f"Ingested into table `{target_table}`", text_color="#34D399")
            else:
                messagebox.showerror("Database Error", message)
                self.lbl_status.configure(text="Ingestion failed", text_color="#EF4444")

        def on_error(exc):
            self.btn_save.configure(state="normal", text="💾  Save to MySQL")
            self.lbl_status.configure(text="Database connection error", text_color="#EF4444")
            messagebox.showerror("Database Error", f"Failed to ingest data:\n{exc}")

        run_async(worker, on_success=on_success, on_error=on_error, widget=self.parent)
