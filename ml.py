"""
ml.py — Machine Learning Module (Polished Aesthetics)
======================================================
Linear Regression & KMeans clustering with high-contrast, modern dark visuals.
"""

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

DARK_BG = '#18191E'
DARK_FG = '#E2E8F0'
GRID_COLOR = '#262934'

ACCENT_COLORS = [
    '#3B82F6', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6',
    '#06B6D4', '#F97316', '#6366F1', '#14B8A6', '#E11D48'
]


def _apply_dark_style(fig, ax):
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors='#94A3B8', labelsize=9)
    ax.xaxis.label.set_color(DARK_FG)
    ax.yaxis.label.set_color(DARK_FG)
    ax.title.set_color('#FFFFFF')
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
        spine.set_linewidth(1.2)


def run_linear_regression(df, feature_col, target_col):
    clean_df = df[[feature_col, target_col]].dropna()
    if len(clean_df) < 5:
        raise ValueError(f"Need at least 5 valid data points, but only got {len(clean_df)}.")
        
    X = clean_df[feature_col].values.reshape(-1, 1)
    y = clean_df[target_col].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    slope = model.coef_[0]
    intercept = model.intercept_
    equation = f"{target_col} = {slope:.3f} × {feature_col} + {intercept:.3f}"
    
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    ax.scatter(
        X_train, y_train,
        color='#3B82F6', alpha=0.55, s=36, edgecolors='none',
        label=f'Train set ({len(X_train)})'
    )
    ax.scatter(
        X_test, y_test,
        color='#10B981', alpha=0.85, s=48, edgecolors='#FFFFFF', linewidths=0.8,
        label=f'Test set ({len(X_test)})', marker='D'
    )
    
    x_line = np.linspace(X.min(), X.max(), 120).reshape(-1, 1)
    y_line = model.predict(x_line)
    ax.plot(
        x_line, y_line,
        color='#EF4444', linewidth=2.4, linestyle='--',
        label=f'Fit (R² = {r2:.3f})'
    )
    
    ax.set_xlabel(feature_col, fontsize=10, labelpad=8)
    ax.set_ylabel(target_col, fontsize=10, labelpad=8)
    ax.set_title(f"Linear Regression: {target_col} vs {feature_col}", fontsize=13, fontweight='bold', pad=12)
    ax.legend(facecolor='#22252D', edgecolor='#2B2F3A', labelcolor=DARK_FG, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.35, color=GRID_COLOR)
    
    fig.tight_layout()
    return {
        'r2': r2,
        'mae': mae,
        'equation': equation,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'figure': fig
    }


def run_kmeans(df, col_x, col_y, n_clusters=3):
    clean_df = df[[col_x, col_y]].dropna()
    if len(clean_df) < n_clusters:
        raise ValueError(f"Need at least {n_clusters} data points for {n_clusters} clusters.")
        
    X = clean_df[[col_x, col_y]].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X_scaled)
    centroids_original = scaler.inverse_transform(kmeans.cluster_centers_)
    
    cluster_sizes = {}
    for i in range(n_clusters):
        cluster_sizes[f"Cluster {i+1}"] = int((labels == i).sum())
        
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    for i in range(n_clusters):
        mask = labels == i
        ax.scatter(
            X[mask, 0], X[mask, 1],
            color=ACCENT_COLORS[i % len(ACCENT_COLORS)],
            alpha=0.75, s=44, edgecolors='none',
            label=f'Cluster {i+1} ({cluster_sizes[f"Cluster {i+1}"]})'
        )
        
    ax.scatter(
        centroids_original[:, 0],
        centroids_original[:, 1],
        color='#FFFFFF', marker='X', s=160,
        edgecolors='#000000', linewidths=1.5,
        label='Centroids', zorder=6
    )
    
    ax.set_xlabel(col_x, fontsize=10, labelpad=8)
    ax.set_ylabel(col_y, fontsize=10, labelpad=8)
    ax.set_title(f"K-Means Clustering (K={n_clusters})", fontsize=13, fontweight='bold', pad=12)
    ax.legend(facecolor='#22252D', edgecolor='#2B2F3A', labelcolor=DARK_FG, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.35, color=GRID_COLOR)
    
    fig.tight_layout()
    return {
        'n_clusters': n_clusters,
        'cluster_sizes': cluster_sizes,
        'centroids': centroids_original.tolist(),
        'inertia': kmeans.inertia_,
        'figure': fig
    }
