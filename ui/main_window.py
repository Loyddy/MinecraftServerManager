import os
import shutil
import re
import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSpinBox,
    QMessageBox, QScrollArea, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from config import VERSIONS_DIR
from utils import load_config, save_config, set_prop_val
from threads import ServerProcessManager, InstallThread, BackupThread
from dialogs import ConsoleDialog, ModManagerDialog, ServerSettingsDialog
from animations import add_click_bounce
from .widgets import DeploySuccessPopup
from .server_card import ServerCardWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fabric Server Manager Pro")
        self.resize(1000, 750)

        self.process_mgr = ServerProcessManager()
        self.auto_backup_config = {}
        self.auto_backup_interval = load_config()
        self.active_backups = []

        self.init_ui()
        self.init_statusbar()

        self.backup_timer = QTimer(self)
        self.backup_timer.timeout.connect(self.auto_backup_task)
        self.backup_timer.start(self.auto_backup_interval * 60 * 1000)

        self.refresh_servers()
        QTimer.singleShot(100, self.fetch_fabric_versions)

    def init_statusbar(self):
        """Initialize progress bar in the bottom status bar"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.statusBar().addPermanentWidget(self.progress_bar)
        self.statusBar().showMessage("Ready")

    def show_progress(self, percent: int, msg: str):
        """Show and update status bar progress bar"""
        if not self.progress_bar.isVisible():
            self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)
        self.statusBar().showMessage(msg)

    def hide_progress(self, msg: str = "Ready", timeout: int = 4000):
        """Hide status bar progress bar"""
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage(msg, timeout)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header Section
        header_layout = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title_lbl = QLabel("Fabric Server Console")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        sub_lbl = QLabel("Lightweight local server deployment and management")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_vbox.addWidget(title_lbl)
        title_vbox.addWidget(sub_lbl)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        badge_lbl = QLabel("● Fabric API Ready")
        badge_lbl.setStyleSheet(
            "color: #60a5fa; background-color: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 11px;")
        header_layout.addWidget(badge_lbl)
        main_layout.addLayout(header_layout)

        # 1. Deploy Card
        deploy_card = QFrame()
        deploy_card.setObjectName("GlassCard")
        deploy_layout = QVBoxLayout(deploy_card)
        deploy_layout.setContentsMargins(20, 20, 20, 20)

        deploy_title = QLabel("📦 Deploy Fabric Server")
        deploy_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 14px;")
        deploy_layout.addWidget(deploy_title)

        deploy_sub_layout = QHBoxLayout()
        self.version_combo = QComboBox()
        self.version_combo.addItem("Loading official versions list...")

        self.install_btn = QPushButton("One-Click Download & Build")
        self.install_btn.setObjectName("accentBtn")
        add_click_bounce(self.install_btn)
        self.install_btn.clicked.connect(self.install_server)

        deploy_sub_layout.addWidget(QLabel("Select Version:"), 0)
        deploy_sub_layout.addWidget(self.version_combo, 1)
        deploy_sub_layout.addWidget(self.install_btn, 0)
        deploy_layout.addLayout(deploy_sub_layout)
        main_layout.addWidget(deploy_card)

        # 2. Auto-Backup Card
        backup_card = QFrame()
        backup_card.setObjectName("GlassCard")
        backup_layout = QHBoxLayout(backup_card)
        backup_layout.setContentsMargins(20, 16, 20, 16)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(self.auto_backup_interval)

        save_interval_btn = QPushButton("Save Interval")
        add_click_bounce(save_interval_btn)
        save_interval_btn.clicked.connect(self.update_backup_interval)

        backup_layout.addWidget(QLabel("🕒 Scheduled Auto-Backup Interval (mins):"))
        backup_layout.addWidget(self.interval_spin)
        backup_layout.addWidget(save_interval_btn)
        backup_layout.addStretch()
        main_layout.addWidget(backup_card)

        # 3. Server Instances Container
        servers_card = QFrame()
        servers_card.setObjectName("GlassCard")
        servers_card_layout = QVBoxLayout(servers_card)
        servers_card_layout.setContentsMargins(20, 20, 20, 20)

        servers_header = QHBoxLayout()
        servers_title = QLabel("⚡ My Server Instances")
        servers_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 14px;")
        refresh_btn = QPushButton("Refresh")
        add_click_bounce(refresh_btn)
        refresh_btn.clicked.connect(self.refresh_servers)
        servers_header.addWidget(servers_title)
        servers_header.addStretch()
        servers_header.addWidget(refresh_btn)
        servers_card_layout.addLayout(servers_header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.rebuild_scroll_content()

        servers_card_layout.addWidget(self.scroll_area)
        main_layout.addWidget(servers_card, 1)

    def rebuild_scroll_content(self):
        if hasattr(self, 'scroll_content') and self.scroll_content:
            self.scroll_area.takeWidget()
            self.scroll_content.setParent(None)
            self.scroll_content.deleteLater()

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.servers_vbox = QVBoxLayout(self.scroll_content)
        self.servers_vbox.setSpacing(12)
        self.servers_vbox.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.scroll_content)

    def fetch_fabric_versions(self):
        try:
            res = requests.get("https://meta.fabricmc.net/v2/versions/game", timeout=5)
            versions = [v['version'] for v in res.json()]
            self.version_combo.clear()
            self.version_combo.addItems(versions)
        except Exception:
            self.version_combo.clear()
            self.version_combo.addItem("Failed to fetch versions")

    def install_server(self):
        version = self.version_combo.currentText()
        if not version or "Failed" in version or "Loading" in version:
            QMessageBox.warning(self, "Warning", "Please select a valid game version first!")
            return

        self.install_btn.setEnabled(False)
        self.install_thread = InstallThread(version)
        self.install_thread.progress_signal.connect(self.show_progress)
        self.install_thread.finished_signal.connect(self.on_install_finished)
        self.install_thread.start()

    def on_install_finished(self, success, msg):
        self.install_btn.setEnabled(True)
        self.hide_progress(msg, 5000)
        if success:
            DeploySuccessPopup(f"🎉 {msg}", self)
            QTimer.singleShot(50, self.refresh_servers)
        else:
            QMessageBox.critical(self, "Error", msg)

    def manual_backup(self, server_name):
        self._start_backup_thread(server_name, is_auto=False)

    def auto_backup_task(self):
        for server_name in list(self.auto_backup_config.keys()):
            if self.auto_backup_config.get(server_name, True) and self.process_mgr.is_running(server_name):
                self._start_backup_thread(server_name, is_auto=True)

    def _start_backup_thread(self, server_name, is_auto=False):
        thread = BackupThread(server_name, is_auto=is_auto)
        self.active_backups.append(thread)
        thread.progress_signal.connect(self.show_progress)

        def _on_finished(success, msg):
            self.hide_progress(msg, 4000)
            if not is_auto:
                if success:
                    QMessageBox.information(self, "Success", msg)
                else:
                    QMessageBox.warning(self, "Backup Failed", msg)
            if thread in self.active_backups:
                self.active_backups.remove(thread)

        thread.finished_signal.connect(_on_finished)
        thread.start()

    def refresh_servers(self):
        self.rebuild_scroll_content()

        if not os.path.exists(VERSIONS_DIR):
            return

        servers = [s for s in os.listdir(VERSIONS_DIR) if os.path.isdir(os.path.join(VERSIONS_DIR, s))]

        if not servers:
            empty_lbl = QLabel("No server instances found. Select a version above and click build to deploy.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #64748b; padding: 30px;")
            self.servers_vbox.addWidget(empty_lbl)
            return

        for server_name in servers:
            is_running = self.process_mgr.is_running(server_name)
            if server_name not in self.auto_backup_config:
                self.auto_backup_config[server_name] = True

            card = ServerCardWidget(
                server_name=server_name,
                is_running=is_running,
                auto_backup_enabled=self.auto_backup_config[server_name]
            )

            card.toggle_run_requested.connect(self.toggle_server_run)
            card.open_console_requested.connect(self.open_console)
            card.open_mods_requested.connect(self.open_mod_manager)
            card.open_settings_requested.connect(self.open_server_settings)
            card.toggle_backup_requested.connect(self.toggle_auto_backup)
            card.manual_backup_requested.connect(self.manual_backup)
            card.delete_requested.connect(self.delete_server)
            card.save_memory_requested.connect(self.save_memory)
            card.save_distances_requested.connect(self.save_distances)

            self.servers_vbox.addWidget(card)

        self.servers_vbox.addStretch()

    def toggle_server_run(self, server_name, is_running):
        if is_running:
            ok, msg = self.process_mgr.stop_server(server_name)
        else:
            running_server = self.process_mgr.get_running_server()
            if running_server:
                QMessageBox.warning(
                    self,
                    "Operation Rejected",
                    f"Only one server can be running at a time!\n\nServer [{running_server}] is currently running. Please stop it first before starting a new server."
                )
                return

            ok, msg = self.process_mgr.start_server(server_name)

        if not ok:
            QMessageBox.warning(self, "Operation Failed", msg)
        QTimer.singleShot(1000, self.refresh_servers)

    def save_memory(self, server_name, memory_gb):
        bat_path = os.path.join(VERSIONS_DIR, server_name, 'start.bat')
        if not os.path.exists(bat_path):
            return
        try:
            with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            content = re.sub(r'-Xmx\d+G', f'-Xmx{memory_gb}G', content, flags=re.IGNORECASE)
            content = re.sub(r'-Xms\d+G', f'-Xms{memory_gb}G', content, flags=re.IGNORECASE)
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Success", f"Memory updated to {memory_gb} GB")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_distances(self, server_name, view_dist, sim_dist):
        set_prop_val(server_name, 'view-distance', view_dist)
        set_prop_val(server_name, 'simulation-distance', sim_dist)
        QMessageBox.information(self, "Success", "Distance configuration updated successfully!")

    def toggle_auto_backup(self, server_name, enabled):
        self.auto_backup_config[server_name] = enabled

    def update_backup_interval(self):
        mins = self.interval_spin.value()
        self.auto_backup_interval = mins
        save_config(mins)
        self.backup_timer.setInterval(mins * 60 * 1000)
        QMessageBox.information(self, "Success", f"Backup interval adjusted to {mins} minutes!")

    def delete_server(self, server_name):
        if QMessageBox.question(self, "Confirm Delete",
                                f"Are you sure you want to delete server [{server_name}]?") == QMessageBox.StandardButton.Yes:
            server_dir = os.path.join(VERSIONS_DIR, server_name)
            try:
                shutil.rmtree(server_dir)
                if server_name in self.auto_backup_config:
                    del self.auto_backup_config[server_name]
                self.refresh_servers()
            except Exception as e:
                QMessageBox.critical(self, "Deletion Failed", str(e))

    def open_console(self, server_name):
        dlg = ConsoleDialog(server_name, self.process_mgr, self)
        self.process_mgr.log_signal.connect(dlg.append_log)
        dlg.exec()
        try:
            self.process_mgr.log_signal.disconnect(dlg.append_log)
        except Exception:
            pass

    def open_mod_manager(self, server_name):
        dlg = ModManagerDialog(server_name, self)
        dlg.exec()

    def open_server_settings(self, server_name):
        dlg = ServerSettingsDialog(server_name, self)
        dlg.exec()