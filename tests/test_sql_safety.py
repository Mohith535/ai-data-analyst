"""
test_sql_safety.py — Unit Tests for AST SQL Validation & Injection Defense
===========================================================================
Tests sqlglot-based AST validation in ai_chat.validate_sql().
Verifies:
  - Legitimate analytical queries pass (CTEs, scalar functions, string literals with semicolons)
  - Column names matching SQL keywords (e.g. `update`) are allowed
  - All SQL injection, file exfiltration, and DoS attacks are rejected
  - Mandatory LIMIT capping/appending is enforced
"""

import pytest
import sys
import os

# Add parent directory to sys.path so ai_chat can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_chat import validate_sql


class TestSQLSafetyAST:
    """Test suite for sqlglot AST-based SQL firewall."""

    # -------------------------------------------------------------
    # 1. Legitimate Queries (MUST PASS)
    # -------------------------------------------------------------
    def test_standard_select(self):
        ok, sql = validate_sql("SELECT * FROM sales_data")
        assert ok is True
        assert "LIMIT 1000" in sql.upper()

    def test_cte_query(self):
        query = (
            "WITH monthly AS ("
            "  SELECT category, SUM(amount) AS total "
            "  FROM sales_data GROUP BY category"
            ") "
            "SELECT * FROM monthly"
        )
        ok, sql = validate_sql(query)
        assert ok is True
        assert "WITH" in sql.upper()

    def test_scalar_replace_function_allowed(self):
        """Scalar string REPLACE() function must NOT be blocked by keyword ban."""
        query = "SELECT REPLACE(category, 'Old', 'New') FROM sales_data"
        ok, sql = validate_sql(query)
        assert ok is True
        assert "REPLACE" in sql.upper()

    def test_column_named_keyword_allowed(self):
        """A column named `update` must NOT be falsely identified as an UPDATE statement."""
        query = "SELECT `update`, category FROM sales_data"
        ok, sql = validate_sql(query)
        assert ok is True

    def test_semicolon_inside_string_literal_allowed(self):
        """Semicolons inside quoted string literals must NOT trigger multiple-statement errors."""
        query = "SELECT * FROM sales_data WHERE notes = '; DROP TABLE users;'"
        ok, sql = validate_sql(query)
        assert ok is True

    def test_markdown_fences_stripped(self):
        query = "```sql\nSELECT category, amount FROM sales_data\n```"
        ok, sql = validate_sql(query)
        assert ok is True
        assert "SELECT" in sql.upper()

    # -------------------------------------------------------------
    # 2. LIMIT Enforcement
    # -------------------------------------------------------------
    def test_limit_appended_when_missing(self):
        ok, sql = validate_sql("SELECT id FROM sales_data")
        assert ok is True
        assert "LIMIT 1000" in sql.upper()

    def test_excessive_limit_capped_to_1000(self):
        ok, sql = validate_sql("SELECT id FROM sales_data LIMIT 50000")
        assert ok is True
        assert "LIMIT 1000" in sql.upper()
        assert "50000" not in sql

    def test_reasonable_limit_preserved(self):
        ok, sql = validate_sql("SELECT id FROM sales_data LIMIT 25")
        assert ok is True
        assert "LIMIT 25" in sql.upper()

    # -------------------------------------------------------------
    # 3. Blocked Attack Vectors (MUST FAIL)
    # -------------------------------------------------------------
    def test_block_drop_table(self):
        ok, err = validate_sql("DROP TABLE sales_data")
        assert ok is False

    def test_block_update_statement(self):
        ok, err = validate_sql("UPDATE sales_data SET amount = 0")
        assert ok is False

    def test_block_delete_statement(self):
        ok, err = validate_sql("DELETE FROM sales_data WHERE id = 1")
        assert ok is False

    def test_block_insert_statement(self):
        ok, err = validate_sql("INSERT INTO sales_data (id) VALUES (1)")
        assert ok is False

    def test_block_alter_table(self):
        ok, err = validate_sql("ALTER TABLE sales_data DROP COLUMN amount")
        assert ok is False

    def test_block_multiple_statements(self):
        ok, err = validate_sql("SELECT 1; SELECT 2")
        assert ok is False
        assert "multiple" in err.lower()

    def test_block_into_outfile(self):
        """File exfiltration via INTO OUTFILE must be blocked by AST."""
        ok, err = validate_sql("SELECT * FROM sales_data INTO OUTFILE '/tmp/leak.csv'")
        assert ok is False
        assert "file export" in err.lower()

    def test_block_into_dumpfile(self):
        ok, err = validate_sql("SELECT * FROM sales_data INTO DUMPFILE '/tmp/leak.bin'")
        assert ok is False

    def test_block_sleep_dos(self):
        """Denial of Service via SLEEP() must be caught by dangerous functions list."""
        ok, err = validate_sql("SELECT SLEEP(10) FROM sales_data")
        assert ok is False
        assert "SLEEP" in err

    def test_block_benchmark_dos(self):
        ok, err = validate_sql("SELECT BENCHMARK(10000000, MD5(1))")
        assert ok is False
        assert "BENCHMARK" in err

    def test_block_load_file(self):
        """Arbitrary local file reading via LOAD_FILE() must be blocked."""
        ok, err = validate_sql("SELECT LOAD_FILE('/etc/passwd')")
        assert ok is False
        assert "LOAD_FILE" in err

    def test_block_empty_query(self):
        ok, err = validate_sql("   ")
        assert ok is False
