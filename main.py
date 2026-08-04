import sys
from PyQt6.QtWidgets import QApplication
from config import MODERN_STYLE
from main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())