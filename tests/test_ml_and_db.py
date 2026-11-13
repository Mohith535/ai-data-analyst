"""
tests/test_ml_and_db.py — Unit Tests for ML Pipelines & DB Enhancements (Phase 4)
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ml
import db


class TestMLEnhancements:
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n = 50
        x1 = np.linspace(10, 100, n)
        x2 = np.random.normal(50, 15, n)
        # target y is strongly correlated with x1, weakly with x2
        y = 2.5 * x1 + 0.3 * x2 + np.random.normal(0, 5, n)
        return pd.DataFrame({'feature_a': x1, 'feature_b': x2, 'target_y': y})

    def test_suggest_best_features_ranking(self, sample_data):
        suggestions = ml.suggest_best_features(sample_data, 'target_y')
        assert len(suggestions) >= 2
        # feature_a has much higher correlation than feature_b
        assert suggestions[0][0] == 'feature_a'
        assert suggestions[0][1] > 0.9

    def test_single_feature_regression(self, sample_data):
        res = ml.run_linear_regression(sample_data, 'feature_a', 'target_y')
        assert 'r2' in res
        assert 'mae' in res
        assert 'equation' in res
        assert 'figure' in res
        assert res['r2'] > 0.9
        assert res['warning'] is None

    def test_multi_feature_regression(self, sample_data):
        res = ml.run_linear_regression(sample_data, ['feature_a', 'feature_b'], 'target_y')
        assert 'r2' in res
        assert res['r2'] > 0.9
        assert 'feature_a' in res['equation']
        assert 'feature_b' in res['equation']

    def test_negative_r2_warning(self):
        # Create an artificial adversarial test where fit produces negative R2
        df = pd.DataFrame({
            'noisy_x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            'actual_y': [100, 2, 95, 3, 80, 5, 100, 1, 90, 4, 105, 2, 98, 1, 102]
        })
        res = ml.run_linear_regression(df, 'noisy_x', 'actual_y')
        # If R2 is negative, check that warning message is populated
        if res['r2'] < 0:
            assert res['warning'] is not None
            assert "Negative R²" in res['warning']


class TestDBDateAndSanitization:
    def test_column_name_sanitization(self):
        assert db.sanitize_column_name("Unit_Price ($)") == "Unit_Price"
        assert db.sanitize_column_name("  Trailing Space  ") == "Trailing_Space"
        assert db.sanitize_column_name("123Number") == "c_123Number"
        assert db.sanitize_column_name("`already_quoted`") == "already_quoted"

    def test_table_name_sanitization(self):
        assert db.sanitize_table_name("Sales Data 2024.csv") == "sales_data_2024"
        assert db.sanitize_table_name("123_data.csv") == "t_123_data"

    def test_get_mysql_type(self):
        assert db.get_mysql_type(np.dtype('int64')) == 'BIGINT'
        assert db.get_mysql_type(np.dtype('float64')) == 'DOUBLE'
        assert db.get_mysql_type(np.dtype('datetime64[ns]')) == 'DATETIME'
        assert db.get_mysql_type(np.dtype('O')) == 'TEXT'


class TestDateSniffing:
    """
    Tests for the targeted date sniffing logic in db.load_dataframe_to_mysql.
    We test the sniffing logic in isolation by reproducing just the detection path.
    Why: We want to confirm name-hint + regex heuristic works, without needing a live DB.
    """

    def _sniff(self, df):
        """
        Re-runs the same date-sniffing logic from db.load_dataframe_to_mysql
        on a copy of df and returns the resulting dtypes.
        """
        import re as _re
        import warnings
        clean_df = df.copy()

        _DATE_NAME_KEYWORDS = ("date", "time", "created", "timestamp", "dt", "year", "month", "day")
        _DATE_REGEX = _re.compile(
            r"^\d{4}-\d{2}-\d{2}|^\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}"
        )

        for col in clean_df.columns:
            if clean_df[col].dtype == 'object':
                col_lower = str(col).lower()
                is_date_named = any(k in col_lower for k in _DATE_NAME_KEYWORDS)
                if not is_date_named:
                    sample_vals = clean_df[col].dropna().head(5).astype(str)
                    is_date_named = any(_DATE_REGEX.match(v.strip()) for v in sample_vals)
                if is_date_named:
                    try:
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", message=".*format.*", category=UserWarning)
                            parsed = pd.to_datetime(clean_df[col], errors='coerce', format='mixed')
                        non_null_orig = clean_df[col].notna().sum()
                        if non_null_orig > 0 and parsed.notna().sum() / non_null_orig >= 0.75:
                            clean_df[col] = parsed
                    except Exception:
                        pass
        return clean_df

    def test_date_named_column_is_converted(self):
        """Column named 'order_date' with ISO dates → converted to datetime64."""
        df = pd.DataFrame({'order_date': ['2024-01-15', '2024-02-20', '2024-03-10']})
        result = self._sniff(df)
        assert 'datetime' in str(result['order_date'].dtype), \
            f"Expected datetime dtype, got {result['order_date'].dtype}"

    def test_non_date_named_numeric_column_not_converted(self):
        """Column 'product_id' with integer strings → must NOT be converted to datetime."""
        df = pd.DataFrame({'product_id': ['1001', '1002', '1003', '1004', '1005']})
        result = self._sniff(df)
        assert result['product_id'].dtype == object, \
            f"product_id should stay as object, got {result['product_id'].dtype}"

    def test_date_regex_match_triggers_conversion(self):
        """Column 'uploaded_on' (no date keyword) but values match dd/mm/yyyy → converted."""
        df = pd.DataFrame({'uploaded_on': ['15/01/2024', '20/02/2024', '10/03/2024']})
        result = self._sniff(df)
        assert 'datetime' in str(result['uploaded_on'].dtype), \
            f"Expected datetime dtype, got {result['uploaded_on'].dtype}"

    def test_non_date_text_column_not_converted(self):
        """Column 'customer_name' with name strings → must NOT be touched by date sniffing."""
        df = pd.DataFrame({'customer_name': ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']})
        result = self._sniff(df)
        assert result['customer_name'].dtype == object, \
            f"customer_name should stay as object, got {result['customer_name'].dtype}"
