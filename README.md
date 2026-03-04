# Yui - Video Downloader

A desktop video downloader built with `PySide6` + `yt-dlp`.

Yui is focused on a clean workflow:
- Paste URL
- Pick format (`mp4`, `mkv`, `mp3`)
- Download with queue + progress tracking
- Review logs and history in-app

## Features

- Modern desktop UI (PySide6)
- URL metadata preview (title + thumbnail)
- Queue-based downloads
- Format options: `mp4`, `mkv`, `mp3`
- Download history panel
- Local file browser panel for downloads
- Built-in log console panel
- Startup yt-dlp version check + auto-update attempt for bundled binary

## Tech Stack

- Python 3.10+
- PySide6
- yt-dlp
- FFmpeg (required for best compatibility and `mp3` extraction)

## Project Structure

```text
Video Downloader/
  main.py
  downloader/
    download.py
    queue_manager.py
  ui/
    main_window.py
    log_console.py
    history_window.py
    queue_item.py
    themes/
      dark.qss
  utils/
    logger.py
    updater.py
  history.py
  settings.py
  assets/
    Yui.ico
```

## Setup (Local Dev)

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install PySide6 yt-dlp
```

3. Install FFmpeg and ensure it is available on `PATH`.
4. Run:

```bash
python main.py
```

## Optional Files

- `cookies.txt` (project root): used by yt-dlp for authenticated/age-restricted content in your current download config.

If you don't need cookies, you can remove or adjust `cookiefile` usage in `downloader/download.py`.

## Packaging Notes

- A PyInstaller spec already exists: `main.spec`.
- App data currently includes:
  - `history.json`
  - `config.json`
  - optional logs (for example `yui.log`, depending on your logging setup)

## Logging + Updater Behavior

At app startup, Yui:
- Initializes the in-app log console
- Checks yt-dlp version
- Checks latest release
- Updates local `yt-dlp.exe` (for bundled app flow) when needed

Typical startup logs:

```text
[INFO] Log console initialized.
[INFO] Checking for yt-dlp updates...
[INFO] yt-dlp current version: <version>
[INFO] yt-dlp already up to date.
```

or

```text
[INFO] yt-dlp updated successfully: <version>
```

## Troubleshooting

- `mp3` conversion not working:
  - Verify FFmpeg is installed and on `PATH`.

- Some URLs fail to fetch/download:
  - Ensure yt-dlp is updated.
  - Add/refresh `cookies.txt` if the source requires authentication.

- UI starts but no logs show:
  - Confirm `utils/logger.py` handler is connected in `ui/main_window.py`.

## Roadmap Ideas

- Add `requirements.txt` or `pyproject.toml`
- Add per-download cancel/retry controls
- Add settings UI (instead of config-only)
- Add release artifacts + installer

---

Built with Python and stubborn debugging sessions.
