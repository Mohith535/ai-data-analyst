"""
app.py — Linear / Raycast Style Workspace with Collapsible Sidebar Navigation & History
========================================================================================
Architecture:
  - Left Collapsible Sidebar with Hamburger (☰) Toggle
  - Integrated Recent Query History Stream in Sidebar
  - One-click history replay (restores query, SQL, and insight into Chat Tab)
  - Seamless tab switching between Chat, Ingestion, Visual Studio, and ML
"""

import customtkinter as ctk
import db
import ai_chat
import history_manager
from ui.upload_tab import UploadTab
from ui.charts_tab import ChartsTab
from ui.ml_tab import MLTab
from ui.chat_tab import ChatTab


class App(ctk.CTk):
    """
    Main application shell featuring a collapsible sidebar, recent history recall, and tab routing.
    """
    
    def __init__(self):
        super().__init__()
        
        # --- Window Setup ---
        self.title("AI Data Analyst — Intelligent Analytics Studio")
        self.geometry("1320x840")
        self.minsize(1020, 680)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0E0E10")  # Pure obsidian
        
        # State
        self.sidebar_expanded = True
        self.active_tab_name = "chat"
        self.nav_buttons = {}
        
        # --- Root Layout (Sidebar + Main Content Canvas) ---
        self.root_container = ctk.CTkFrame(self, fg_color="transparent")
        self.root_container.pack(fill="both", expand=True)
        
        # 1. Left Collapsible Sidebar
        self.sidebar_frame = ctk.CTkFrame(
            self.root_container,
            fg_color="#121316",
            corner_radius=0,
            border_width=1,
            border_color="#1E2024",
            width=240
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar_frame.pack_propagate(False)
        
        self._build_sidebar()
        
        # 2. Main Content Canvas
        self.main_canvas = ctk.CTkFrame(self.root_container, fg_color="#0E0E10", corner_radius=0)
        self.main_canvas.pack(side="right", fill="both", expand=True, padx=0, pady=0)
        
        self._build_top_header()
        self._build_tab_views()
        
        # Connect ChatTab to refresh history when a query finishes
        self.chat_tab.on_query_success = self.refresh_sidebar_history
        
        # Set default view to AI Analyst Chat
        self.switch_tab("chat")
        self.refresh_sidebar_history()
        
    def _build_sidebar(self):
        """Constructs the sidebar navigation menu."""
        # Top Logo + Hamburger Toggle
        top_bar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=54)
        top_bar.pack(fill="x", padx=10, pady=(12, 10))
        top_bar.pack_propagate(False)
        
        # Hamburger Toggle Button (☰)
        self.btn_toggle = ctk.CTkButton(
            top_bar,
            text="☰",
            font=ctk.CTkFont(size=18, weight="bold"),
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#1F2228",
            text_color="#CBD5E1",
            corner_radius=8,
            command=self.toggle_sidebar
        )
        self.btn_toggle.pack(side="left")
        
        # Brand Title Label
        self.lbl_brand = ctk.CTkLabel(
            top_bar,
            text="AI ANALYST",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_brand.pack(side="left", padx=10)
        
        # Nav Items Container
        self.nav_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=10, pady=6)
        
        nav_items = [
            ("chat", "💬", "AI Analyst Chat"),
            ("upload", "📂", "Upload Dataset"),
            ("charts", "📊", "Visual Studio"),
            ("ml", "🤖", "ML Workbench")
        ]
        
        for key, icon, title in nav_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=f"  {icon}  {title}",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#1A1D24",
                text_color="#94A3B8",
                command=lambda k=key: self.switch_tab(k)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = (btn, icon, title)
            
        # Recent History Section Header
        self.history_header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.history_header_frame.pack(fill="x", padx=12, pady=(16, 4))
        
        self.lbl_history_title = ctk.CTkLabel(
            self.history_header_frame,
            text="RECENT QUERIES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#64748B"
        )
        self.lbl_history_title.pack(side="left")
        
        # History Scrollable Box
        self.history_scroll = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color="transparent",
            corner_radius=0
        )
        self.history_scroll.pack(fill="both", expand=True, padx=6, pady=4)
        
        # Bottom Workspace Pill
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.bottom_sidebar.pack(side="bottom", fill="x", padx=10, pady=14)
        
        self.lbl_engine_badge = ctk.CTkLabel(
            self.bottom_sidebar,
            text="⚡ Groq 120B Connected",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#161B22",
            text_color="#60A5FA",
            corner_radius=8,
            height=30
        )
        self.lbl_engine_badge.pack(fill="x")
        
    def _build_top_header(self):
        """Builds the floating utility top bar."""
        self.top_header = ctk.CTkFrame(self.main_canvas, fg_color="#121316", height=48, corner_radius=0)
        self.top_header.pack(fill="x", padx=0, pady=0)
        self.top_header.pack_propagate(False)
        
        self.lbl_header_title = ctk.CTkLabel(
            self.top_header,
            text="Workspace / AI Analyst Chat",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#E2E8F0"
        )
        self.lbl_header_title.pack(side="left", padx=20)
        
        header_pills = ctk.CTkFrame(self.top_header, fg_color="transparent")
        header_pills.pack(side="right", padx=16)
        
        ctk.CTkLabel(
            header_pills,
            text="● MySQL: Active",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#10B981",
            fg_color="#13241C",
            corner_radius=10,
            padx=10, pady=3
        ).pack(side="left", padx=5)
        
    def _build_tab_views(self):
        """Constructs and mounts all 4 feature tabs."""
        self.content_holder = ctk.CTkFrame(self.main_canvas, fg_color="transparent")
        self.content_holder.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.tab_frames = {}
        for tab_key in ["chat", "upload", "charts", "ml"]:
            frame = ctk.CTkFrame(self.content_holder, fg_color="transparent")
            self.tab_frames[tab_key] = frame
            
        self.chat_tab = ChatTab(self.tab_frames["chat"])
        self.upload_tab = UploadTab(self.tab_frames["upload"])
        self.charts_tab = ChartsTab(self.tab_frames["charts"])
        self.ml_tab = MLTab(self.tab_frames["ml"])
        
    def switch_tab(self, tab_key):
        """Switches active view and updates sidebar highlights."""
        self.active_tab_name = tab_key
        
        for frame in self.tab_frames.values():
            frame.pack_forget()
            
        self.tab_frames[tab_key].pack(fill="both", expand=True)
        
        for key, (btn, icon, title) in self.nav_buttons.items():
            if key == tab_key:
                btn.configure(
                    fg_color="#5E6AD2",
                    text_color="#FFFFFF",
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94A3B8",
                    font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal")
                )
                
        titles = {
            "chat": "Workspace / AI Analyst Chat",
            "upload": "Workspace / Dataset Ingestion",
            "charts": "Workspace / Visual Studio Analytics",
            "ml": "Workspace / Machine Learning Workbench"
        }
        self.lbl_header_title.configure(text=titles.get(tab_key, "Workspace"))
        
    def toggle_sidebar(self):
        """Collapses or expands the sidebar."""
        if self.sidebar_expanded:
            self.sidebar_frame.configure(width=58)
            self.lbl_brand.pack_forget()
            self.lbl_history_title.pack_forget()
            self.history_scroll.pack_forget()
            self.lbl_engine_badge.configure(text="⚡")
            for key, (btn, icon, title) in self.nav_buttons.items():
                btn.configure(text=icon, anchor="center")
            self.sidebar_expanded = False
        else:
            self.sidebar_frame.configure(width=240)
            self.lbl_brand.pack(side="left", padx=10)
            self.lbl_history_title.pack(side="left")
            self.history_scroll.pack(fill="both", expand=True, padx=6, pady=4)
            self.lbl_engine_badge.configure(text="⚡ Groq 120B Connected")
            for key, (btn, icon, title) in self.nav_buttons.items():
                btn.configure(text=f"  {icon}  {title}", anchor="w")
            self.sidebar_expanded = True
            self.refresh_sidebar_history()
            
    def refresh_sidebar_history(self):
        """Re-populates the recent history list in the sidebar."""
        for child in self.history_scroll.winfo_children():
            child.destroy()
            
        history = history_manager.load_history()
        if not history:
            ctk.CTkLabel(
                self.history_scroll,
                text="No recent queries",
                font=ctk.CTkFont(size=11),
                text_color="#475569"
            ).pack(pady=8)
            return
            
        for item in history[:15]:
            q_text = item.get("question", "")
            btn_text = (q_text[:22] + "...") if len(q_text) > 22 else q_text
            btn = ctk.CTkButton(
                self.history_scroll,
                text=f"• {btn_text}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                anchor="w",
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color="#1A1D24",
                text_color="#94A3B8",
                command=lambda entry=item: self._replay_history(entry)
            )
            btn.pack(fill="x", pady=1)
            
    def _replay_history(self, entry):
        """Restores a previous query session into the Chat Tab."""
        self.switch_tab("chat")
        self.chat_tab.entry_question.delete(0, "end")
        self.chat_tab.entry_question.insert(0, entry.get("question", ""))
        target_table = entry.get("table", "")
        if target_table in db.list_tables():
            self.chat_tab.table_var.set(target_table)
        # Automatically trigger replay
        self.chat_tab.ask_ai()
