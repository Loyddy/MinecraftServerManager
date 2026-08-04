from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QFormLayout, QLineEdit, QComboBox,
                             QSpinBox, QCheckBox, QPushButton, QMessageBox, QLabel, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from utils import get_prop_val, set_prop_val
from animations import play_bounce_in, add_click_bounce


class ServerSettingsDialog(QDialog):
    """采用内部容器动画的服务器设置对话框 (完全解决原生窗口闪烁 Bug)"""

    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.setWindowTitle(f"Server Settings - {server_name}")
        self.resize(450, 380)

        self.setStyleSheet("""
            QDialog { background-color: #1e293b; }
            QLabel { color: #f8fafc; font-weight: bold; }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px;
                color: white;
            }
            QCheckBox { color: #f8fafc; }
            QTabWidget::pane { border: 1px solid #334155; border-radius: 6px; background: #0f172a; }
            QTabBar::tab { background: #1e293b; color: #94a3b8; padding: 8px 16px; border-top-left-radius: 4px; border-top-right-radius: 4px;}
            QTabBar::tab:selected { background: #3b82f6; color: white; font-weight: bold; }
        """)

        # 根布局与内部动画容器
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget(self)
        root_layout.addWidget(self.container)

        self.init_ui()
        play_bounce_in(self.container, duration=400)

    def init_ui(self):
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel(f"⚙️ Configure: {self.server_name}")
        title.setStyleSheet("font-size: 16px; margin-bottom: 5px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._init_basic_tab()
        self._init_world_tab()
        self._init_network_tab()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Close")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: 1px solid #64748b; color: white; padding: 8px 20px; border-radius: 6px; }
            QPushButton:hover { background-color: #334155; }
        """)
        add_click_bounce(cancel_btn)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Config")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; border: none; color: white; padding: 8px 20px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        add_click_bounce(save_btn)
        save_btn.clicked.connect(self.save_settings)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _init_basic_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(15, 20, 15, 20)
        form.setVerticalSpacing(16)

        self.motd_input = QLineEdit(str(get_prop_val(self.server_name, "motd", "A Minecraft Server")))

        self.gamemode_combo = QComboBox()
        self.gamemode_combo.addItems(["survival", "creative", "adventure", "spectator"])
        self.gamemode_combo.setCurrentText(str(get_prop_val(self.server_name, "gamemode", "survival")))

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["peaceful", "easy", "normal", "hard"])
        self.difficulty_combo.setCurrentText(str(get_prop_val(self.server_name, "difficulty", "easy")))

        self.max_players_spin = QSpinBox()
        self.max_players_spin.setRange(1, 1000)
        self.max_players_spin.setValue(int(get_prop_val(self.server_name, "max-players", 20)))

        form.addRow("📝 Server MOTD:", self.motd_input)
        form.addRow("🎮 Game Mode:", self.gamemode_combo)
        form.addRow("⚔️ Difficulty:", self.difficulty_combo)
        form.addRow("👥 Max Players:", self.max_players_spin)

        self.tabs.addTab(tab, "Basic")

    def _init_world_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(15, 20, 15, 20)
        form.setVerticalSpacing(16)

        self.pvp_check = QCheckBox("Allow players to attack each other")
        self.pvp_check.setChecked(bool(get_prop_val(self.server_name, "pvp", True)))

        self.hardcore_check = QCheckBox("One death = Game Over")
        self.hardcore_check.setStyleSheet("color: #fca5a5;")
        self.hardcore_check.setChecked(bool(get_prop_val(self.server_name, "hardcore", False)))

        self.flight_check = QCheckBox("Allow flight (prevents kick for flying)")
        self.flight_check.setChecked(bool(get_prop_val(self.server_name, "allow-flight", False)))

        form.addRow("⚔️ PVP:", self.pvp_check)
        form.addRow("💀 Hardcore:", self.hardcore_check)
        form.addRow("🦅 Flight:", self.flight_check)

        self.tabs.addTab(tab, "World Rules")

    def _init_network_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(15, 20, 15, 20)
        form.setVerticalSpacing(16)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(int(get_prop_val(self.server_name, "server-port", 25565)))

        self.online_mode_check = QCheckBox("Validate users with Mojang (Disable for offline)")
        self.online_mode_check.setChecked(bool(get_prop_val(self.server_name, "online-mode", True)))

        form.addRow("🔌 Server Port:", self.port_spin)
        form.addRow("🌐 Online Mode:", self.online_mode_check)

        self.tabs.addTab(tab, "Network")

    def save_settings(self):
        set_prop_val(self.server_name, "motd", self.motd_input.text())
        set_prop_val(self.server_name, "gamemode", self.gamemode_combo.currentText())
        set_prop_val(self.server_name, "difficulty", self.difficulty_combo.currentText())
        set_prop_val(self.server_name, "max-players", self.max_players_spin.value())

        set_prop_val(self.server_name, "pvp", self.pvp_check.isChecked())
        set_prop_val(self.server_name, "hardcore", self.hardcore_check.isChecked())
        set_prop_val(self.server_name, "allow-flight", self.flight_check.isChecked())

        set_prop_val(self.server_name, "server-port", self.port_spin.value())
        set_prop_val(self.server_name, "online-mode", self.online_mode_check.isChecked())

        QMessageBox.information(self, "Success",
                                "Settings successfully saved!\nPlease restart the server for changes to take effect.")


class ConsoleDialog(QDialog):
    def __init__(self, server_name, process_mgr, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.process_mgr = process_mgr
        self.setWindowTitle(f"Console - {server_name}")
        self.resize(700, 450)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget(self)
        root_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 16, 16, 16)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #0f172a; color: #f8fafc; font-family: Consolas, monospace;")
        layout.addWidget(self.log_output)

        cmd_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.returnPressed.connect(self.send_command)
        send_btn = QPushButton("Send")
        add_click_bounce(send_btn)
        send_btn.clicked.connect(self.send_command)

        cmd_layout.addWidget(self.cmd_input)
        cmd_layout.addWidget(send_btn)
        layout.addLayout(cmd_layout)

        self.load_existing_logs()
        play_bounce_in(self.container, duration=400)

    def load_existing_logs(self):
        logs = self.process_mgr.get_logs(self.server_name)
        if logs:
            self.log_output.setPlainText("\n".join(logs))
            self.scroll_to_bottom()

    def append_log(self, name, text):
        if name == self.server_name:
            self.log_output.append(text)
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        QTimer.singleShot(10, lambda: self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        ))

    def send_command(self):
        cmd = self.cmd_input.text().strip()
        if cmd:
            self.process_mgr.send_cmd(self.server_name, cmd)
            self.cmd_input.clear()


class ModManagerDialog(QDialog):
    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.setWindowTitle(f"Mod Manager - {server_name}")
        self.resize(500, 400)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget(self)
        root_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 16, 16, 16)

        label = QLabel("Mod Manager Interface\n(Drag and Drop .jar files here to install)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        play_bounce_in(self.container, duration=400)