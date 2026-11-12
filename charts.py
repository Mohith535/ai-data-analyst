"""
charts.py — Polished Matplotlib Chart Helpers (Apple / Glass Modern Aesthetic)
================================================================================
Theme Highlights:
  - Deep dark background (#18191E) matching CustomTkinter UI
  - Refined modern color palette (iOS / macOS inspired blue, emerald, amber, rose, violet)
  - Subtle grid lines (#2B2F3A) with zero visual clutter
  - Clean typographic hierarchy
  - Auto-downsampling & smart binning to prevent overcrowding on large tables
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# macOS Dark Theme Palette
DARK_BG = '#18191E'
DARK_FG = '#E2E8F0'
GRID_COLOR = '#262934'

# Modern Apple-inspired UI chart palette
ACCENT_COLORS = [
    '#3B82F6',  # iOS Blue
    '#10B981',  # Emerald
    '#F59E0B',  # Amber
    '#EC4899',  # Rose Pink
    '#8B5CF6',  # Violet
    '#06B6D4',  # Cyan
    '#F97316',  # Tangerine
    '#6366F1',  # Indigo
    '#14B8A6',  # Teal
    '#E11D48'   # Crimson
]


def _apply_dark_style(fig, ax):
    """Apply high-end modern dark styling."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors='#94A3B8', labelsize=9)
    ax.xaxis.label.set_color(DARK_FG)
    ax.yaxis.label.set_color(DARK_FG)
    ax.title.set_color('#FFFFFF')
    
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
        spine.set_linewidth(1.2)


def create_bar_chart(df, x_col, y_col, title=None):
    """Bar chart with rounded aesthetics and gradient-like accent fills."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    plot_df = df.copy()
    if len(plot_df) > 18:
        if pd.api.types.is_numeric_dtype(plot_df[y_col]):
            plot_df = plot_df.nlargest(18, y_col)
        else:
            plot_df = plot_df.head(18)
    
    ax.bar(
        range(len(plot_df)),
        plot_df[y_col],
        color=ACCENT_COLORS[:len(plot_df)],
        edgecolor='#1E232E',
        linewidth=1.2,
        width=0.62,
        alpha=0.92
    )
    
    ax.set_xticks(range(len(plot_df)))
    ax.set_xticklabels(
        plot_df[x_col].astype(str),
        rotation=35,
        ha='right',
        fontsize=9,
        fontweight='medium'
    )
    
    ax.set_xlabel(x_col, fontsize=10, labelpad=8)
    ax.set_ylabel(y_col, fontsize=10, labelpad=8)
    ax.set_title(title or f"{y_col} by {x_col}", fontsize=13, fontweight='bold', pad=12)
    ax.grid(axis='y', linestyle='--', alpha=0.35, color=GRID_COLOR)
    
    fig.tight_layout()
    return fig


def create_line_chart(df, x_col, y_col, title=None):
    """
    Clean line chart with smart point downsampling.
    Prevents overcrowded vertical bars when plotting hundreds of records.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    plot_df = df.copy()
    
    # Downsample if too many points to avoid crowded visual noise
    total_pts = len(plot_df)
    if total_pts > 60:
        step = max(1, total_pts // 50)
        plot_df = plot_df.iloc[::step].copy()
    
    show_markers = len(plot_df) <= 30
    
    ax.plot(
        plot_df[x_col].astype(str),
        plot_df[y_col],
        color='#3B82F6',
        linewidth=2.4,
        marker='o' if show_markers else None,
        markersize=5,
        markerfacecolor='#10B981',
        markeredgecolor='#FFFFFF',
        markeredgewidth=1.0,
        alpha=0.95
    )
    
    # Label formatting for X axis
    n_labels = len(plot_df)
    if n_labels > 10:
        ticks_to_show = np.linspace(0, n_labels - 1, 8, dtype=int)
        ax.set_xticks(ticks_to_show)
        ax.set_xticklabels([str(plot_df[x_col].iloc[i]) for i in ticks_to_show], rotation=35, ha='right', fontsize=9)
    else:
        plt.xticks(rotation=35, ha='right', fontsize=9)
    
    ax.set_xlabel(x_col, fontsize=10, labelpad=8)
    ax.set_ylabel(y_col, fontsize=10, labelpad=8)
    ax.set_title(title or f"{y_col} Trend over {x_col}", fontsize=13, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.35, color=GRID_COLOR)
    
    fig.tight_layout()
    return fig


def create_pie_chart(df, label_col, value_col, title=None):
    """Donut/Pie chart with modern slice separation and legible labels."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    plot_df = df.copy()
    if len(plot_df) > 7:
        if pd.api.types.is_numeric_dtype(plot_df[value_col]):
            plot_df = plot_df.sort_values(value_col, ascending=False)
            top = plot_df.head(6)
            other_val = plot_df.iloc[6:][value_col].sum()
            other_row = pd.DataFrame({label_col: ['Other'], value_col: [other_val]})
            plot_df = pd.concat([top, other_row], ignore_index=True)
    
    wedges, texts, autotexts = ax.pie(
        plot_df[value_col],
        labels=plot_df[label_col].astype(str),
        colors=ACCENT_COLORS[:len(plot_df)],
        autopct='%1.1f%%',
        startangle=140,
        pctdistance=0.75,
        wedgeprops=dict(width=0.6, edgecolor=DARK_BG, linewidth=2),
        textprops={'color': DARK_FG, 'fontsize': 9}
    )
    
    for autotext in autotexts:
        autotext.set_color('#FFFFFF')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
        
    ax.set_title(title or f"Distribution: {value_col}", fontsize=13, fontweight='bold', pad=12)
    fig.tight_layout()
    return fig


def create_histogram(df, col, bins=20, title=None):
    """Histogram with clean density bars."""
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    ax.hist(
        df[col].dropna(),
        bins=bins,
        color='#6366F1',
        edgecolor=DARK_BG,
        linewidth=1.2,
        alpha=0.88
    )
    
    ax.set_xlabel(col, fontsize=10, labelpad=8)
    ax.set_ylabel("Frequency", fontsize=10, labelpad=8)
    ax.set_title(title or f"Distribution of {col}", fontsize=13, fontweight='bold', pad=12)
    ax.grid(axis='y', linestyle='--', alpha=0.35, color=GRID_COLOR)
    
    fig.tight_layout()
    return fig


def create_auto_chart(df, title="AI Analysis Result"):
    """Auto-picks the optimal chart format."""
    if df is None or df.empty or len(df.columns) < 1:
        return None
        
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    numeric_cols = [c for c in numeric_cols if '_id' not in c.lower()]
    
    # 1. Single column
    if len(df.columns) == 1:
        if numeric_cols:
            return create_histogram(df, numeric_cols[0], title=title)
        return None
        
    # 2. Categorical + Numeric
    if text_cols and numeric_cols:
        if len(df) <= 6:
            return create_pie_chart(df, text_cols[0], numeric_cols[0], title=title)
        return create_bar_chart(df, text_cols[0], numeric_cols[0], title=title)
        
    # 3. Two Numeric columns:
    # If the rows exceed 40, a histogram distribution of the metric is far more informative than a massive point mesh
    if len(numeric_cols) >= 2:
        if len(df) > 40:
            # Show distribution of the target metric
            return create_histogram(df, numeric_cols[1], bins=25, title=f"Distribution of {numeric_cols[1]}")
        return create_line_chart(df, numeric_cols[0], numeric_cols[1], title=title)
        
    # 4. Fallback
    cols = list(df.columns)
    if len(cols) >= 2:
        return create_bar_chart(df, cols[0], cols[1], title=title)
        
    return None
