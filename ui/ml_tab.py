"""
ml_tab.py — Machine Learning Tab UI (macOS Glass Polish)
=========================================================
"""

import customtkinter as ctk
from tkinter import messagebox
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import db
import ml


class MLTab:
    """Manages the Machine Learning workbench tab."""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_canvas = None
        
        # --- Top Controls Card ---
        self.controls_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.controls_frame.pack(fill="x", padx=16, pady=(12, 6))
        
        row1 = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 6))
        
        ctk.CTkLabel(row1, text="Table:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.table_var = ctk.StringVar(value="Select a table")
        self.table_dropdown = ctk.CTkOptionMenu(
            row1, variable=self.table_var, values=["Select a table"],
            command=self._on_table_selected, width=190, fg_color="#262A34"
        )
        self.table_dropdown.pack(side="left", padx=(0, 10))
        
        self.btn_refresh = ctk.CTkButton(
            row1, text="🔄 Refresh", command=self._refresh_tables,
            width=90, height=30, fg_color="#2E3442", hover_color="#3B4254"
        )
        self.btn_refresh.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(row1, text="Algorithm:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.model_var = ctk.StringVar(value="Linear Regression")
        self.model_dropdown = ctk.CTkOptionMenu(
            row1, variable=self.model_var,
            values=["Linear Regression", "KMeans Clustering"],
            command=self._on_model_changed, width=190, fg_color="#262A34"
        )
        self.model_dropdown.pack(side="left", padx=(0, 10))
        
        # Row 2: Dimensions & Execution
        row2 = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(4, 10))
        
        self.lbl_feature = ctk.CTkLabel(row2, text="Feature (X):", font=ctk.CTkFont(size=12))
        self.lbl_feature.pack(side="left", padx=(0, 4))
        self.feature_var = ctk.StringVar(value="—")
        self.feature_dropdown = ctk.CTkOptionMenu(row2, variable=self.feature_var, values=["—"], width=150, fg_color="#262A34")
        self.feature_dropdown.pack(side="left", padx=(0, 12))
        
        self.lbl_target = ctk.CTkLabel(row2, text="Target (Y):", font=ctk.CTkFont(size=12))
        self.lbl_target.pack(side="left", padx=(0, 4))
        self.target_var = ctk.StringVar(value="—")
        self.target_dropdown = ctk.CTkOptionMenu(row2, variable=self.target_var, values=["—"], width=150, fg_color="#262A34")
        self.target_dropdown.pack(side="left", padx=(0, 12))
        
        self.lbl_clusters = ctk.CTkLabel(row2, text="K (Clusters):", font=ctk.CTkFont(size=12))
        self.lbl_clusters.pack(side="left", padx=(0, 4))
        self.clusters_var = ctk.StringVar(value="3")
        self.clusters_entry = ctk.CTkEntry(row2, textvariable=self.clusters_var, width=50, fg_color="#262A34")
        self.clusters_entry.pack(side="left", padx=(0, 15))
        
        self.btn_run = ctk.CTkButton(
            row2, text="🚀 Train & Fit", command=self._run_model,
            width=140, height=34, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#8B5CF6", hover_color="#7C3AED"
        )
        self.btn_run.pack(side="left")
        
        # --- Metrics Banner ---
        self.metrics_banner = ctk.CTkFrame(parent, fg_color="#22252D", corner_radius=8)
        self.metrics_banner.pack(fill="x", padx=16, pady=4)
        
        self.lbl_results = ctk.CTkLabel(
            self.metrics_banner,
            text="⚡ Model metrics, evaluation scores, and equations will be calculated here.",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#10B981",
            justify="left"
        )
        self.lbl_results.pack(padx=14, pady=6, anchor="w")
        
        # --- Visual Canvas Card ---
        self.chart_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.chart_frame.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        
        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="🤖 Predictive Model Canvas\n\nConfigure algorithm and features to train real-time ML pipelines.",
            font=ctk.CTkFont(size=15), text_color="#64748B"
        )
        self.placeholder.pack(expand=True)
        
        self._refresh_tables()
        self._on_model_changed("Linear Regression")
        
    def _refresh_tables(self):
        tables = db.list_tables()
        if tables:
            self.table_dropdown.configure(values=tables)
            if self.table_var.get() not in tables:
                self.table_var.set(tables[0])
                self._on_table_selected(tables[0])
        else:
            self.table_dropdown.configure(values=["No tables found"])
            self.table_var.set("No tables found")
            
    def _on_table_selected(self, table_name):
        if table_name in ("Select a table", "No tables found"):
            return
        df, _ = db.run_query(f"SELECT * FROM `{table_name}` LIMIT 100")
        if df is None:
            return
        numeric_cols = [c for c in df.select_dtypes(include=['number']).columns if c != '_id']
        if numeric_cols:
            self.feature_dropdown.configure(values=numeric_cols)
            self.target_dropdown.configure(values=numeric_cols)
            self.feature_var.set(numeric_cols[0])
            self.target_var.set(numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])
            
    def _on_model_changed(self, model_name):
        if model_name == "Linear Regression":
            self.lbl_feature.configure(text="Feature (X):")
            self.lbl_target.configure(text="Target (Y):")
            self.lbl_clusters.configure(text_color="gray")
            self.clusters_entry.configure(state="disabled")
        else:
            self.lbl_feature.configure(text="Dimension 1:")
            self.lbl_target.configure(text="Dimension 2:")
            self.lbl_clusters.configure(text_color="#F8FAFC")
            self.clusters_entry.configure(state="normal")
            
    def _run_model(self):
        table = self.table_var.get()
        f = self.feature_var.get()
        t = self.target_var.get()
        model_type = self.model_var.get()
        
        if table in ("Select a table", "No tables found") or f == "—" or t == "—":
            messagebox.showwarning("Notice", "Select table and numerical features.")
            return
            
        sql = f"SELECT `{f}`, `{t}` FROM `{table}`"
        df, err = db.run_query(sql)
        if err or df is None or df.empty:
            messagebox.showerror("Data Error", err or "No rows found.")
            return
            
        try:
            self.btn_run.configure(state="disabled", text="⏳ Fitting...")
            self.parent.update()
            
            if model_type == "Linear Regression":
                res = ml.run_linear_regression(df, f, t)
                txt = f"📐 R² Score: {res['r2']:.4f}  |  MAE: {res['mae']:.2f}  |  Equation: {res['equation']}"
                self.lbl_results.configure(text=txt)
                self._embed_chart(res['figure'])
            else:
                k = int(self.clusters_var.get())
                res = ml.run_kmeans(df, f, t, n_clusters=k)
                txt = f"📊 K: {res['n_clusters']}  |  Inertia: {res['inertia']:.2f}  |  Counts: {res['cluster_sizes']}"
                self.lbl_results.configure(text=txt)
                self._embed_chart(res['figure'])
        except Exception as e:
            messagebox.showerror("Model Error", str(e))
        finally:
            self.btn_run.configure(state="normal", text="🚀 Train & Fit")
            
    def _embed_chart(self, fig):
        if self.current_canvas is not None:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None
        self.placeholder.pack_forget()
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
