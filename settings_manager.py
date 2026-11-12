"""
settings_manager.py — Application Settings & Preferences Manager
==================================================================
Persists user configuration in `settings.json`:
  - ai_teacher_mode (bool): Whether AI delivers conversational educational takeaways
  - auto_chart_enabled (bool): Whether automated chart visualization renders
  - selected_model (str): Current Groq inference model
"""

import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "ai_teacher_mode": True,
    "auto_chart_enabled": True,
    "theme": "dark"
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"[SETTINGS ERROR] Could not save settings: {e}")


def get_setting(key, default=None):
    s = load_settings()
    return s.get(key, default)


def set_setting(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)
    return s
