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
import tkinter.ttk as ttk
import pandas as pd

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


# -----------------------------------------------------------------------------
# Modern Linear-Style Treeview Engine (Zebra Rows, Sorting, Hover)
# -----------------------------------------------------------------------------

def apply_modern_treeview_styling(tree):
    """
    Applies high-contrast dark theme styling, custom row heights,
    zebra row tag configurations, and hover highlighting to a ttk.Treeview.
    
    Why (Viva Defense):
      Default ttk Treeviews on Windows use native win32 styling which defaults to
      bright white backgrounds and cramped 18px row heights. CustomTkinter dark mode
      requires ttk.Style override using 'default' or 'clam' theme to maintain the
      deep Linear aesthetic (#14161B canvas, #181A22 zebra rows, and #282D3D hover).
    """
    style = ttk.Style()
    try:
        style.theme_use("default")
    except Exception:
        pass

    style.configure(
        "Treeview",
        background="#14161B",
        foreground="#E2E8F0",
        fieldbackground="#14161B",
        rowheight=28,
        font=(FONT_SANS, 10),
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background="#1E2027",
        foreground="#F8FAFC",
        relief="flat",
        font=(FONT_SANS, 10, "bold"),
        padding=(8, 6)
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#2A2D37"), ("pressed", "#5E6AD2")],
        foreground=[("active", "#FFFFFF")]
    )
    style.map(
        "Treeview",
        background=[("selected", "#5E6AD2")],
        foreground=[("selected", "#FFFFFF")]
    )

    # Configure Zebra striping and hover tags
    tree.tag_configure("even", background="#14161B", foreground="#E2E8F0")
    tree.tag_configure("odd",  background="#181A22", foreground="#E2E8F0")
    tree.tag_configure("hover", background="#282D3D", foreground="#FFFFFF")

    # Wire up hover tracking
    _enable_treeview_hover(tree)


def _enable_treeview_hover(tree):
    """Dynamically applies a subtle hover highlight to the row beneath the mouse."""
    if hasattr(tree, "_hover_bound") and tree._hover_bound:
        return
    tree._hover_bound = True
    tree._last_hovered = None

    def on_motion(event):
        item = tree.identify_row(event.y)
        if item != tree._last_hovered:
            # Restore previous row tags
            if tree._last_hovered and tree.exists(tree._last_hovered):
                tags = [t for t in tree.item(tree._last_hovered, "tags") if t != "hover"]
                tree.item(tree._last_hovered, tags=tags)
            # Highlight current row
            if item and tree.exists(item):
                curr_tags = list(tree.item(item, "tags"))
                if "hover" not in curr_tags:
                    curr_tags.append("hover")
                tree.item(item, tags=curr_tags)
                tree._last_hovered = item
            else:
                tree._last_hovered = None

    def on_leave(event):
        if tree._last_hovered and tree.exists(tree._last_hovered):
            tags = [t for t in tree.item(tree._last_hovered, "tags") if t != "hover"]
            tree.item(tree._last_hovered, tags=tags)
        tree._last_hovered = None

    tree.bind("<Motion>", on_motion, add="+")
    tree.bind("<Leave>", on_leave, add="+")


def sort_treeview_column(tree, col, reverse=False):
    """
    Sorts Treeview rows by clicked column header (numeric-aware or alphabetical).
    Updates column header with ▲ / ▼ direction indicator and preserves zebra striping.
    
    Why (Viva Defense):
      Raw SQL tables and CSV exports often present data in arbitrary default order.
      Enabling client-side header-click sorting gives the user instant exploratory
      interactivity without issuing expensive database round-trips.
    """
    items = tree.get_children("")
    if not items:
        return

    data = []
    for item in items:
        val = tree.set(item, col)
        # Numerical conversion attempt
        try:
            num = float(str(val).replace(",", "").replace("$", "").replace("%", ""))
            sort_key = (0, num)
        except (ValueError, AttributeError):
            sort_key = (1, str(val).lower())
        data.append((sort_key, item))

    data.sort(reverse=reverse, key=lambda x: x[0])

    # Reorder items and restripe alternate zebra tags
    for index, (_, item) in enumerate(data):
        tree.move(item, "", index)
        tag = "even" if index % 2 == 0 else "odd"
        tree.item(item, tags=(tag,))

    # Update headings with sort indicator
    for c in tree["columns"]:
        raw_text = tree.heading(c)["text"]
        clean_text = raw_text.replace(" ▲", "").replace(" ▼", "")
        if c == col:
            arrow = " ▼" if reverse else " ▲"
            tree.heading(
                c,
                text=clean_text + arrow,
                command=lambda _c=c, _r=not reverse: sort_treeview_column(tree, _c, _r)
            )
        else:
            tree.heading(
                c,
                text=clean_text,
                command=lambda _c=c, _r=False: sort_treeview_column(tree, _c, _r)
            )


def populate_modern_treeview(tree, df, max_rows=500):
    """
    Populates Treeview with DataFrame records, configures column headers,
    applies sort triggers, and alternating zebra rows.
    """
    apply_modern_treeview_styling(tree)

    # Clear old entries
    for item in tree.get_children():
        tree.delete(item)

    columns = list(df.columns)
    tree["columns"] = columns

    for col in columns:
        col_str = str(col)
        tree.heading(
            col,
            text=col_str,
            anchor="w",
            command=lambda _c=col: sort_treeview_column(tree, _c, False)
        )
        sample_vals = df[col].head(30).astype(str).tolist()
        max_len = max([len(col_str)] + [len(v) for v in sample_vals]) if sample_vals else len(col_str)
        width = max(95, min(280, max_len * 10 + 28))
        tree.column(col, width=width, minwidth=80, anchor="w")

    display_df = df.head(max_rows) if max_rows else df
    for i, (_, row) in enumerate(display_df.iterrows()):
        vals = [str(v) if pd.notna(v) and str(v) != "nan" else "" for v in row]
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", values=vals, tags=(tag,))
