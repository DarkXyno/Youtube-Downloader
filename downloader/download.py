import yt_dlp
from pathlib import Path


# -------------------------------
# Fetch metadata only
# -------------------------------
def get_video_info(url):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": False,
        "noplaylist": False,
        "cookiefile": "cookies.txt",
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return info


# -------------------------------
# Download logic
# -------------------------------
def download_video(
    url,
    output_path="downloads",
    format_type="mp4",
    progress_callback=None,
    status_callback=None,
):
    Path(output_path).mkdir(exist_ok=True)

    def hook(d):
        # Progress %
        if progress_callback and d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)

            if total:
                progress = downloaded / total * 100
                progress_callback(progress)

        # Playlist progress
        if d.get("status") == "downloading":
            index = d.get("playlist_index")
            total_entries = d.get("n_entries")

            if index and total_entries and status_callback:
                status_callback(
                    f"Downloading video {index} / {total_entries}"
                )

        if progress_callback and d["status"] == "finished":
            progress_callback(100)

    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "progress_hooks": [hook],
        "noplaylist": False,
        "cookiefile": "cookies.txt",
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
    }

    # ---------------- Format selection ----------------
    if format_type == "mp4":
        ydl_opts["format"] = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "best[ext=mp4]/best"
        )
        ydl_opts["merge_output_format"] = "mp4"

    elif format_type == "mkv":
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mkv"

    elif format_type == "mp3":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    # ---------------- Download ----------------
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
