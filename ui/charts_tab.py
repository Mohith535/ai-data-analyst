"""
charts_tab.py — Charts Tab UI (macOS Glass Polish)
===================================================
Integrated controls card, sleek selectors, embedded modern charts.
"""

import customtkinter as ctk
from tkinter import messagebox
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import db
import charts
from ui.async_helper import run_async


class ChartsTab:
    """Manages the Visual Analytics tab."""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_canvas = None
        self.current_fig = None
        
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
        self.btn_refresh.pack(side="left", padx=(0, 15))
        
        # Row 2: Selectors
        row2 = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(4, 10))
        
        ctk.CTkLabel(row2, text="X-Axis:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.x_var = ctk.StringVar(value="—")
        self.x_dropdown = ctk.CTkOptionMenu(row2, variable=self.x_var, values=["—"], width=150, fg_color="#262A34")
        self.x_dropdown.pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(row2, text="Y-Axis:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.y_var = ctk.StringVar(value="—")
        self.y_dropdown = ctk.CTkOptionMenu(row2, variable=self.y_var, values=["—"], width=150, fg_color="#262A34")
        self.y_dropdown.pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(row2, text="Type:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.chart_type_var = ctk.StringVar(value="Bar")
        self.chart_type_dropdown = ctk.CTkOptionMenu(
            row2, variable=self.chart_type_var, values=["Bar", "Line", "Pie", "Histogram"],
            width=120, fg_color="#262A34"
        )
        self.chart_type_dropdown.pack(side="left", padx=(0, 15))
        
        self.btn_generate = ctk.CTkButton(
            row2, text="📊 Render Chart", command=self._generate_chart,
            width=140, height=34, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3B82F6", hover_color="#2563EB"
        )
        self.btn_generate.pack(side="left")
        
        # --- Chart Canvas Card ---
        self.chart_frame = ctk.CTkFrame(parent, fg_color="#18191E", corner_radius=12)
        self.chart_frame.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        
        self.placeholder = ctk.CTkLabel(
            self.chart_frame,
            text="📈 Visual Studio Canvas\n\nChoose dataset dimensions above and render interactive charts.",
            font=ctk.CTkFont(size=15), text_color="#64748B"
        )
        self.placeholder.pack(expand=True)
        self._refresh_tables()
        
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
        columns = db.get_table_columns(table_name)
        if columns:
            self.x_dropdown.configure(values=columns)
            self.y_dropdown.configure(values=columns)
            self.x_var.set(columns[0])
            self.y_var.set(columns[1] if len(columns) > 1 else columns[0])
            
    def _generate_chart(self):
        table = self.table_var.get()
        x_col = self.x_var.get()
        y_col = self.y_var.get()
        chart_type = self.chart_type_var.get()
        
        if table in ("Select a table", "No tables found") or x_col == "—" or y_col == "—":
            messagebox.showwarning("Notice", "Select table and axis columns.")
            return
            
        sql = f"SELECT `{y_col}` FROM `{table}` LIMIT 5000" if chart_type == "Histogram" else f"SELECT `{x_col}`, `{y_col}` FROM `{table}` LIMIT 5000"
        
        self.btn_generate.configure(state="disabled", text="⏳ Rendering...")
        
        def worker():
            df, error = db.run_query(sql)
            if error:
                raise ValueError(error)
            if df is None or df.empty:
                raise ValueError("Query returned 0 rows.")
                
            if chart_type == "Bar":
                return charts.create_bar_chart(df, x_col, y_col)
            elif chart_type == "Line":
                return charts.create_line_chart(df, x_col, y_col)
            elif chart_type == "Pie":
                return charts.create_pie_chart(df, x_col, y_col)
            elif chart_type == "Histogram":
                return charts.create_histogram(df, y_col)
            else:
                raise ValueError(f"Unknown chart type: {chart_type}")

        def on_success(fig):
            self.btn_generate.configure(state="normal", text="📊 Render Chart")
            self._embed_chart(fig)

        def on_error(exc):
            self.btn_generate.configure(state="normal", text="📊 Render Chart")
            messagebox.showerror("Render Error", f"Failed to generate chart:\n{exc}")

        run_async(worker, on_success=on_success, on_error=on_error, widget=self.parent)
            
    def _embed_chart(self, fig):
        # Prevent memory leaks: explicitly close previously active figure
        if self.current_fig is not None:
            plt.close(self.current_fig)
        self.current_fig = fig
        
        if self.current_canvas is not None:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None
        self.placeholder.pack_forget()
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
