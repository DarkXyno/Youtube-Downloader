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
    QListWidgetItem,
    QTreeView,
    QFileSystemModel,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QObject, Signal, QTimer

from downloader.download import download_video, get_video_info
from downloader.queue_manager import DownloadQueueManager
from settings import load_settings, save_settings
from history import add_history_entry
from ui.history_window import HistoryWindow
from ui.theme import DARK_THEME
from ui.queue_item import QueueItemWidget
from history import load_history


# ---------------- Signals ----------------
class ProgressSignals(QObject):
    progress = Signal(str, float)
    status = Signal(str)
    error = Signal(str)
    thumbnail = Signal(QPixmap)
    queue_update = Signal(str, str) # status, title

# ---------------- Main Window ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yui - Video Downloader")
        self.setFixedSize(1600, 900)

        # ----- Toolbar (geometry-based) -----
        self.toolbar = QWidget(self)
        self.toolbar.setGeometry(0, 0, 800, 40)

        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        # Toolbar background
        self.toolbar.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 200);
                border-radius: 12px;
            }

            QPushButton {
                color: #ddd;
                background: transparent;
                border: none;
                padding: 6px 12px;
            }

            QPushButton:hover {
                background: rgba(255, 255, 255, 40);
                border-radius: 6px;
            }
            """)

        self.toggle_files_btn = QPushButton("Downloads")
        toolbar_layout.addWidget(self.toggle_files_btn)
        self.toggle_files_btn.clicked.connect(self.show_downloads)

        self.history_btn = QPushButton("History")
        toolbar_layout.addWidget(self.history_btn)
        self.history_btn.clicked.connect(self.show_history_panel)

        self.change_bg_btn = QPushButton("Change Background")
        toolbar_layout.addWidget(self.change_bg_btn)
        self.change_bg_btn.clicked.connect(self.change_background)

        toolbar_layout.addStretch()

        # Toggle file panel visibility
        self.toggle_files_btn.clicked.connect(
            self.show_downloads
        )

        # Settings
        self.settings = load_settings()
        self.download_path = self.settings.get("download_path", "downloads")

        # Signals
        self.signals = ProgressSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.status.connect(self.update_status)
        self.signals.error.connect(self.show_error)
        self.signals.queue_update.connect(self.update_queue_ui)

        # Backgroud
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        bg_path = self.settings.get("background", "assets/bg.jpg")
        pixmap = QPixmap(bg_path)
        self.bg_label.setPixmap(pixmap)
        
        # Download folder view 
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(
            self.file_model.index(self.download_path)
        )
        self.file_view.setMaximumWidth(400)

        # ----- panel -----
        self.panel = QWidget(self)

        # panel background only
        self.panel.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 190);
                border-radius: 12px;
            }
        """)

        # file panel
        self.file_panel = QWidget(self)

        self.file_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 25, 190);
                border-radius: 12px;}
            """)
        
        with open("ui/themes/dark.qss", "r") as f:
            self.file_panel.setStyleSheet(
                self.file_panel.styleSheet() + f.read()
            )

        # load theme file
        with open("ui/themes/dark.qss", "r") as f:
            self.panel.setStyleSheet(
                self.panel.styleSheet() + f.read()
            )

        # ----- layout on panel -----
        layout = QVBoxLayout(self.panel)

        # layout on file panel
        file_layout = QVBoxLayout(self.file_panel)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")

        self.file_view = QTreeView()
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(
            self.file_model.index(self.download_path)
        )

        file_layout.addWidget(self.file_view)

        self.panel.setGeometry(800, 0, 800, 900)
        self.file_panel.setGeometry(80, 80, 600, 700)

        self.history_list = QListWidget()
        file_layout.addWidget(self.history_list)
        self.history_list.hide()

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
        self.queue_widgets = {}

        # ----- Queue Manager -----
        self.queue_manager = DownloadQueueManager(self.signals)

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

    # ---------------- Change background ----------------
    def change_background(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select background", 
            "",
            "Images (*.png *.jpg *.jpeg *.JPG *.JPEG *.PNG);;All Files (*)"
        )

        if file:
            self.settings["background"] = file
            save_settings(self.settings)

            pixmap = QPixmap(file)
            self.bg_label.setPixmap(pixmap)

    # ---------------- Update queue UI ----------------
    def update_queue_ui(self, status, title):
        if status == "Queued":
            widget = QueueItemWidget(title)

            item = QListWidgetItem(self.queue_list)
            item.setSizeHint(widget.sizeHint())

            self.queue_list.addItem(item)
            self.queue_list.setItemWidget(item, widget)

            self.queue_widgets[title] = widget

        elif status == "Starting":
            widget = self.queue_widgets.get(title)
            if widget:
                widget.set_status(f"Downloading: {title}")
    
    # ---------------- Folder selection ----------------
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")

        if folder:
            self.download_path = folder
            self.settings["download_path"] = folder
            save_settings(self.settings)

            self.file_view.setRootIndex(self.file_model.index(folder))

    # ---------------- History ----------------
    def show_history(self):
        self.history_window = HistoryWindow()
        self.history_window.show()

    # Show downloads
    def show_downloads(self):
        self.file_view.show()
        self.history_list.hide()
        self._highlight_toolbar(self.toggle_files_btn)

    def show_history_panel(self):
        self.file_view.hide()
        self.history_list.show()
        self.populate_history()
        self._highlight_toolbar(self.history_btn)

    def _highlight_toolbar(self, active_btn):
        for btn in [self.toggle_files_btn, self.history_btn]:
            btn.setStyleSheet("")

        active_btn.setStyleSheet("""
            QPushButton {
                    background: rgba(255, 255, 255, 60);
                    border-radius: 6px;
            }
        """)

    def populate_history(self):
        self.history_list.clear()

        history = load_history()
        for item in history:
            text = f"{item['title']} ({item['format']})"
            self.history_list.addItem(text)

    # ---------------- Progress updates ----------------
    def update_progress(self, title, value):
        widget = self.queue_widgets.get(title)

        if widget:
            widget.set_progress(value)

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
        self.info_timer.start(200)

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
