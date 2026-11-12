"""
app.py — Main Application Window (macOS Glassmorphism Theme & Polished Experience)
=====================================================================================
Features:
  - macOS Dark Glass inspired styling: Deep charcoal backgrounds (#121316, #18191E)
  - Pill navigation tabs with custom accent markers
  - Interactive status bar (DB Connection indicator, Groq Model indicator)
  - macOS window-like header pill bar
  - Smooth visual hierarchy
"""

import customtkinter as ctk
import db
import ai_chat
from ui.upload_tab import UploadTab
from ui.charts_tab import ChartsTab
from ui.ml_tab import MLTab
from ui.chat_tab import ChatTab


class App(ctk.CTk):
    """
    Main application window designed with modern macOS glass aesthetics.
    """
    
    def __init__(self):
        super().__init__()
        
        # --- Window Configuration ---
        self.title("AI Data Analyst — Intelligent Desktop Analytics")
        self.geometry("1240x780")
        self.minsize(980, 650)
        
        # Appearance: Clean dark mode
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Base background: Deep macOS slate
        self.configure(fg_color="#121316")
        
        # --- Top Header Bar (macOS Pill Navigation + Brand) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="#18191E", corner_radius=14, height=56)
        self.header_frame.pack(fill="x", padx=16, pady=(14, 8))
        self.header_frame.pack_propagate(False)
        
        # macOS Traffic Light aesthetic dots
        traffic_dots = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        traffic_dots.pack(side="left", padx=(14, 12))
        
        # Red, Yellow, Green dots
        for color in ["#FF5F56", "#FFBD2E", "#27C93F"]:
            dot = ctk.CTkLabel(
                traffic_dots, text="●", font=ctk.CTkFont(size=14),
                text_color=color, width=14
            )
            dot.pack(side="left", padx=2)
            
        # App Title & Badge
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=10)
        
        ctk.CTkLabel(
            title_box,
            text="AI DATA ANALYST",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#FFFFFF"
        ).pack(side="left")
        
        badge = ctk.CTkLabel(
            title_box,
            text=" v2.0 PRO ",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            fg_color="#2A2D37",
            text_color="#58A6FF",
            corner_radius=6
        )
        badge.pack(side="left", padx=8)
        
        # Right Side Header Stats (Live indicators)
        stats_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        stats_frame.pack(side="right", padx=14)
        
        # DB Status Pill
        self.db_pill = ctk.CTkLabel(
            stats_frame,
            text="● MySQL: Connected",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#27C93F",
            fg_color="#1E2322",
            corner_radius=12,
            padx=10, pady=4
        )
        self.db_pill.pack(side="left", padx=5)
        
        # AI Model Pill
        self.ai_pill = ctk.CTkLabel(
            stats_frame,
            text="⚡ Engine: Groq 120B",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#88bbee",
            fg_color="#192433",
            corner_radius=12,
            padx=10, pady=4
        )
        self.ai_pill.pack(side="left", padx=5)
        
        # --- Tab View (Glassmorphism Frame) ---
        self.tabview = ctk.CTkTabview(
            self,
            anchor="nw",
            corner_radius=14,
            fg_color="#18191E",
            segmented_button_fg_color="#22252D",
            segmented_button_selected_color="#3B82F6",
            segmented_button_selected_hover_color="#2563EB",
            segmented_button_unselected_color="#22252D",
            segmented_button_unselected_hover_color="#2E323D"
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        
        # Tabs
        self.tab_upload = self.tabview.add("  📂 Upload & Dataset  ")
        self.tab_charts = self.tabview.add("  📊 Visual Analytics  ")
        self.tab_ml = self.tabview.add("  🤖 Machine Learning  ")
        self.tab_chat = self.tabview.add("  💬 AI Analyst Chat  ")
        
        # Initialize tab components
        self.upload_tab = UploadTab(self.tab_upload)
        self.charts_tab = ChartsTab(self.tab_charts)
        self.ml_tab = MLTab(self.tab_ml)
        self.chat_tab = ChatTab(self.tab_chat)
        
        # Set default tab
        self.tabview.set("  📂 Upload & Dataset  ")
