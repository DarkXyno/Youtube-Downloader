DARK_THEME = """
QWidget {
    color: white;
}

QLineEdit, QComboBox {
    background-color: rgba(255, 255, 255, 30);
    border: 1px solid rgba(255,255,255,80);
    border-radius: 6px;
    padding: 6px;
    color: white;
}

QPushButton {
    background-color: rgba(0, 170, 200, 180);
    border-radius: 8px;
    padding: 8px;
    color: white;
}

QPushButton:hover {
    background-color: rgba(0, 200, 230, 200);
}

QProgressBar {
    background-color: rgba(255,255,255,30);
    border-radius: 6px;
    height: 12px;
}

QProgressBar::chunk {
    background-color: rgb(0, 200, 230);
    border-radius: 6px;
}
"""
