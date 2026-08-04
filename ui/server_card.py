from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal

from utils import get_server_memory, get_prop_val
from animations import play_bounce_in, add_click_bounce
from .widgets import NonScrollSlider


class ServerCardWidget(QFrame):
    """单个服务器实例卡片组件（集成果冻 Q 弹下压与卡片入场 Bounce 动画）"""

    toggle_run_requested = pyqtSignal(str, bool)
    open_console_requested = pyqtSignal(str)
    open_mods_requested = pyqtSignal(str)
    open_settings_requested = pyqtSignal(str)
    toggle_backup_requested = pyqtSignal(str, bool)
    manual_backup_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    save_memory_requested = pyqtSignal(str, int)
    save_distances_requested = pyqtSignal(str, int, int)

    def __init__(self, server_name: str, is_running: bool, auto_backup_enabled: bool, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.is_running = is_running
        self.auto_backup_enabled = auto_backup_enabled

        self.setObjectName("ServerCard")
        self.setStyleSheet("""
            QFrame#ServerCard {
                background-color: rgba(30, 41, 59, 0.4); 
                border: 1px solid rgba(255, 255, 255, 0.05); 
                border-radius: 12px;
            }
            QFrame#ServerCard:hover {
                border: 1px solid #60a5fa;
                background-color: rgba(30, 41, 59, 0.7);
            }
            QFrame#ServerCard QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                padding: 6px 14px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
            }
            QFrame#ServerCard QPushButton:hover {
                border: 1px solid rgba(255, 255, 255, 0.35);
                background-color: rgba(255, 255, 255, 0.15);
            }
            QFrame#ServerCard QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
            QFrame#ServerCard QPushButton#accentBtn {
                border: 1px solid rgba(59, 130, 246, 0.5);
                color: #93c5fd;
                background-color: rgba(59, 130, 246, 0.15);
            }
            QFrame#ServerCard QPushButton#accentBtn:hover {
                border: 1px solid rgba(59, 130, 246, 0.8);
                background-color: rgba(59, 130, 246, 0.3);
            }
            QFrame#ServerCard QPushButton#dangerBtn {
                border: 1px solid rgba(239, 68, 68, 0.5);
                color: #fca5a5;
                background-color: rgba(239, 68, 68, 0.15);
            }
            QFrame#ServerCard QPushButton#dangerBtn:hover {
                border: 1px solid rgba(239, 68, 68, 0.8);
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)

        self.init_ui()
        play_bounce_in(self, duration=550, delay=20)

    def init_ui(self):
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(16, 14, 16, 14)

        # Row 1: 名称、状态与基本控制按钮
        row1 = QHBoxLayout()
        name_lbl = QLabel(self.server_name)
        name_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #f8fafc;")

        status_lbl = QLabel("● Running" if self.is_running else "● Stopped")
        status_lbl.setStyleSheet(
            "color: #4ade80; font-weight: 600;" if self.is_running else "color: #94a3b8; font-weight: 600;")

        row1.addWidget(name_lbl)
        row1.addWidget(status_lbl)
        row1.addStretch()

        run_btn = QPushButton("Stop" if self.is_running else "Start")
        run_btn.setObjectName("dangerBtn" if self.is_running else "accentBtn")
        run_btn.clicked.connect(lambda: self.toggle_run_requested.emit(self.server_name, self.is_running))

        console_btn = QPushButton("Console")
        console_btn.clicked.connect(lambda: self.open_console_requested.emit(self.server_name))

        mod_btn = QPushButton("Mods")
        mod_btn.clicked.connect(lambda: self.open_mods_requested.emit(self.server_name))

        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(lambda: self.open_settings_requested.emit(self.server_name))

        auto_backup_btn = QPushButton(f"Auto-Backup: {'On' if self.auto_backup_enabled else 'Off'}")
        auto_backup_btn.setCheckable(True)
        auto_backup_btn.setChecked(self.auto_backup_enabled)
        auto_backup_btn.clicked.connect(lambda: self._on_toggle_backup_clicked(auto_backup_btn))

        backup_btn = QPushButton("Backup")
        backup_btn.clicked.connect(lambda: self.manual_backup_requested.emit(self.server_name))

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("dangerBtn")
        del_btn.setEnabled(not self.is_running)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.server_name))

        # 给各个按钮都绑定弹性触感反馈
        for btn in [run_btn, console_btn, mod_btn, settings_btn, auto_backup_btn, backup_btn, del_btn]:
            add_click_bounce(btn)
            row1.addWidget(btn)

        card_layout.addLayout(row1)

        # Row 2: 内存设置
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("💾 Max Memory Allocation:"))

        mem_slider = NonScrollSlider(Qt.Orientation.Horizontal)
        mem_slider.setRange(1, 16)
        mem_current_val = get_server_memory(self.server_name)
        mem_slider.setValue(mem_current_val)
        mem_slider.setEnabled(not self.is_running)

        mem_val_lbl = QLabel(f"{mem_current_val} GB")
        mem_val_lbl.setStyleSheet("color: #60a5fa; font-weight: bold;")
        mem_slider.valueChanged.connect(lambda val: mem_val_lbl.setText(f"{val} GB"))

        save_mem_btn = QPushButton("Save")
        save_mem_btn.setEnabled(not self.is_running)
        add_click_bounce(save_mem_btn)
        save_mem_btn.clicked.connect(lambda: self.save_memory_requested.emit(self.server_name, mem_slider.value()))

        row2.addWidget(mem_slider, 1)
        row2.addWidget(mem_val_lbl)
        row2.addWidget(save_mem_btn)
        card_layout.addLayout(row2)

        # Row 3: 视距与仿真距离
        row3 = QHBoxLayout()

        row3.addWidget(QLabel("👁️ View Distance:"))
        vd_slider = NonScrollSlider(Qt.Orientation.Horizontal)
        vd_slider.setRange(8, 32)
        vd_val = get_prop_val(self.server_name, 'view-distance', 10)
        vd_slider.setValue(vd_val)

        vd_val_lbl = QLabel(f"{vd_val}")
        vd_val_lbl.setStyleSheet("color: #60a5fa; font-weight: bold; min-width: 20px;")
        vd_slider.valueChanged.connect(lambda val: vd_val_lbl.setText(f"{val}"))

        row3.addWidget(vd_slider, 1)
        row3.addWidget(vd_val_lbl)

        row3.addWidget(QLabel("🎯 Sim Distance:"))
        sd_slider = NonScrollSlider(Qt.Orientation.Horizontal)
        sd_slider.setRange(4, 16)
        sd_val = get_prop_val(self.server_name, 'simulation-distance', 10)
        sd_slider.setValue(sd_val)

        sd_val_lbl = QLabel(f"{sd_val}")
        sd_val_lbl.setStyleSheet("color: #60a5fa; font-weight: bold; min-width: 20px;")
        sd_slider.valueChanged.connect(lambda val: sd_val_lbl.setText(f"{val}"))

        row3.addWidget(sd_slider, 1)
        row3.addWidget(sd_val_lbl)

        save_dist_btn = QPushButton("Save Distances")
        add_click_bounce(save_dist_btn)
        save_dist_btn.clicked.connect(
            lambda: self.save_distances_requested.emit(self.server_name, vd_slider.value(), sd_slider.value())
        )
        row3.addWidget(save_dist_btn)

        card_layout.addLayout(row3)

    def _on_toggle_backup_clicked(self, btn: QPushButton):
        enabled = btn.isChecked()
        btn.setText(f"Auto-Backup: {'On' if enabled else 'Off'}")
        self.toggle_backup_requested.emit(self.server_name, enabled)