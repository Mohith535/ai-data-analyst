"""
settings_tab.py — Application Settings & Preference Controls
=============================================================
Hosts toggles and configuration options requested by the user:
  - 🎓 AI Teacher Mode (ON / OFF): Toggles plain-English takeaways vs raw SQL only
  - 📊 Auto-Chart Engine (ON / OFF): Toggles dynamic visual analytics rendering
  - 🗑️ Clear Query History: Resets recent query stream
  - 🔍 Active Model Inspector: Displays live Groq LLM endpoint
"""

import customtkinter as ctk
from tkinter import messagebox
import settings_manager
import history_manager
import ai_chat
from ui.async_helper import run_async


class SettingsTab:
    """Manages system preferences, AI Teacher toggles, and cache clearing."""
    
    def __init__(self, parent, on_settings_changed=None):
        self.parent = parent
        self.on_settings_changed = on_settings_changed
        
        # Main Settings Card
        self.card = ctk.CTkFrame(parent, fg_color="#121316", corner_radius=14)
        self.card.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(self.card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 14))
        
        ctk.CTkLabel(
            header,
            text="⚙️ SYSTEM SETTINGS & PREFERENCES",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")
        
        # Section 1: AI Behavior Toggles
        sec1 = ctk.CTkFrame(self.card, fg_color="#18191E", corner_radius=10)
        sec1.pack(fill="x", padx=20, pady=10)
        
        sec1_header = ctk.CTkFrame(sec1, fg_color="transparent")
        sec1_header.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            sec1_header,
            text="AI ASSISTANT & TEACHER CONTROLS",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#818CF8"
        ).pack(side="left")
        
        # Toggle 1: AI Teacher Mode
        row1 = ctk.CTkFrame(sec1, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=8)
        
        self.sw_teacher_var = ctk.BooleanVar(value=settings_manager.get_setting("ai_teacher_mode", True))
        self.sw_teacher = ctk.CTkSwitch(
            row1,
            text="Enable AI Teacher Mode (Conversational Insights & Takeaways)",
            variable=self.sw_teacher_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            progress_color="#5E6AD2",
            command=self._save_toggles
        )
        self.sw_teacher.pack(side="left")
        
        # Toggle 2: Automated Visual Charting
        row2 = ctk.CTkFrame(sec1, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        
        self.sw_chart_var = ctk.BooleanVar(value=settings_manager.get_setting("auto_chart_enabled", True))
        self.sw_chart = ctk.CTkSwitch(
            row2,
            text="Enable Automated Visual Chart Generation",
            variable=self.sw_chart_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            progress_color="#10B981",
            command=self._save_toggles
        )
        self.sw_chart.pack(side="left")

        # Toggle 3: Data Privacy / Raw Sample Transmission Mode
        row3 = ctk.CTkFrame(sec1, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(4, 14))
        
        self.sw_privacy_var = ctk.BooleanVar(value=settings_manager.get_setting("send_data_sample", False))
        self.sw_privacy = ctk.CTkSwitch(
            row3,
            text="Send Data Sample to AI for Insights (Default: OFF — Strict Local Privacy Mode)",
            variable=self.sw_privacy_var,
            onvalue=True,
            offvalue=False,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            progress_color="#F59E0B",
            command=self._save_toggles
        )
        self.sw_privacy.pack(side="left")
        
        # Section 2: Engine & History Maintenance
        sec2 = ctk.CTkFrame(self.card, fg_color="#18191E", corner_radius=10)
        sec2.pack(fill="x", padx=20, pady=10)
        
        sec2_header = ctk.CTkFrame(sec2, fg_color="transparent")
        sec2_header.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            sec2_header,
            text="DATASTORE & INFERENCE ENGINE",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#818CF8"
        ).pack(side="left")
        
        # Clear History Button
        row_hist = ctk.CTkFrame(sec2, fg_color="transparent")
        row_hist.pack(fill="x", padx=16, pady=10)
        
        ctk.CTkLabel(
            row_hist,
            text="Recent Query Cache:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#CBD5E1"
        ).pack(side="left", padx=(0, 10))
        
        self.btn_clear_hist = ctk.CTkButton(
            row_hist,
            text="🗑️ Clear Query History",
            command=self._clear_history,
            width=180,
            height=34,
            fg_color="#1E2024",
            hover_color="#EF4444",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        self.btn_clear_hist.pack(side="left")
        
        # Active Model Info & Test Connection Row
        row_model = ctk.CTkFrame(sec2, fg_color="transparent")
        row_model.pack(fill="x", padx=16, pady=(4, 14))
        
        ctk.CTkLabel(
            row_model,
            text="Active LLM Pipeline:  OpenAI GPT-OSS 120B / Qwen 27B via Groq Cloud LPU",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#64748B"
        ).pack(side="left", padx=(0, 15))

        self.btn_test_api = ctk.CTkButton(
            row_model,
            text="⚡ Test API Connection",
            command=self._test_groq_connection,
            width=160,
            height=30,
            fg_color="#1E2024",
            hover_color="#5E6AD2",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        self.btn_test_api.pack(side="left")

    def _test_groq_connection(self):
        self.btn_test_api.configure(state="disabled", text="⏳ Testing...")
        
        def worker():
            client = ai_chat.get_groq_client()
            return ai_chat.get_available_model(client, force_refresh=True)

        def on_success(model):
            self.btn_test_api.configure(state="normal", text="⚡ Test API Connection")
            if self.on_settings_changed:
                self.on_settings_changed()
            messagebox.showinfo(
                "Groq API Connected",
                f"Successfully connected to Groq LPU Cloud!\n\n"
                f"Active Model: {model}\n"
                f"Status: Operational (Ready for Text-to-SQL & Insights)"
            )

        def on_error(exc):
            self.btn_test_api.configure(state="normal", text="⚡ Test API Connection")
            if self.on_settings_changed:
                self.on_settings_changed()
            messagebox.showerror(
                "Groq Connection Error",
                f"Could not connect to Groq API:\n\n{exc}\n\n"
                "Please verify your GROQ_API_KEY in .env or run setup.bat."
            )

        run_async(worker, on_success=on_success, on_error=on_error, widget=self.parent)
        
    def _save_toggles(self):
        settings_manager.set_setting("ai_teacher_mode", self.sw_teacher_var.get())
        settings_manager.set_setting("auto_chart_enabled", self.sw_chart_var.get())
        settings_manager.set_setting("send_data_sample", self.sw_privacy_var.get())
        if self.on_settings_changed:
            self.on_settings_changed()
            
    def _clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all saved recent query sessions?"):
            history_manager.clear_history()
            messagebox.showinfo("History Cleared", "Query history has been reset.")
            if self.on_settings_changed:
                self.on_settings_changed()
