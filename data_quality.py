"""
data_quality.py — Automated Dataset Quality & Hygiene Profiler
===============================================================
Performs deep dataset profiling:
  - Total records & column count
  - Missing value counts & completeness percentages
  - Duplicate row detection
  - Column datatype distribution
  - Numerical summary (Min, Max, Mean, Outlier detection via IQR)
"""

import pandas as pd
import numpy as np


def profile_dataset(df):
    """
    Run automated quality checks across a DataFrame.
    
    Returns:
        dict: Hygiene statistics and column-level metrics
    """
    if df is None or df.empty:
        return None
        
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    
    # 1. Missing Values Analysis
    missing_by_col = df.isnull().sum().to_dict()
    total_missing = sum(missing_by_col.values())
    completeness_score = ((total_cells - total_missing) / max(1, total_cells)) * 100
    
    # 2. Duplicate Detection
    duplicate_rows = int(df.duplicated().sum())
    
    # 3. Column Statistics
    col_profiles = []
    for col in df.columns:
        col_series = df[col]
        dtype = str(col_series.dtype)
        n_missing = int(col_series.isnull().sum())
        missing_pct = (n_missing / max(1, total_rows)) * 100
        n_unique = int(col_series.nunique())
        
        info = {
            "name": str(col),
            "dtype": dtype,
            "missing": n_missing,
            "missing_pct": round(missing_pct, 1),
            "unique": n_unique,
            "outliers": 0,
            "stats": ""
        }
        
        # Numerical outlier check using IQR rule (1.5 * IQR)
        if pd.api.types.is_numeric_dtype(col_series) and col != '_id':
            clean_s = col_series.dropna()
            if len(clean_s) > 4:
                q25 = clean_s.quantile(0.25)
                q75 = clean_s.quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outlier_count = int(((clean_s < lower_bound) | (clean_s > upper_bound)).sum())
                info["outliers"] = outlier_count
                info["stats"] = f"Min: {clean_s.min():.1f} | Avg: {clean_s.mean():.1f} | Max: {clean_s.max():.1f}"
        col_profiles.append(info)
        
    return {
        "rows": total_rows,
        "cols": total_cols,
        "completeness": round(completeness_score, 1),
        "total_missing": total_missing,
        "duplicates": duplicate_rows,
        "columns": col_profiles
    }
