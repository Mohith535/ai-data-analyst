"""
app.py — Linear / Raycast Style Workspace with Full Navigation & Settings
==========================================================================
Architecture:
  - Collapsible Sidebar with navigation items:
      * 💬 AI Analyst Chat
      * 📂 Upload Dataset
      * 📊 Visual Studio (Matplotlib)
      * 🌐 Interactive Studio (Plotly 3D & Zoom)
      * 🤖 ML Workbench
      * ⚙️ Settings (AI Teacher Toggle, Chart Toggle, History Management)
  - Recent Query History with 1-click replay
"""

import customtkinter as ctk
from PIL import Image
import os
import matplotlib.pyplot as plt
import db
import ai_chat
import history_manager
import settings_manager
from ui.async_helper import run_async
from ui.upload_tab import UploadTab
from ui.charts_tab import ChartsTab
from ui.ml_tab import MLTab
from ui.chat_tab import ChatTab
from ui.interactive_tab import InteractiveTab
from ui.settings_tab import SettingsTab


def _load_nav_icon(name, size=18):
    """
    Load a PNG icon from assets/icons/ as a CTkImage (HiDPI-safe).
    Falls back to None gracefully if the file is missing.
    Why: CTkImage scales correctly on Retina/HiDPI displays; raw
    PhotoImage would appear blurry on 2x screens.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", f"{name}.png")
    try:
        pil_img = Image.open(os.path.abspath(path)).resize((size, size), Image.LANCZOS)
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
    except Exception:
        return None


class App(ctk.CTk):
    """
    Main application shell featuring a collapsible sidebar, recent history recall, and tab routing.
    """
    
    def __init__(self):
        super().__init__()
        
        self.title("AI Data Analyst — Intelligent Analytics Studio")
        self.geometry("1340x840")
        self.minsize(1020, 680)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0E0E10")
        
        self.sidebar_expanded = True
        self.active_tab_name = "chat"
        self.nav_buttons = {}
        self.engine_status = ("⚡ Checking Groq...", "#60A5FA", "#161B22")
        
        # Cleanly close all Matplotlib figures on exit
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # --- Root Layout ---
        self.root_container = ctk.CTkFrame(self, fg_color="transparent")
        self.root_container.pack(fill="both", expand=True)
        
        # 1. Left Sidebar
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
        
        self.chat_tab.on_query_success = self.refresh_sidebar_history
        self.switch_tab("chat")
        self.refresh_sidebar_history()
        self.check_groq_status()
        
        # --- Global Keyboard Shortcuts ---
        # Why: Ctrl+1..6 let power users navigate without touching the mouse.
        # We bind at the root window level so shortcuts work from any focused widget.
        tab_keys = ["chat", "upload", "charts", "interactive", "ml", "settings"]
        for i, k in enumerate(tab_keys, start=1):
            self.bind(f"<Control-{i}>", lambda e, key=k: self.switch_tab(key))
        
    def _build_sidebar(self):
        top_bar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent", height=54)
        top_bar.pack(fill="x", padx=10, pady=(12, 6))
        top_bar.pack_propagate(False)
        
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
        
        self.lbl_brand = ctk.CTkLabel(
            top_bar,
            text="AI ANALYST",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_brand.pack(side="left", padx=10)
        
        self.nav_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=10, pady=4)
        
        # Nav items: (tab_key, icon_filename, emoji_fallback, label, shortcut_hint)
        nav_items = [
            ("chat",        "chat",        "💬", "AI Analyst Chat",   "⌃1"),
            ("upload",      "upload",      "📂", "Upload Dataset",    "⌃2"),
            ("charts",      "charts",      "📊", "Visual Studio",     "⌃3"),
            ("interactive", "interactive", "🌐", "Interactive Studio","⌃4"),
            ("ml",          "ml",          "🤖", "ML Workbench",      "⌃5"),
            ("settings",    "settings",    "⚙️", "Settings & Prefs",  "⌃6"),
        ]
        
        for key, icon_name, emoji, title, hint in nav_items:
            ctk_icon = _load_nav_icon(icon_name, size=16)
            # Build button text: use emoji as text prefix when image loaded (image replaces it visually)
            btn_text = f"  {title}" if ctk_icon else f"  {emoji}  {title}"
            btn = ctk.CTkButton(
                self.nav_container,
                text=btn_text,
                image=ctk_icon,
                compound="left",          # icon left of text
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#1A1D24",
                text_color="#94A3B8",
                command=lambda k=key: self.switch_tab(k)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = (btn, ctk_icon, emoji, title)
            
        self.history_header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.history_header_frame.pack(fill="x", padx=12, pady=(14, 2))
        
        self.lbl_history_title = ctk.CTkLabel(
            self.history_header_frame,
            text="RECENT QUERIES",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#64748B"
        )
        self.lbl_history_title.pack(side="left")
        
        self.history_scroll = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color="transparent",
            corner_radius=0
        )
        self.history_scroll.pack(fill="both", expand=True, padx=6, pady=2)
        
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.bottom_sidebar.pack(side="bottom", fill="x", padx=10, pady=12)
        
        self.lbl_engine_badge = ctk.CTkLabel(
            self.bottom_sidebar,
            text=self.engine_status[0],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=self.engine_status[2],
            text_color=self.engine_status[1],
            corner_radius=8,
            height=30
        )
        self.lbl_engine_badge.pack(fill="x")
        
    def _build_top_header(self):
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
        self.content_holder = ctk.CTkFrame(self.main_canvas, fg_color="transparent")
        self.content_holder.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.tab_frames = {}
        for tab_key in ["chat", "upload", "charts", "interactive", "ml", "settings"]:
            frame = ctk.CTkFrame(self.content_holder, fg_color="transparent")
            self.tab_frames[tab_key] = frame
            
        self.chat_tab = ChatTab(self.tab_frames["chat"])
        self.upload_tab = UploadTab(self.tab_frames["upload"])
        self.charts_tab = ChartsTab(self.tab_frames["charts"])
        self.interactive_tab = InteractiveTab(self.tab_frames["interactive"])
        self.ml_tab = MLTab(self.tab_frames["ml"])
        self.settings_tab = SettingsTab(self.tab_frames["settings"], on_settings_changed=self._on_settings_updated)
        
    def _on_settings_updated(self):
        self.check_groq_status()
        self.chat_tab.sync_settings_state()
        self.refresh_sidebar_history()
        
    def switch_tab(self, tab_key):
        self.active_tab_name = tab_key
        for frame in self.tab_frames.values():
            frame.pack_forget()
        self.tab_frames[tab_key].pack(fill="both", expand=True)
        
        for key, (btn, ctk_icon, emoji, title) in self.nav_buttons.items():
            if key == tab_key:
                btn.configure(
                    fg_color="#5E6AD2",
                    text_color="#FFFFFF",
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94A3B8",
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal")
                )
                
        titles = {
            "chat": "Workspace / AI Analyst Chat",
            "upload": "Workspace / Dataset Ingestion",
            "charts": "Workspace / Visual Studio Analytics",
            "interactive": "Workspace / Interactive 3D Studio",
            "ml": "Workspace / Machine Learning Workbench",
            "settings": "Workspace / System Settings & Preferences"
        }
        self.lbl_header_title.configure(text=titles.get(tab_key, "Workspace"))
        
    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar_frame.configure(width=58)
            self.lbl_brand.pack_forget()
            self.lbl_history_title.pack_forget()
            self.history_scroll.pack_forget()
            self.lbl_engine_badge.configure(
                text="⚡",
                text_color=self.engine_status[1],
                fg_color=self.engine_status[2]
            )
            for key, (btn, icon, title) in self.nav_buttons.items():
                btn.configure(text=icon, anchor="center")
            self.sidebar_expanded = False
        else:
            self.sidebar_frame.configure(width=240)
            self.lbl_brand.pack(side="left", padx=10)
            self.lbl_history_title.pack(side="left")
            self.history_scroll.pack(fill="both", expand=True, padx=6, pady=2, before=self.bottom_sidebar)
            self.lbl_engine_badge.configure(
                text=self.engine_status[0],
                text_color=self.engine_status[1],
                fg_color=self.engine_status[2]
            )
            for key, (btn, icon, title) in self.nav_buttons.items():
                btn.configure(text=f"  {icon}  {title}", anchor="w")
            self.sidebar_expanded = True
            self.refresh_sidebar_history()
            
    def check_groq_status(self):
        """Asynchronously queries Groq status and updates the sidebar badge dynamically."""
        def worker():
            key = os.getenv("GROQ_API_KEY", "").strip()
            if not key or key == "your_groq_api_key_here":
                return ("⚠️ Groq: No API Key", "#F59E0B", "#2A2012")
            try:
                client = ai_chat.get_groq_client()
                model = ai_chat.get_available_model(client)
                short_model = model.split("/")[-1].replace("-versatile", "").upper()
                return (f"⚡ Groq {short_model}", "#10B981", "#13241C")
            except Exception:
                return ("❌ Groq: Offline", "#EF4444", "#2D1515")

        def on_success(status):
            self.engine_status = status
            if self.sidebar_expanded:
                self.lbl_engine_badge.configure(
                    text=status[0],
                    text_color=status[1],
                    fg_color=status[2]
                )
            else:
                self.lbl_engine_badge.configure(
                    text="⚡",
                    text_color=status[1],
                    fg_color=status[2]
                )

        run_async(worker, on_success=on_success, widget=self)

    def _on_close(self):
        """Clean up all Matplotlib figures on window close to eliminate memory leaks."""
        try:
            plt.close("all")
        except Exception:
            pass
        self.destroy()
            
    def refresh_sidebar_history(self):
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
        self.switch_tab("chat")
        self.chat_tab.entry_question.delete(0, "end")
        self.chat_tab.entry_question.insert(0, entry.get("question", ""))
        target_table = entry.get("table", "")
        if target_table in db.list_tables():
            self.chat_tab.table_var.set(target_table)
        self.chat_tab.ask_ai()
