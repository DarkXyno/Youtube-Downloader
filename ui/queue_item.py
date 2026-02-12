from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

class QueueItemWidget(QWidget):
    def __init__(self, title):
        super().__init__()

        layout = QVBoxLayout(self)

        self.title = title
        self.title_label = QLabel(title)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        layout.addWidget(self.title_label)
        layout.addWidget(self.progress)

    def set_progress(self, value):
        self.progress.setValue(int(value))

    def set_status(self, text):
        self.title_label.setText(text)