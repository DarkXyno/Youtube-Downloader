import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import json


YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_LATEST_API_URL = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"


def _run_command(cmd):
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        creationflags=creation_flags,
    )


def _resolve_ytdlp_command():
    base_dir = os.path.dirname(sys.executable)
    local_exe = os.path.join(base_dir, "yt-dlp.exe")

    if os.path.exists(local_exe):
        return [local_exe]

    which_path = shutil.which("yt-dlp")
    if which_path:
        return [which_path]

    # Fallback for Python installs where yt-dlp is available as a module.
    return [sys.executable, "-m", "yt_dlp"]


def _resolve_local_ytdlp_exe_path():
    base_dir = os.path.dirname(sys.executable)
    local_exe = os.path.join(base_dir, "yt-dlp.exe")
    return local_exe


def _get_local_version(base_cmd):
    result = _run_command(base_cmd + ["--version"])
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def _get_latest_version():
    request = urllib.request.Request(
        YTDLP_LATEST_API_URL,
        headers={"User-Agent": "Yui-Video-Downloader-Updater"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    # GitHub returns tag names like "2025.01.15" (or sometimes prefixed).
    return str(data.get("tag_name", "")).lstrip("v").strip() or None


def _download_file(url, destination):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Yui-Video-Downloader-Updater"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, open(destination, "wb") as f:
        f.write(response.read())


def update_ytdlp():
    logger = logging.getLogger(__name__)
    logger.info("Checking for yt-dlp updates...")

    try:
        base_cmd = _resolve_ytdlp_command()
        local_version = _get_local_version(base_cmd)
        logger.info(f"yt-dlp current version: {local_version or 'unknown'}")

        latest_version = _get_latest_version()
        if not latest_version:
            logger.warning("Could not determine latest yt-dlp version.")
            return

        if local_version and local_version.strip() == latest_version.strip():
            logger.info("yt-dlp already up to date.")
            return

        ytdlp_exe_path = _resolve_local_ytdlp_exe_path()
        download_dir = os.path.dirname(ytdlp_exe_path)
        os.makedirs(download_dir, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(prefix="yt-dlp_", suffix=".exe", dir=download_dir)
        os.close(fd)

        try:
            _download_file(YTDLP_DOWNLOAD_URL, temp_path)
            os.replace(temp_path, ytdlp_exe_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Re-check version after replacement.
        updated_cmd = [ytdlp_exe_path]
        updated_version = _get_local_version(updated_cmd) or latest_version
        logger.info(f"yt-dlp updated successfully: {updated_version}")
    except FileNotFoundError:
        logger.error("yt-dlp not found for auto-update.")
    except Exception as e:
        logger.error(f"yt-dlp auto-update error: {e}")


def start_updater():
    threading.Thread(target=update_ytdlp, daemon=True).start()
