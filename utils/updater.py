import subprocess
import threading
import sys
import os
import time

def update_ytdlp():
    time.sleep(80)  # Delay to allow the main application to start
    try:
        base_dir = os.path.dirname(sys.executable)
        ytdlp_path = os.path.join(base_dir, "yt-dlp.exe")

        subprocess.Popen(
            [ytdlp_path, "-U"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    except Exception:
        pass


def start_updater():
    threading.Thread(target=update_ytdlp, daemon=True).start()