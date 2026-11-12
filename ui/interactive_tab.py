"""
interactive_tab.py — Interactive Data Studio Workbench
=========================================================
Lets users build interactive, zoomable, pan-able, and 3D data visualisations
using Plotly and inspect full-resolution HTML visual canvases.
"""

import customtkinter as ctk
from tkinter import messagebox
import db
import interactive_studio


class InteractiveTab:
    """Manages the Interactive Data Studio view."""
    
    def __init__(self, parent):
        self.parent = parent
        
        # Main Card
        self.card = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=14)
        self.card.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text="🌐 INTERACTIVE DATA STUDIO (PLOTLY 3D & ZOOM ENGINE)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")
        
        # Subtitle
        ctk.CTkLabel(
            self.card,
            text="Generate high-performance, zoomable, 3D and drill-down interactive graphics rendered in real-time.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=20, pady=(0, 14))
        
        # Controls Frame
        controls = ctk.CTkFrame(self.card, fg_color="#18191E", corner_radius=10)
        controls.pack(fill="x", padx=20, pady=6)
        
        # Row 1: Table & Chart Type
        r1 = ctk.CTkFrame(controls, fg_color="transparent")
        r1.pack(fill="x", padx=16, pady=10)
        
        ctk.CTkLabel(r1, text="Table:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.table_var = ctk.StringVar(value="Select a table")
        self.table_dropdown = ctk.CTkOptionMenu(
            r1, variable=self.table_var, values=["Select a table"],
            command=self._on_table_selected, width=190, fg_color="#262A34"
        )
        self.table_dropdown.pack(side="left", padx=(0, 12))
        
        self.btn_refresh = ctk.CTkButton(
            r1, text="🔄 Refresh", command=self._refresh_tables,
            width=90, height=32, fg_color="#2E3442", hover_color="#3B4254"
        )
        self.btn_refresh.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(r1, text="Studio Chart Type:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.type_var = ctk.StringVar(value="Scatter 3D")
        self.type_dropdown = ctk.CTkOptionMenu(
            r1, variable=self.type_var,
            values=["Scatter 3D", "Interactive Bar", "Interactive Line", "Box Plot", "Correlation Heatmap"],
            command=self._on_type_changed, width=200, fg_color="#262A34"
        )
        self.type_dropdown.pack(side="left", padx=(0, 12))
        
        # Row 2: Dimension Selectors
        self.r2 = ctk.CTkFrame(controls, fg_color="transparent")
        self.r2.pack(fill="x", padx=16, pady=(4, 14))
        
        ctk.CTkLabel(self.r2, text="X-Axis:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.x_var = ctk.StringVar(value="—")
        self.x_dd = ctk.CTkOptionMenu(self.r2, variable=self.x_var, values=["—"], width=140, fg_color="#262A34")
        self.x_dd.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(self.r2, text="Y-Axis:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 4))
        self.y_var = ctk.StringVar(value="—")
        self.y_dd = ctk.CTkOptionMenu(self.r2, variable=self.y_var, values=["—"], width=140, fg_color="#262A34")
        self.y_dd.pack(side="left", padx=(0, 10))
        
        self.lbl_z = ctk.CTkLabel(self.r2, text="Z-Axis (3D):", font=ctk.CTkFont(size=12))
        self.lbl_z.pack(side="left", padx=(0, 4))
        self.z_var = ctk.StringVar(value="—")
        self.z_dd = ctk.CTkOptionMenu(self.r2, variable=self.z_var, values=["—"], width=140, fg_color="#262A34")
        self.z_dd.pack(side="left", padx=(0, 14))
        
        self.btn_launch = ctk.CTkButton(
            self.r2, text="🚀 Launch Interactive Canvas", command=self._launch_studio,
            width=220, height=36, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#5E6AD2", hover_color="#4F58B8"
        )
        self.btn_launch.pack(side="left")
        
        # Info Preview Box
        preview_box = ctk.CTkFrame(self.card, fg_color="#18191E", corner_radius=10)
        preview_box.pack(fill="both", expand=True, padx=20, pady=16)
        
        self.lbl_preview = ctk.CTkLabel(
            preview_box,
            text="✨ Interactive Canvas Ready\n\n"
                 "Select dataset and axes above, then click 'Launch Interactive Canvas'.\n"
                 "The studio will generate a dynamic, GPU-accelerated 3D/Zoomable Plotly visualization in your browser.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#64748B"
        )
        self.lbl_preview.pack(expand=True)
        
        self._refresh_tables()
        self._on_type_changed("Scatter 3D")
        
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
        cols = db.get_table_columns(table_name)
        if cols:
            self.x_dd.configure(values=cols)
            self.y_dd.configure(values=cols)
            self.z_dd.configure(values=cols)
            self.x_var.set(cols[0])
            self.y_var.set(cols[1] if len(cols) > 1 else cols[0])
            self.z_var.set(cols[2] if len(cols) > 2 else cols[0])
            
    def _on_type_changed(self, chart_type):
        if chart_type == "Scatter 3D":
            self.lbl_z.pack(side="left", padx=(0, 4))
            self.z_dd.pack(side="left", padx=(0, 14))
        else:
            self.lbl_z.pack_forget()
            self.z_dd.pack_forget()
            
    def _launch_studio(self):
        table = self.table_var.get()
        if table in ("Select a table", "No tables found"):
            messagebox.showwarning("Notice", "Select a valid table first.")
            return
            
        df, err = db.run_query(f"SELECT * FROM `{table}` LIMIT 2000")
        if err or df is None or df.empty:
            messagebox.showerror("Error", err or "Dataset contains no records.")
            return
            
        chart_type = self.type_var.get()
        x = self.x_var.get()
        y = self.y_var.get()
        z = self.z_var.get() if chart_type == "Scatter 3D" else None
        
        try:
            html_path = interactive_studio.generate_interactive_chart(
                df, chart_type, x, y, z_col=z
            )
            self.lbl_preview.configure(
                text=f"✅ Interactive Canvas Launched!\n\nFile saved to: {html_path}\n"
                     f"Rotatable 3D / Pan / Zoom controls are now active in your browser.",
                text_color="#34D399"
            )
        except Exception as e:
            messagebox.showerror("Studio Error", str(e))
