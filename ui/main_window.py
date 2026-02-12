import urllib.request
import tempfile
import threading

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QComboBox,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QListWidget,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QObject, Signal, QTimer

from downloader.download import download_video, get_video_info
from downloader.queue_manager import DownloadQueueManager
from settings import load_settings, save_settings
from history import add_history_entry
from ui.history_window import HistoryWindow
from ui.theme import DARK_THEME


# ---------------- Signals ----------------
class ProgressSignals(QObject):
    progress = Signal(float)
    status = Signal(str)
    error = Signal(str)
    thumbnail = Signal(QPixmap)

# ---------------- Main Window ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yui - Video Downloader")
        self.resize(1600, 900)

        # ----- settings -----
        self.settings = load_settings()
        self.download_path = self.settings.get("download_path", "downloads")

        # ----- signals -----
        self.signals = ProgressSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.status.connect(self.update_status)
        self.signals.error.connect(self.show_error)

        # ----- background -----
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        pixmap = QPixmap("assets/bg.jpg")
        self.bg_label.setPixmap(pixmap)
        
        # ----- panel -----
        self.panel = QWidget(self)

        # panel background only
        self.panel.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 190);
                border-radius: 12px;
            }
        """)

        # load theme file
        with open("ui/themes/dark.qss", "r") as f:
            self.panel.setStyleSheet(
                self.panel.styleSheet() + f.read()
            )

        # ----- Root layout -----
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addStretch()
        root_layout.addWidget(self.panel)
        root_layout.addSpacing(40)

        # ----- layout on panel -----
        layout = QVBoxLayout(self.panel)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here")
        layout.addWidget(self.url_input)

        # ----- Title label -----
        self.title_label = QLabel("Video: -")

        # ----- Thumbnail -----
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)

        preview_layout = QHBoxLayout()
        preview_layout.addWidget(self.thumbnail_label)
        preview_layout.addWidget(self.title_label)

        layout.addLayout(preview_layout)

        self.signals.thumbnail.connect(self.thumbnail_label.setPixmap)

        # ----- Queue List -----
        self.queue_list = QListWidget()
        layout.addWidget(self.queue_list, stretch=1)

        # ----- Queue Manager -----
        self.queue_manager = DownloadQueueManager(
            self.signals,
            self.update_queue_ui
        )

        # ----- Format selector -----
        self.format_box = QComboBox()
        self.format_box.addItems(["mp4", "mkv", "mp3"])
        layout.addWidget(self.format_box)

        # ----- Folder + History buttons -----
        buttons_layout = QHBoxLayout()

        self.folder_btn = QPushButton("Choose Download Folder")
        buttons_layout.addWidget(self.folder_btn)

        self.history_btn = QPushButton("History")
        buttons_layout.addWidget(self.history_btn)

        layout.addLayout(buttons_layout)

        # Download button
        self.download_btn = QPushButton("Download")
        layout.addWidget(self.download_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

        # Connections
        self.download_btn.clicked.connect(self.start_download)
        self.folder_btn.clicked.connect(self.choose_folder)
        self.history_btn.clicked.connect(self.show_history)

        # Auto info fetch timer
        self.info_timer = QTimer()
        self.info_timer.setSingleShot(True)
        self.info_timer.timeout.connect(self.fetch_video_info)

        self.url_input.textChanged.connect(self.schedule_info_fetch)

    # ---------------- Resize background ----------------
    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

    # ---------------- Update queue UI ----------------
    def update_queue_ui(self, status, title):
        if status == "Queued":
            self.queue_list.addItem(f"Queued: {title}")

        elif status == "Starting":
            self.queue_list.addItem(f"Downloading: {title}")
    
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

    # ---------------- Download finished callback ----------------
    def on_video_finished(self, title, playlist, index):
        url = self.url_input.text().strip()
        fmt = self.format_box.currentText()

        if playlist:
            display_title = f"{playlist} → {title}"
        else:
            display_title = title

        add_history_entry(
            display_title,
            url,
            fmt,
            self.download_path,
        )

    # ---------------- Error popup ----------------
    def show_error(self, message):
        QMessageBox.critical(self, "Download Error", message)

    # ---------------- Auto info fetch ----------------
    def schedule_info_fetch(self):
        text = self.url_input.text().strip()

        if "youtube.com" not in text and "youtu.be" not in text:
            self.title_label.setText("Video: -")
            self.thumbnail_label.clear()
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
                thumb_url = info.get("thumbnail")

                if thumb_url:
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    urllib.request.urlretrieve(thumb_url, tmp_file.name)

                    pixmap = QPixmap(tmp_file.name)

                    if not pixmap.isNull():
                        scaled = pixmap.scaled(
                            320, 180,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )

                        self.signals.thumbnail.emit(scaled)

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
                self.queue_manager.add(
                    url, self.download_path, fmt
                    )    

                self.signals.status.emit("Download complete")

            except Exception as e:
                self.signals.status.emit("Download failed")
                self.signals.error.emit(str(e))

            finally:
                self.download_btn.setEnabled(True)

        threading.Thread(target=run, daemon=True).start()
