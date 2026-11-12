"""
interactive_studio.py — Interactive Data Studio Engine (Plotly HTML Canvas)
=============================================================================
Provides high-performance interactive 3D, Zoomable, and Pan-able charts
rendered via Plotly and viewed in the user's default browser or exported to HTML.
"""

import os
import webbrowser
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def generate_interactive_chart(df, chart_type, x_col, y_col, z_col=None, color_col=None):
    """
    Generate an interactive Plotly chart and launch it in the local browser.
    
    Parameters:
        df (pd.DataFrame): Data
        chart_type (str): 'Scatter 3D', 'Interactive Bar', 'Interactive Line', 'Box Plot', 'Correlation Heatmap'
        x_col, y_col, z_col, color_col (str): Selected column dimensions
        
    Returns:
        str: Absolute path of generated HTML canvas
    """
    if df is None or df.empty:
        raise ValueError("Cannot plot an empty dataset.")
        
    output_html = os.path.join(os.path.dirname(__file__), "interactive_chart.html")
    template = "plotly_dark"
    
    if chart_type == "Scatter 3D":
        if not (x_col and y_col and z_col):
            raise ValueError("3D Scatter plot requires X, Y, and Z axes.")
        fig = px.scatter_3d(
            df, x=x_col, y=y_col, z=z_col,
            color=color_col if color_col in df.columns else None,
            title=f"Interactive 3D Scatter: {x_col} vs {y_col} vs {z_col}",
            template=template
        )
    elif chart_type == "Interactive Bar":
        fig = px.bar(
            df, x=x_col, y=y_col,
            color=color_col if color_col in df.columns else None,
            title=f"Interactive Bar Analysis: {y_col} by {x_col}",
            template=template
        )
    elif chart_type == "Interactive Line":
        fig = px.line(
            df, x=x_col, y=y_col,
            title=f"Interactive Trend Analysis: {y_col} over {x_col}",
            template=template
        )
    elif chart_type == "Box Plot":
        fig = px.box(
            df, x=x_col, y=y_col,
            title=f"Distribution & Quartiles: {y_col} grouped by {x_col}",
            template=template
        )
    elif chart_type == "Correlation Heatmap":
        numeric_df = df.select_dtypes(include=['number'])
        corr = numeric_df.corr()
        fig = px.imshow(
            corr, text_auto=True, aspect="auto",
            title="Correlation Matrix Heatmap",
            template=template, color_continuous_scale="Viridis"
        )
    else:
        fig = px.scatter(
            df, x=x_col, y=y_col,
            title=f"Interactive Scatter: {y_col} vs {x_col}",
            template=template
        )
        
    fig.update_layout(
        paper_bgcolor="#121316",
        plot_bgcolor="#18191E",
        font=dict(family="Segoe UI, sans-serif", color="#E2E8F0")
    )
    
    fig.write_html(output_html)
    webbrowser.open(f"file:///{output_html}")
    return output_html
