import os
import sys
import json
from pathlib import Path
from datetime import datetime

HISTORY_FILE = Path("history.json")

# 
def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = Path(app_dir()) / "history.json"


# -------------------------------
# Load history
# -------------------------------
def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# -------------------------------
# Save history
# -------------------------------
def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)


# -------------------------------
# Add entry
# -------------------------------
def add_history_entry(title, url, fmt, folder):
    history = load_history()

    entry = {
        "title": title,
        "url": url,
        "format": fmt,
        "folder": folder,
        # unified timestamp field
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # newest first
    history.insert(0, entry)

    save_history(history)
