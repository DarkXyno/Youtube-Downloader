import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.updater import start_updater


def main():
    app = QApplication(sys.argv)

    window = MainWindow()

    start_updater()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
