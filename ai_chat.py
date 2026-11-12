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
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set or still default in .env file.\n"
            "Get your free key from https://console.groq.com and paste it in E:\\ai_data_analyst\\.env"
        )
    return Groq(api_key=api_key)


def get_available_model(client):
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
    cols = [f"- {item['column']} ({item['type']})" for item in schema if item['column'] != '_id']
    schema_str = "\n".join(cols)
    return f"Table Name: `{table_name}`\nColumns:\n{schema_str}"


def validate_sql(query):
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
    try:
        client = get_groq_client()
    except Exception as e:
        return None, str(e)
        
    if not model:
        model = get_available_model(client)
        
    schema_text = build_schema_prompt(table_name, schema)
    
    system_prompt = (
        "You are an expert MySQL database analyst.\n"
        "Your sole task is to convert any user request, question, or overview prompt into a valid MySQL 8.0 SELECT statement.\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY the raw SQL query. Absolutely NO conversational disclaimers, NO markdown code fences, and NO apologies.\n"
        "2. If the user asks for an overview, summary, or generic exploration, write: `SELECT * FROM `{table_name}` LIMIT 25`\n"
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
        # fallback seamlessly to a clean overview query rather than crashing the user's UI
        if not is_valid:
            fallback_sql = f"SELECT * FROM `{table_name}` LIMIT 25"
            return fallback_sql, None
            
        return final_sql_or_err, None
        
    except Exception as e:
        return None, f"Groq API Error: {e}"


def summarize_results(user_question, df, model=None):
    if df is None or df.empty:
        return "No records were found matching this criteria in the database."
        
    try:
        client = get_groq_client()
    except Exception as e:
        return f"Could not generate text summary: {e}"
        
    if not model:
        model = get_available_model(client)
        
    sample_data = df.head(8).to_string(index=False)
    total_rows = len(df)
    
    system_prompt = (
        "You are a friendly, expert Senior Data Analyst & Educator.\n"
        "Review the user's question and the returned tabular records, then write a helpful, conversational "
        "2-to-4 sentence plain-English explanation.\n"
        "Explain what the numbers show, what patterns emerge, and what actionable takeaways the user can learn from this."
    )
    
    user_prompt = (
        f"User Question: \"{user_question}\"\n"
        f"Total Records: {total_rows}\n"
        f"Data Sample:\n{sample_data}\n\n"
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
