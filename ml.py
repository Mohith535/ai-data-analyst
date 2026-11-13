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


def suggest_best_features(df, target_col, top_n=3):
    """
    Computes Pearson correlation between all numeric features and target_col.
    Returns list of tuples: (col_name, correlation_value).
    Sorted from strongest correlation to weakest (|r| descending).
    Useful for guiding users away from arbitrary feature selection.
    """
    numeric_df = df.select_dtypes(include=['number']).copy()
    if target_col not in numeric_df.columns:
        return []
    
    corrs = []
    for col in numeric_df.columns:
        if col == target_col or col in ('_id', 'id', 'order_id'):
            continue
        valid = numeric_df[[col, target_col]].dropna()
        if len(valid) >= 3 and valid[col].std() > 0:
            corr = valid[col].corr(valid[target_col])
            if not np.isnan(corr):
                corrs.append((col, float(corr), abs(float(corr))))
                
    corrs.sort(key=lambda x: x[2], reverse=True)
    return [(col, corr) for col, corr, _ in corrs[:top_n]]


def run_linear_regression(df, feature_cols, target_col):
    """
    Fits Ordinary Least Squares Linear Regression.
    Supports single feature (str) or multi-feature (list of str).
    
    Why:
      - Multi-feature regression allows capturing joint effects (e.g., Price and Quantity).
      - If R² is negative on unseen test split, explains that residual variance exceeds
        total target variance (worse than mean prediction) and suggests top correlated feature.
    """
    if isinstance(feature_cols, str):
        feature_cols = [feature_cols]
    else:
        feature_cols = list(feature_cols)
    
    cols_to_use = feature_cols + [target_col]
    clean_df = df[cols_to_use].copy()
    for c in cols_to_use:
        clean_df[c] = pd.to_numeric(clean_df[c], errors='coerce')
    clean_df = clean_df.dropna()
    
    min_rows = max(5, len(feature_cols) + 2)
    if len(clean_df) < min_rows:
        raise ValueError(f"Need at least {min_rows} valid numeric rows, but only found {len(clean_df)}.")
        
    X = clean_df[feature_cols].values
    y = clean_df[target_col].values
    
    if len(clean_df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    else:
        X_train, X_test, y_train, y_test = X, X, y, y
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    intercept = float(model.intercept_)
    
    # Format formula
    if len(feature_cols) == 1:
        slope = float(model.coef_[0])
        equation = f"{target_col} = {slope:.3f} × {feature_cols[0]} + {intercept:.3f}"
    else:
        terms = [f"{coef:+.3f}×{col}" for coef, col in zip(model.coef_, feature_cols)]
        equation = f"{target_col} = " + " ".join(terms) + f" + {intercept:.3f}"
    
    # Feature suggestions and viva-ready negative R2 diagnosis
    suggestions = suggest_best_features(df, target_col)
    warning = None
    if r2 < 0:
        top_hint = f"'{suggestions[0][0]}' (r = {suggestions[0][1]:+.2f})" if suggestions else "another feature"
        warning = (
            f"Negative R² ({r2:.3f})! On unseen test data, the model's residual sum of squares "
            f"exceeds total variance (worse than horizontal mean). Top correlated feature: {top_hint}."
        )
    elif r2 < 0.2 and suggestions and suggestions[0][0] not in feature_cols:
        warning = f"Low R² ({r2:.3f}). Consider adding '{suggestions[0][0]}' (r = {suggestions[0][1]:+.2f}) to improve fit."
    
    fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=100)
    _apply_dark_style(fig, ax)
    
    if len(feature_cols) == 1:
        f_name = feature_cols[0]
        ax.scatter(
            X_train[:, 0], y_train,
            color='#3B82F6', alpha=0.55, s=36, edgecolors='none',
            label=f'Train set ({len(X_train)})'
        )
        ax.scatter(
            X_test[:, 0], y_test,
            color='#10B981', alpha=0.85, s=48, edgecolors='#FFFFFF', linewidths=0.8,
            label=f'Test set ({len(X_test)})', marker='D'
        )
        
        x_line = np.linspace(X[:, 0].min(), X[:, 0].max(), 120).reshape(-1, 1)
        y_line = model.predict(x_line)
        ax.plot(
            x_line, y_line,
            color='#EF4444', linewidth=2.4, linestyle='--',
            label=f'Fit (R² = {r2:.3f})'
        )
        
        ax.set_xlabel(f_name, fontsize=10, labelpad=8)
        ax.set_ylabel(target_col, fontsize=10, labelpad=8)
        ax.set_title(f"Linear Regression: {target_col} vs {f_name}", fontsize=13, fontweight='bold', pad=12)
    else:
        # Multi-variable: Actual vs Predicted plot with diagonal reference line
        y_train_pred = model.predict(X_train)
        ax.scatter(
            y_train, y_train_pred,
            color='#3B82F6', alpha=0.55, s=36, edgecolors='none',
            label=f'Train ({len(y_train)})'
        )
        ax.scatter(
            y_test, y_pred,
            color='#10B981', alpha=0.85, s=48, edgecolors='#FFFFFF', linewidths=0.8,
            label=f'Test ({len(y_test)})', marker='D'
        )
        
        min_v = float(min(y.min(), y_pred.min(), y_train_pred.min()))
        max_v = float(max(y.max(), y_pred.max(), y_train_pred.max()))
        ax.plot(
            [min_v, max_v], [min_v, max_v],
            color='#EF4444', linewidth=2.2, linestyle='--',
            label=f'Ideal y = ŷ (R² = {r2:.3f})'
        )
        
        ax.set_xlabel(f"Actual {target_col}", fontsize=10, labelpad=8)
        ax.set_ylabel(f"Predicted {target_col}", fontsize=10, labelpad=8)
        features_str = ", ".join(feature_cols[:2]) + ("..." if len(feature_cols) > 2 else "")
        ax.set_title(f"Multi-Variable Regression ({features_str} → {target_col})", fontsize=13, fontweight='bold', pad=12)
    
    ax.legend(facecolor='#22252D', edgecolor='#2B2F3A', labelcolor=DARK_FG, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.35, color=GRID_COLOR)
    fig.tight_layout()
    
    return {
        'r2': r2,
        'mae': mae,
        'equation': equation,
        'warning': warning,
        'suggestions': suggestions,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'figure': fig
    }


def run_kmeans(df, col_x, col_y, n_clusters=3):
    clean_df = df[[col_x, col_y]].copy()
    clean_df[col_x] = pd.to_numeric(clean_df[col_x], errors='coerce')
    clean_df[col_y] = pd.to_numeric(clean_df[col_y], errors='coerce')
    clean_df = clean_df.dropna()
    
    if len(clean_df) < n_clusters:
        raise ValueError(f"Need at least {n_clusters} valid numeric rows for {n_clusters} clusters, but found {len(clean_df)}.")
        
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
