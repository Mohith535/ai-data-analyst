"""
db.py — Database module for AI Data Analyst (Robust Column Sanitization)
========================================================================
Handles all MySQL interactions:
  - Connecting to MySQL server
  - Creating database
  - Loading DataFrame into table with robust column name sanitization
  - Running queries safely
  - Listing tables & extracting schemas
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import re
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection(use_database=True):
    try:
        config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
        if use_database:
            config["database"] = os.getenv("DB_NAME", "analyst_db")
        return mysql.connector.connect(**config)
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


def initialize_database():
    conn = get_connection(use_database=False)
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        db_name = os.getenv("DB_NAME", "analyst_db")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] Could not create database: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def sanitize_table_name(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name).strip('_').lower()
    if name and name[0].isdigit():
        name = 't_' + name
    return name or 'uploaded_data'


def sanitize_column_name(col_name):
    """
    Sanitize CSV column headers into reliable MySQL column identifiers.
    
    Why:
      CSV files often have trailing spaces, quotes, parentheses, dollar signs,
      slashes, or control characters (e.g. 'Unit_Cost ', 'Price ($)', 'Order/ID').
      In MySQL, identifiers with trailing whitespace or special characters
      trigger Error 1166 (42000): Incorrect column name.
    """
    col = str(col_name).strip()
    # Strip any enclosing quotes
    col = col.strip("'\"`")
    # Replace any non-alphanumeric character with underscore
    col = re.sub(r'[^a-zA-Z0-9_]', '_', col)
    # Collapse multiple underscores
    col = re.sub(r'_+', '_', col).strip('_')
    # If empty or begins with digit, prefix safely
    if not col:
        col = 'col'
    elif col[0].isdigit():
        col = 'c_' + col
    return col


def get_mysql_type(dtype):
    dtype_str = str(dtype)
    if 'int' in dtype_str:
        return 'BIGINT'
    elif 'float' in dtype_str:
        return 'DOUBLE'
    elif 'bool' in dtype_str:
        return 'BOOLEAN'
    elif 'datetime' in dtype_str:
        return 'DATETIME'
    else:
        return 'TEXT'


def load_dataframe_to_mysql(df, table_name):
    """
    Persist DataFrame into MySQL with cleaned column headers.
    """
    conn = get_connection()
    if conn is None:
        return False, "Could not connect to MySQL. Is the server running?"
    
    try:
        cursor = conn.cursor()
        
        # 1. Sanitize all DataFrame column names cleanly to avoid Error 1166
        clean_df = df.copy()
        new_columns = []
        seen = {}
        for c in clean_df.columns:
            clean_c = sanitize_column_name(c)
            # Avoid duplicate column names
            if clean_c in seen:
                seen[clean_c] += 1
                clean_c = f"{clean_c}_{seen[clean_c]}"
            else:
                seen[clean_c] = 0
            new_columns.append(clean_c)
        clean_df.columns = new_columns
        
        # 2. Build CREATE TABLE SQL
        columns_sql = []
        for col_name in clean_df.columns:
            mysql_type = get_mysql_type(clean_df[col_name].dtype)
            columns_sql.append(f"`{col_name}` {mysql_type}")
        
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `_id` INT AUTO_INCREMENT PRIMARY KEY,
                {', '.join(columns_sql)}
            )
        """
        
        # 3. Drop existing table & recreate
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute(create_sql)
        
        # 4. Insert rows in batches of 1,000 to prevent packet size overflows
        placeholders = ', '.join(['%s'] * len(clean_df.columns))
        col_names = ', '.join([f"`{c}`" for c in clean_df.columns])
        insert_sql = f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})"
        
        data = clean_df.where(pd.notnull(clean_df), None).values.tolist()
        clean_data = []
        for row in data:
            clean_row = []
            for val in row:
                if val is None:
                    clean_row.append(None)
                elif hasattr(val, 'item'):
                    clean_row.append(val.item())
                else:
                    clean_row.append(val)
            clean_data.append(tuple(clean_row))
        
        batch_size = 1000
        for i in range(0, len(clean_data), batch_size):
            cursor.executemany(insert_sql, clean_data[i:i + batch_size])
        conn.commit()
        
        return True, f"Ingested {len(clean_data)} rows into table `{table_name}`"
    
    except Error as e:
        return False, f"MySQL error: {e}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def run_query(sql):
    """
    Execute a read query and return results as a Pandas DataFrame.
    Uses native cursor fetch to avoid Pandas/SQLAlchemy DBAPI UserWarnings.
    Enforces session-level read-only safety and execution timeout.
    """
    conn = get_connection()
    if conn is None:
        return None, "Could not connect to MySQL."
    try:
        cursor = conn.cursor()
        
        # Defense-in-depth: Set read-only session transaction
        try:
            cursor.execute("SET SESSION TRANSACTION READ ONLY")
        except Exception:
            pass
            
        # Defense-in-depth: Set 5-second query timeout (MySQL 8.0+ / MariaDB)
        try:
            cursor.execute("SET SESSION max_execution_time = 5000")
        except Exception:
            try:
                cursor.execute("SET SESSION max_statement_time = 5")
            except Exception:
                pass
                
        cursor.execute(sql)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            df = pd.DataFrame(data, columns=columns)
        else:
            df = pd.DataFrame()
        cursor.close()
        return df, None
    except Exception as e:
        return None, f"Query error: {e}"
    finally:
        if conn and conn.is_connected():
            conn.close()


def list_tables():
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return [row[0] for row in cursor.fetchall()]
    except Error as e:
        print(f"[DB ERROR] Could not list tables: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_table_schema(table_name):
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`")
        schema = []
        for row in cursor.fetchall():
            schema.append({'column': row[0], 'type': row[1]})
        return schema
    except Error as e:
        print(f"[DB ERROR] Could not get schema for '{table_name}': {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_table_columns(table_name):
    schema = get_table_schema(table_name)
    return [s['column'] for s in schema if s['column'] != '_id']
