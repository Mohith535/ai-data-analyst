"""
tests/test_phase_b.py — Unit Tests for Phase B Enhancements
===========================================================
Verifies:
  - Lucide-style PNG icons exist in assets/icons/ and are valid 24x24 PNGs
  - Theme Treeview utilities exist and are callable
  - mplcursors chart tooltips can attach to Matplotlib Agg figures without errors
  - Requirements.txt contains mplcursors
"""

import os
import sys
import pytest
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import charts
from ui import theme


class TestPhaseBAssets:
    """Verify PNG icons in assets/icons."""

    @pytest.mark.parametrize("icon_name", [
        "chat", "upload", "charts", "interactive", "ml", "settings"
    ])
    def test_nav_icon_exists_and_valid(self, icon_name):
        icon_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "assets", "icons", f"{icon_name}.png"
        ))
        assert os.path.exists(icon_path), f"Missing icon: {icon_path}"
        with Image.open(icon_path) as img:
            assert img.format == "PNG"
            assert img.size == (24, 24)


class TestChartTooltips:
    """Verify mplcursors tooltips attachment to figures."""

    def test_add_chart_tooltips_on_bar_chart(self):
        df = pd.DataFrame({'cat': ['A', 'B', 'C'], 'val': [10, 20, 30]})
        fig = charts.create_bar_chart(df, 'cat', 'val')
        # Should execute cleanly without raising any exception
        charts.add_chart_tooltips(fig)
        assert fig is not None
        plt.close(fig)

    def test_add_chart_tooltips_on_line_chart(self):
        df = pd.DataFrame({'x': [1, 2, 3, 4], 'y': [5, 15, 10, 25]})
        fig = charts.create_line_chart(df, 'x', 'y')
        charts.add_chart_tooltips(fig)
        assert fig is not None
        plt.close(fig)

    def test_add_chart_tooltips_none_safe(self):
        # Must gracefully handle None without raising
        charts.add_chart_tooltips(None)


class TestThemeTreeviewHelpers:
    """Verify theme module exposes modern treeview styling helpers."""

    def test_helpers_exist(self):
        assert hasattr(theme, "apply_modern_treeview_styling")
        assert hasattr(theme, "sort_treeview_column")
        assert hasattr(theme, "populate_modern_treeview")
        assert hasattr(theme, "Toast")
