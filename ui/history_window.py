from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget
from history import load_history


class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Download History")
        self.resize(500, 400)

        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        self.populate()

    def populate(self):
        history = load_history()

        self.list_widget.clear()

        for item in history:
            time = (
                item.get("timestamp")
                or item.get("time")
                or "Unknown time"
            )
            fmt = item.get("format", "?")
            title = item.get("title", "Unknown title")

            text = f"{time} | {fmt} | {title}"
            self.list_widget.addItem(text)
