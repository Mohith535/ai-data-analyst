"""
ai_chat.py — Groq AI Integration (Robust Text-to-SQL with Conversational Fallback)
====================================================================================
Fix:
  - If user asks open-ended or conversational questions ("give me the overview", "only read this"),
    the prompt explicitly instructs the LLM to write a safe `SELECT * ... LIMIT 50` query
    rather than refusing with "I'm sorry, I can't help with that".
  - If the model ever outputs a non-SELECT apology, it automatically catches it and falls back
    to a standard `SELECT * FROM [table] LIMIT 25` query so analysis NEVER fails.
"""

import os
import re
import sqlglot
from sqlglot import exp
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Blacklisted functions that can be used for DoS or arbitrary file reading
DANGEROUS_FUNCTIONS = {"sleep", "benchmark", "load_file", "sys_eval", "sys_exec"}


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set or still default in .env file.\n"
            "Get your free key from https://console.groq.com and paste it in your .env file."
        )
    return Groq(api_key=api_key)


# Cached available Groq model ID to avoid redundant API network roundtrips
_CACHED_AVAILABLE_MODEL = None


def get_available_model(client, force_refresh=False):
    """
    Returns the optimal active model for SQL generation and analysis.
    Caches model discovery to save network roundtrips on every query.
    """
    global _CACHED_AVAILABLE_MODEL
    if _CACHED_AVAILABLE_MODEL and not force_refresh:
        return _CACHED_AVAILABLE_MODEL

    # Verified Groq LPU models in order of analytical capability
    preferred = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "allam-2-7b"
    ]
    try:
        remote_models = {m.id for m in client.models.list().data}
        for model in preferred:
            if model in remote_models:
                _CACHED_AVAILABLE_MODEL = model
                return model
        for m_id in remote_models:
            if "gpt-oss" in m_id or "qwen" in m_id:
                _CACHED_AVAILABLE_MODEL = m_id
                return m_id
    except Exception:
        pass
        
    _CACHED_AVAILABLE_MODEL = "openai/gpt-oss-120b"
    return _CACHED_AVAILABLE_MODEL


def build_schema_prompt(table_name, schema):
    cols = [f"- {item['column']} ({item['type']})" for item in schema if item['column'] != '_id']
    schema_str = "\n".join(cols)
    return f"Table Name: `{table_name}`\nColumns:\n{schema_str}"


def validate_sql(query):
    """
    Validates a SQL query using sqlglot AST parsing (MySQL dialect).
    Enforces:
      1. Single statement only
      2. Root statement must be a read-only SELECT (or CTE / WITH ... SELECT)
      3. Prohibits DDL/DML (DROP, INSERT, UPDATE, DELETE, ALTER, etc.)
      4. Blocks dangerous functions (SLEEP, BENCHMARK, LOAD_FILE, etc.)
      5. Blocks file system export clauses (INTO OUTFILE / DUMPFILE)
      6. Enforces/caps LIMIT <= 1000
    Returns:
      (is_valid: bool, cleaned_sql_or_error: str)
    """
    if not query or not query.strip():
        return False, "Empty query received."
        
    clean = query.strip()
    
    # Extract from markdown block if LLM returned fenced code
    md_match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
    if md_match:
        clean = md_match.group(1).strip()
        
    # Strip any accidental preamble (e.g., "Here is your query: SELECT ...")
    select_match = re.search(r"\b(SELECT|WITH)\b[\s\S]*", clean, re.IGNORECASE)
    if select_match:
        clean = select_match.group(0).strip()
        
    # Remove trailing semicolon
    clean = clean.rstrip(";").strip()
    
    # Fast pre-check for MySQL-specific file exfiltration clauses
    if re.search(r"\bINTO\s+(OUTFILE|DUMPFILE)\b", clean, re.IGNORECASE):
        return False, "Forbidden file export clause detected (INTO OUTFILE/DUMPFILE)."
    
    # 1. Parse AST with sqlglot using MySQL dialect
    try:
        statements = sqlglot.parse(clean, read="mysql")
    except Exception as e:
        return False, f"SQL Syntax Error: {e}"
        
    if not statements:
        return False, "Could not parse SQL statement."
    if len(statements) > 1:
        return False, "Query contains multiple statements. Only single queries are allowed."
        
    ast = statements[0]
    if ast is None:
        return False, "Invalid SQL statement structure."
        
    # 2. Must be a Select or Union expression (CTE 'WITH ... SELECT' is represented as Select in sqlglot)
    if not isinstance(ast, (exp.Select, exp.Union)):
        return False, "Only read-only SELECT queries are permitted."
        
    # 3. Check for any forbidden DDL / DML nodes inside the AST
    forbidden_types = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
        exp.Alter, exp.Command, exp.Transaction, exp.Commit, exp.Rollback
    )
    for node in ast.walk():
        if isinstance(node, forbidden_types):
            return False, f"Forbidden statement type detected: {node.key.upper()}"
            
    # 4. Check for file export (INTO OUTFILE / INTO DUMPFILE)
    if ast.find(exp.Into):
        return False, "Forbidden file export clause detected (INTO OUTFILE/DUMPFILE)."
        
    # 5. Check for dangerous functions (SLEEP, BENCHMARK, LOAD_FILE, etc.)
    for func in ast.find_all(exp.Anonymous, exp.Func):
        func_name = (func.name or "").lower()
        if not func_name and hasattr(func, "this"):
            func_name = str(func.this).lower()
        if func_name in DANGEROUS_FUNCTIONS:
            return False, f"Forbidden dangerous function detected: {func_name.upper()}()"
            
    # 6. Enforce LIMIT <= 1000 (cap existing limit if > 1000, or append LIMIT 1000)
    limit_node = ast.find(exp.Limit)
    if limit_node and limit_node.expression:
        try:
            curr_limit = int(str(limit_node.expression))
            if curr_limit > 1000:
                limit_node.set("expression", exp.Literal.number(1000))
        except (ValueError, TypeError):
            limit_node.set("expression", exp.Literal.number(1000))
    else:
        ast = ast.limit(1000)
        
    final_sql = ast.sql(dialect="mysql")
    return True, final_sql


def generate_sql(table_name, schema, user_question, model=None):
    """
    Translates user question into valid MySQL SELECT query via Groq.
    Returns:
      (sql: str | None, error: str | None, is_fallback: bool)
    """
    try:
        client = get_groq_client()
    except Exception as e:
        return None, str(e), False
        
    if not model:
        model = get_available_model(client)
        
    schema_text = build_schema_prompt(table_name, schema)
    
    system_prompt = (
        "You are an expert MySQL database analyst.\n"
        "Your sole task is to convert any user request, question, or overview prompt into a valid MySQL 8.0 SELECT statement.\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY the raw SQL query. Absolutely NO conversational disclaimers, NO markdown code fences, and NO apologies.\n"
        f"2. If the user asks for an overview, summary, or generic exploration, write: SELECT * FROM `{table_name}` LIMIT 25\n"
        "3. ONLY output SELECT statements. Never write DROP, DELETE, UPDATE, INSERT, or ALTER.\n"
        "4. Wrap all table and column names in backticks (`).\n"
        "5. Do NOT include a semicolon at the end."
    )
    
    user_prompt = (
        f"Database Schema:\n{schema_text}\n\n"
        f"User Prompt: \"{user_question}\"\n\n"
        f"Generate the exact MySQL SELECT statement:"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=250
        )
        
        raw_sql = response.choices[0].message.content.strip()
        is_valid, final_sql_or_err = validate_sql(raw_sql)
        
        # Self-healing fallback: If LLM apologized or hallucinated invalid non-SELECT output,
        # fallback seamlessly to a clean overview query with is_fallback=True
        if not is_valid:
            fallback_sql = f"SELECT * FROM `{table_name}` LIMIT 25"
            return fallback_sql, None, True
            
        return final_sql_or_err, None, False
        
    except Exception as e:
        return None, f"Groq API Error: {e}", False


def summarize_results(user_question, df, model=None, send_sample=False):
    """
    Synthesizes a conversational plain-English takeaway explaining query results.
    
    Privacy Model:
      - If send_sample=False (Default): Transmits ONLY column headers, row counts, and
        summary statistical aggregates (Min, Mean, Max). Zero raw data rows leave local MySQL!
      - If send_sample=True (Opt-in via Settings): Transmits a small sample preview
        (up to 8 rows x 10 cols) for granular qualitative context.
    """
    if df is None or df.empty:
        return "No records were found matching this criteria in the database."
        
    try:
        client = get_groq_client()
    except Exception as e:
        return f"Could not generate text summary: {e}"
        
    if not model:
        model = get_available_model(client)
        
    total_rows = len(df)
    
    if send_sample:
        clean_sample = df.head(8).fillna('-')
        if len(clean_sample.columns) > 10:
            clean_sample = clean_sample.iloc[:, :10]
        data_context = f"Data Sample (First {len(clean_sample)} rows):\n{clean_sample.to_string(index=False)}"
    else:
        # Privacy-Preserving Mode: Send only statistical summaries
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != '_id']
        agg_lines = []
        for col in numeric_cols[:8]:
            s = df[col].dropna()
            if not s.empty:
                agg_lines.append(f"- {col}: Min = {s.min():.2f}, Mean = {s.mean():.2f}, Max = {s.max():.2f}")
                
        col_list = [c for c in df.columns if c != '_id'][:12]
        col_summary = f"Columns Available: {', '.join(col_list)}"
        if agg_lines:
            agg_summary = "Aggregate Statistical Summary (No raw data rows transmitted):\n" + "\n".join(agg_lines)
        else:
            agg_summary = f"Distinct Categories / Records: {total_rows} matching rows."
            
        data_context = f"{col_summary}\n{agg_summary}"
    
    system_prompt = (
        "You are a friendly, expert Senior Data Analyst & Educator.\n"
        "Review the user's question and the returned result summary, then write a helpful, conversational "
        "2-to-4 sentence plain-English explanation.\n"
        "Explain what the patterns and numbers mean, and what actionable takeaways the user can learn from this."
    )
    
    user_prompt = (
        f"User Question: \"{user_question}\"\n"
        f"Total Records: {total_rows}\n"
        f"{data_context}\n\n"
        f"Provide the plain-English takeaway:"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Summary generation error: {e})"
