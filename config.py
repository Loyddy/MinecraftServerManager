import os
import sys

# --- Base Path Configuration ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VERSIONS_DIR = os.path.join(BASE_DIR, 'Versions')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

os.makedirs(VERSIONS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

# --- Modern QSS Stylesheet ---
MODERN_STYLE = """
QMainWindow, QDialog {
    background-color: #0b0f17;
}

QWidget {
    color: #cbd5e1;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 13px;
}

QFrame#GlassCard {
    background-color: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}

QLabel {
    color: #cbd5e1;
    background: transparent;
}

QPushButton {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 6px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
    border-color: rgba(255, 255, 255, 0.2);
}

QPushButton:pressed {
    background-color: #0f172a;
}

QPushButton#accentBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
    color: #ffffff;
    border: none;
    border-radius: 10px;
}

QPushButton#accentBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1);
}

QPushButton#dangerBtn {
    background-color: rgba(244, 63, 94, 0.1);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.2);
    border-radius: 10px;
}

QPushButton#dangerBtn:hover {
    background-color: rgba(244, 63, 94, 0.2);
}

QComboBox, QSpinBox, QLineEdit {
    background-color: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 6px 12px;
    color: #f8fafc;
}

QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
    border: 1px solid #3b82f6;
}

QComboBox::drop-down {
    border: none;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #60a5fa;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QScrollBar:vertical {
    background: #0b0f17;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
}

QStatusBar {
    background: #0f172a;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
}

QProgressBar {
    background-color: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    font-size: 11px;
    font-weight: bold;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #60a5fa);
    border-radius: 5px;
}
"""