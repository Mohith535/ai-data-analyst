"""
history_manager.py — Analytics Query & Chat History Manager
=============================================================
Persists user queries, generated SQL, AI insights, and timestamps
into a local JSON datastore (`history.json`) for instant session recall.
"""

import os
import json
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "history.json")


def load_history():
    """Load query history list from disk."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history_item(table, question, sql, insight):
    """Append a query session entry to history."""
    history = load_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "table": str(table),
        "question": str(question),
        "sql": str(sql),
        "insight": str(insight)
    }
    # Prepend to keep latest on top (max 50 entries)
    history.insert(0, entry)
    history = history[:50]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[HISTORY ERROR] Could not save history: {e}")
    return history


def clear_history():
    """Clear all saved history."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception:
        pass
