import threading

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import QObject, Signal, QTimer

from downloader.download import download_video, get_video_info
from settings import load_settings, save_settings
from history import add_history_entry
from ui.history_window import HistoryWindow


# ---------------- Signals ----------------
class ProgressSignals(QObject):
    progress = Signal(float)
    status = Signal(str)
    error = Signal(str)


# ---------------- Main Window ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Downloader")
        self.resize(500, 300)

        self.settings = load_settings()
        self.download_path = self.settings.get("download_path", "downloads")

        self.signals = ProgressSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.status.connect(self.update_status)
        self.signals.error.connect(self.show_error)

        layout = QVBoxLayout()

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here")
        layout.addWidget(self.url_input)

        # Title label
        self.title_label = QLabel("Video: -")
        layout.addWidget(self.title_label)

        # Format selector
        self.format_box = QComboBox()
        self.format_box.addItems(["mp4", "mkv", "mp3"])
        layout.addWidget(self.format_box)

        # Folder selection
        self.folder_btn = QPushButton("Choose Download Folder")
        layout.addWidget(self.folder_btn)

        # History button
        self.history_btn = QPushButton("History")
        layout.addWidget(self.history_btn)

        # Download button
        self.download_btn = QPushButton("Download")
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # Connections
        self.download_btn.clicked.connect(self.start_download)
        self.folder_btn.clicked.connect(self.choose_folder)
        self.history_btn.clicked.connect(self.show_history)

        # Auto info fetch timer
        self.info_timer = QTimer()
        self.info_timer.setSingleShot(True)
        self.info_timer.timeout.connect(self.fetch_video_info)

        self.url_input.textChanged.connect(self.schedule_info_fetch)

    # ---------------- Folder selection ----------------
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")

        if folder:
            self.download_path = folder
            self.settings["download_path"] = folder
            save_settings(self.settings)

    # ---------------- History ----------------
    def show_history(self):
        self.history_window = HistoryWindow()
        self.history_window.show()

    # ---------------- Progress updates ----------------
    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def update_status(self, text):
        self.status_label.setText(text)

    # ---------------- Error popup ----------------
    def show_error(self, message):
        QMessageBox.critical(self, "Download Error", message)

    # ---------------- Auto info fetch ----------------
    def schedule_info_fetch(self):
        text = self.url_input.text().strip()

        if "youtube.com" not in text and "youtu.be" not in text:
            self.title_label.setText("Video: -")
            return

        if not self.download_btn.isEnabled():
            return

        self.title_label.setText("Fetching info...")
        self.info_timer.start(600)

    # ---------------- Fetch metadata ----------------
    def fetch_video_info(self):
        url = self.url_input.text().strip()

        if not url:
            return

        def run():
            try:
                info = get_video_info(url)

                if info.get("_type") == "playlist":
                    entries = info.get("entries") or []
                    entries = list(entries)

                    count = len(entries)
                    title = info.get("title", "Playlist")

                    self.title_label.setText(
                        f"Playlist: {title} ({count} videos)"
                    )
                else:
                    title = info.get("title", "Unknown title")
                    self.title_label.setText(f"Video: {title}")

            except Exception:
                self.title_label.setText("Could not fetch info")

        threading.Thread(target=run, daemon=True).start()

    # ---------------- Download ----------------
    def start_download(self):
        url = self.url_input.text().strip()
        fmt = self.format_box.currentText()

        if not url:
            return

        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.signals.status.emit("Downloading...")

        def run():
            try:
                download_video(
                    url,
                    self.download_path,
                    fmt,
                    progress_callback=self.signals.progress.emit,
                    status_callback=self.signals.status.emit,
                )

                info = get_video_info(url)
                title = info.get("title", "Unknown")

                add_history_entry(
                    title,
                    url,
                    fmt,
                    self.download_path,
                )

                self.signals.status.emit("Download complete")

            except Exception as e:
                self.signals.status.emit("Download failed")
                self.signals.error.emit(str(e))

            finally:
                self.download_btn.setEnabled(True)

        threading.Thread(target=run, daemon=True).start()
