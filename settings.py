import json
from pathlib import Path

CONFIG_FILE = Path("config.json")


# -------------------------------
# Load settings
# -------------------------------
def load_settings():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# -------------------------------
# Save settings
# -------------------------------
def save_settings(settings):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)
