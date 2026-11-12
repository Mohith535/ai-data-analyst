"""
db.py — Database module for AI Data Analyst
============================================
Handles all MySQL interactions:
  - Connecting to MySQL server
  - Creating the database if it doesn't exist
  - Loading a pandas DataFrame into a MySQL table
  - Running arbitrary SQL queries
  - Listing all tables
  - Getting table schema (column names and types)

WHY a separate module?
  Keeps database logic out of the UI code. If we ever switch
  databases (e.g., to PostgreSQL), we only change this file.
"""

import mysql.connector
from mysql.connector import Error
import pandas as pd
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# WHY? So we never hardcode passwords or API keys in source code.
load_dotenv()


def get_connection(use_database=True):
    """
    Create and return a MySQL connection.
    
    Parameters:
        use_database (bool): If True, connect to the specific database.
                            If False, connect to MySQL server only (for creating DB).
    
    Returns:
        mysql.connector.connection.MySQLConnection or None
    
    WHY the use_database flag?
        When we first run the app, the database might not exist yet.
        We need to connect WITHOUT specifying a database, then CREATE it.
        After that, we connect WITH the database.
    """
    try:
        config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
        }
        if use_database:
            config["database"] = os.getenv("DB_NAME", "analyst_db")
        
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


def initialize_database():
    """
    Create the database if it doesn't exist.
    
    Called once when the app starts. Uses use_database=False
    because the DB might not exist yet.
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection(use_database=False)
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        db_name = os.getenv("DB_NAME", "analyst_db")
        # CREATE DATABASE IF NOT EXISTS — safe to run multiple times
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        conn.commit()
        print(f"[DB] Database '{db_name}' is ready.")
        return True
    except Error as e:
        print(f"[DB ERROR] Could not create database: {e}")
        return False
    finally:
        # ALWAYS close connections to avoid leaks
        if conn.is_connected():
            cursor.close()
            conn.close()


def sanitize_table_name(filename):
    """
    Convert a CSV filename into a valid MySQL table name.
    
    Examples:
        "Sales Data (2024).csv"  →  "sales_data_2024"
        "my-file.csv"            →  "my_file"
    
    WHY?
        MySQL table names can't have spaces, hyphens, or special chars.
        We strip the extension, replace non-alphanumeric chars with underscores,
        collapse multiple underscores, and lowercase everything.
    """
    # Remove file extension
    name = os.path.splitext(filename)[0]
    # Replace any non-alphanumeric character with underscore
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Collapse multiple underscores into one
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Lowercase for consistency
    name = name.lower()
    # If name starts with a digit, prefix with 't_' (MySQL tables can't start with digits in some contexts)
    if name and name[0].isdigit():
        name = 't_' + name
    # Fallback if name is empty
    if not name:
        name = 'uploaded_data'
    return name


def get_mysql_type(dtype):
    """
    Map a pandas dtype to a MySQL column type.
    
    WHY not let pandas.to_sql() do this?
        pandas.to_sql() works great with SQLAlchemy, but we're using
        mysql-connector-python directly (simpler dependency).
        So we manually map types.
    """
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
        # Default: TEXT for strings and anything else
        return 'TEXT'


def load_dataframe_to_mysql(df, table_name):
    """
    Create a MySQL table from a pandas DataFrame and insert all rows.
    
    Parameters:
        df (pd.DataFrame): The data to store
        table_name (str): Already-sanitized table name
    
    Returns:
        tuple: (success: bool, message: str)
    
    HOW IT WORKS:
        1. Build a CREATE TABLE statement from the DataFrame's columns and dtypes
        2. Drop the table if it already exists (so re-uploading replaces data)
        3. Insert rows in batches using executemany() for speed
    """
    conn = get_connection()
    if conn is None:
        return False, "Could not connect to MySQL. Is the server running?"
    
    try:
        cursor = conn.cursor()
        
        # --- Step 1: Build CREATE TABLE SQL ---
        columns_sql = []
        for col_name in df.columns:
            # Backtick column names to handle spaces and reserved words
            mysql_type = get_mysql_type(df[col_name].dtype)
            safe_col = f"`{col_name}`"
            columns_sql.append(f"{safe_col} {mysql_type}")
        
        # Add an auto-increment primary key for good practice
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `_id` INT AUTO_INCREMENT PRIMARY KEY,
                {', '.join(columns_sql)}
            )
        """
        
        # --- Step 2: Drop existing table (re-upload = replace) ---
        cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
        cursor.execute(create_sql)
        
        # --- Step 3: Insert rows ---
        # Build INSERT statement with %s placeholders
        placeholders = ', '.join(['%s'] * len(df.columns))
        col_names = ', '.join([f"`{c}`" for c in df.columns])
        insert_sql = f"INSERT INTO `{table_name}` ({col_names}) VALUES ({placeholders})"
        
        # Convert DataFrame to list of tuples
        # Replace NaN with None (MySQL NULL)
        data = df.where(pd.notnull(df), None).values.tolist()
        # Convert numpy types to Python types for mysql-connector
        clean_data = []
        for row in data:
            clean_row = []
            for val in row:
                if val is None:
                    clean_row.append(None)
                elif hasattr(val, 'item'):
                    # numpy int64/float64 → Python int/float
                    clean_row.append(val.item())
                else:
                    clean_row.append(val)
            clean_data.append(tuple(clean_row))
        
        # executemany is faster than individual inserts
        cursor.executemany(insert_sql, clean_data)
        conn.commit()
        
        row_count = len(clean_data)
        return True, f"Loaded {row_count} rows into table '{table_name}'"
    
    except Error as e:
        return False, f"MySQL error: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def run_query(sql):
    """
    Execute a SQL query and return results as a pandas DataFrame.
    
    Parameters:
        sql (str): The SQL query to execute (should be SELECT only for safety)
    
    Returns:
        tuple: (df: pd.DataFrame or None, error: str or None)
    
    WHY return a DataFrame?
        DataFrames are easy to display in Treeview and to plot with matplotlib.
    """
    conn = get_connection()
    if conn is None:
        return None, "Could not connect to MySQL."
    
    try:
        # pd.read_sql() executes the query and returns a DataFrame directly
        df = pd.read_sql(sql, conn)
        return df, None
    except Exception as e:
        return None, f"Query error: {e}"
    finally:
        if conn.is_connected():
            conn.close()


def list_tables():
    """
    Get a list of all table names in the database.
    
    Returns:
        list[str]: Table names, or empty list on error
    
    Used by the Charts tab and ML tab to let the user pick which dataset to work with.
    """
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        # cursor returns list of tuples like [('sales_data',), ('products',)]
        tables = [row[0] for row in cursor.fetchall()]
        return tables
    except Error as e:
        print(f"[DB ERROR] Could not list tables: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_table_schema(table_name):
    """
    Get column names and types for a specific table.
    
    Returns:
        list[dict]: Each dict has 'column' and 'type' keys.
                    Example: [{'column': 'product', 'type': 'TEXT'}, ...]
    
    WHY?
        - The Charts/ML tabs need column names for dropdowns
        - The AI Chat tab sends this schema to Groq (NOT the actual data)
          so the LLM can write correct SQL without seeing private data
    """
    conn = get_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE `{table_name}`")
        # DESCRIBE returns: (Field, Type, Null, Key, Default, Extra)
        schema = []
        for row in cursor.fetchall():
            schema.append({
                'column': row[0],
                'type': row[1]
            })
        return schema
    except Error as e:
        print(f"[DB ERROR] Could not get schema for '{table_name}': {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_table_columns(table_name):
    """
    Convenience function: get just the column names (no types) for a table.
    Filters out the auto-generated '_id' column since users didn't upload it.
    
    Returns:
        list[str]: Column names
    """
    schema = get_table_schema(table_name)
    return [s['column'] for s in schema if s['column'] != '_id']

