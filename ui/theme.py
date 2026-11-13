"""
ui/theme.py — Unified Linear / Raycast Design System & UI Utilities
===================================================================
Provides centralized design tokens and reusable UI helpers:
  - High-contrast dark theme colors
  - Border and elevation definitions
  - Typography metrics
  - Non-blocking Toast notification system
"""

import customtkinter as ctk

# -----------------------------------------------------------------------------
# Color Palette (Linear / Raycast Dark Aesthetic)
# -----------------------------------------------------------------------------
BG_CANVAS = "#0E0E10"
BG_SIDEBAR = "#121316"
BG_CARD = "#121316"
BG_CARD_INNER = "#18191E"
BG_INPUT = "#18191E"
BG_CODE = "#0C0D0F"

# Borders & Separators
BORDER_SUBTLE = "#1E2024"
BORDER_DEFAULT = "#22252D"
BORDER_FOCUS = "#5E6AD2"

# Brand & Accent Tokens
ACCENT_PRIMARY = "#5E6AD2"
ACCENT_PRIMARY_HOVER = "#4F58B8"
ACCENT_SUCCESS = "#10B981"
ACCENT_WARNING = "#F59E0B"
ACCENT_DANGER = "#EF4444"
ACCENT_INFO = "#818CF8"

# Text Colors
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"
TEXT_DIM = "#64748B"

# Font Families
FONT_SANS = "Segoe UI"
FONT_MONO = "Consolas"


class Toast:
    """
    Non-blocking toast notification that auto-dismisses after a timeout.
    
    Why (Viva Defense):
      Standard `tkinter.messagebox` calls are synchronous and block the main GUI loop,
      forcing the user to stop, move their mouse, and click 'OK' for minor feedback.
      Modern professional desktop applications (Linear, VS Code, Raycast) use floating
      non-blocking toasts that convey status and dissolve automatically after a duration.
    """
    
    _active_toast = None
    
    @classmethod
    def show(cls, parent, message, duration_ms=2800, style="success"):
        # Dismiss any previously visible toast immediately
        if cls._active_toast is not None:
            try:
                cls._active_toast.destroy()
            except Exception:
                pass
            cls._active_toast = None
        
        palette = {
            "success": (ACCENT_SUCCESS, "#0D2818"),
            "error":   (ACCENT_DANGER, "#2D1515"),
            "warning": (ACCENT_WARNING, "#2A2012"),
            "info":    (ACCENT_INFO, "#1A1A2E"),
        }
        fg, bg = palette.get(style, palette["info"])
        
        toast = ctk.CTkFrame(
            parent,
            fg_color=bg,
            corner_radius=10,
            border_width=1,
            border_color=fg
        )
        toast.place(relx=0.5, rely=0.02, anchor="n")
        cls._active_toast = toast
        
        ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(family=FONT_SANS, size=12, weight="bold"),
            text_color=fg,
            padx=18,
            pady=8
        ).pack()
        
        def dismiss():
            try:
                toast.destroy()
            except Exception:
                pass
            if cls._active_toast is toast:
                cls._active_toast = None
        
        parent.after(duration_ms, dismiss)
