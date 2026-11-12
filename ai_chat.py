"""
ai_chat.py — Groq AI Integration (Text-to-SQL + Natural Language Summaries)
=============================================================================
Handles:
  1. Sending table schema + user's question to Groq -> returns safe SQL query.
  2. (Optional) Taking SQL query execution results -> generates a concise,
     plain-English text explanation/insight.
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_groq_client():
    """Initialize Groq client using API key from .env."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set or still default in .env file.\n"
            "Get your free key from https://console.groq.com and paste it in E:\\ai_data_analyst\\.env"
        )
    return Groq(api_key=api_key)


def get_available_model(client):
    """
    Dynamically pick the best text-to-SQL model available on user's Groq tier.
    Falls back gracefully across preferred open-source models.
    """
    preferred = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile"
    ]
    try:
        remote_models = {m.id for m in client.models.list().data}
        for model in preferred:
            if model in remote_models:
                return model
        for m_id in remote_models:
            if "gpt-oss" in m_id or "qwen" in m_id:
                return m_id
    except Exception:
        pass
    return "openai/gpt-oss-120b"


def build_schema_prompt(table_name, schema):
    """Format table schema into a readable text block for LLM prompt."""
    cols = [f"- {item['column']} ({item['type']})" for item in schema if item['column'] != '_id']
    schema_str = "\n".join(cols)
    return f"Table Name: `{table_name}`\nColumns:\n{schema_str}"


def validate_sql(query):
    """
    Strict safety check on generated SQL.
    Rules:
      1. Must start with SELECT or WITH.
      2. No destructive keywords (DROP, DELETE, UPDATE, etc.).
      3. No multiple chained queries (no semicolon injection).
    """
    clean = query.strip()
    clean = re.sub(r"^```(?:sql)?\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean)
    clean = clean.strip()
    
    if clean.endswith(";"):
        clean = clean[:-1].strip()
        
    if ";" in clean:
        return False, "Query contains multiple statements. Only single queries are allowed."
        
    upper_query = clean.upper()
    if not (upper_query.startswith("SELECT") or upper_query.startswith("WITH")):
        return False, "Only read-only SELECT queries are permitted."
        
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "REPLACE", "CREATE", "GRANT", "REVOKE"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", upper_query):
            return False, f"Forbidden statement keyword detected: {word}"
            
    return True, clean


def generate_sql(table_name, schema, user_question, model=None):
    """Call Groq API to convert English question into safe SQL query."""
    try:
        client = get_groq_client()
    except Exception as e:
        return None, str(e)
        
    if not model:
        model = get_available_model(client)
        
    schema_text = build_schema_prompt(table_name, schema)
    
    system_prompt = (
        "You are an expert MySQL database analyst.\n"
        "Your job is to convert natural language questions into valid, optimized MySQL 8.0 SELECT queries.\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY the raw SQL query. No explanations, no markdown formatting, no code fences (do NOT use ```sql).\n"
        "2. ONLY write SELECT statements. Never write INSERT, UPDATE, DELETE, DROP, or ALTER.\n"
        "3. Wrap all table and column names in backticks (`).\n"
        "4. Rely strictly on the columns provided in the schema.\n"
        "5. If calculating aggregations (e.g. SUM, AVG), give aliases with `AS`.\n"
        "6. Do not include semicolons at the end."
    )
    
    user_prompt = (
        f"Database Schema:\n{schema_text}\n\n"
        f"User Question: {user_question}\n\n"
        f"Provide the exact MySQL SELECT statement:"
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        raw_sql = response.choices[0].message.content.strip()
        is_valid, final_sql_or_err = validate_sql(raw_sql)
        
        if not is_valid:
            return None, f"Security Validation Failed: {final_sql_or_err}"
            
        return final_sql_or_err, None
        
    except Exception as e:
        return None, f"Groq API Error: {e}"


def summarize_results(user_question, df, model=None):
    """
    Generate a concise plain-English natural language summary from the query results.
    
    Parameters:
        user_question (str): The user's original query
        df (pd.DataFrame): The returned results from MySQL
        model (str, optional): Groq model
        
    Returns:
        str: Plain English insight or summary
    """
    if df is None or df.empty:
        return "No records were found matching this criteria in the database."
        
    try:
        client = get_groq_client()
    except Exception as e:
        return f"Could not generate text summary: {e}"
        
    if not model:
        model = get_available_model(client)
        
    # Take at most top 10 rows to keep tokens minimal and fast
    sample_data = df.head(10).to_string(index=False)
    total_rows = len(df)
    
    system_prompt = (
        "You are a helpful Senior Data Analyst assistant.\n"
        "Given the user's question and the tabular data results returned from the database, "
        "provide a friendly, direct, concise plain-English explanation (2 to 4 sentences).\n"
        "Highlight the key insights, figures, or takeaways clearly without repeating raw table dumps."
    )
    
    user_prompt = (
        f"User Question: \"{user_question}\"\n"
        f"Total Rows Returned: {total_rows}\n"
        f"Data Preview:\n{sample_data}\n\n"
        f"Provide the concise plain-English summary:"
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
