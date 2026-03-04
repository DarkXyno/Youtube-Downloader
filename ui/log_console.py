from PySide6.QtWidgets import QTextEdit

class LogConsole(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def append_log(self, message):
        # QTextEdit uses append() for adding plain text lines.
        self.append(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
