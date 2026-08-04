import os
import zipfile
import subprocess
import threading
import requests
from datetime import datetime
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal
from config import VERSIONS_DIR, BACKUPS_DIR
from utils import get_server_memory, clean_old_backups


class InstallThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, version):
        super().__init__()
        self.version = version

    def run(self):
        server_name = f"{self.version}_fabric"
        target_dir = os.path.join(VERSIONS_DIR, server_name)
        os.makedirs(target_dir, exist_ok=True)
        try:
            self.progress_signal.emit(5, "Preparing environment...")
            with open(os.path.join(target_dir, 'eula.txt'), 'w') as f:
                f.write("eula=true\n")

            self.progress_signal.emit(15, "Fetching Fabric Installer metadata...")
            installer_url = requests.get("https://meta.fabricmc.net/v2/versions/installer").json()[0]['url']
            installer_path = os.path.join(target_dir, 'fabric-installer.jar')

            self.progress_signal.emit(25, "Downloading Fabric Installer...")
            res = requests.get(installer_url, stream=True)
            res.raise_for_status()

            total_length = int(res.headers.get('content-length', 0))
            downloaded = 0

            with open(installer_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_length > 0:
                            percent = 25 + int((downloaded / total_length) * 35)
                            self.progress_signal.emit(percent, f"Downloading Installer ({downloaded // 1024} KB)...")

            self.progress_signal.emit(65, f"Building Fabric Server ({self.version})...")
            subprocess.run(
                ["java", "-jar", "fabric-installer.jar", "server", "-mcversion", self.version, "-downloadMinecraft"],
                cwd=target_dir, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            self.progress_signal.emit(90, "Creating startup script...")
            start_bat_path = os.path.join(target_dir, 'start.bat')
            with open(start_bat_path, 'w', encoding='utf-8') as f:
                f.write("@echo off\njava -Xmx2G -Xms2G -jar fabric-server-launch.jar nogui\npause")

            self.progress_signal.emit(100, "Installation Complete!")
            self.finished_signal.emit(True, f"Server [{server_name}] built successfully!")
        except Exception as e:
            self.finished_signal.emit(False, f"Installation failed: {str(e)}")


class BackupThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, server_name, is_auto=False):
        super().__init__()
        self.server_name = server_name
        self.is_auto = is_auto

    def run(self):
        world_dir = os.path.join(VERSIONS_DIR, self.server_name, 'world')
        if not os.path.exists(world_dir):
            self.finished_signal.emit(False, f"[{self.server_name}] World save folder missing!")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        server_backup_dir = os.path.join(BACKUPS_DIR, self.server_name)
        os.makedirs(server_backup_dir, exist_ok=True)

        prefix = "world_auto" if self.is_auto else "world"
        zip_path = os.path.join(server_backup_dir, f"{prefix}_{timestamp}.zip")

        try:
            self.progress_signal.emit(10, f"[{self.server_name}] Scanning files...")
            file_list = []
            for root, _, files in os.walk(world_dir):
                for file in files:
                    file_list.append(os.path.join(root, file))

            total_files = len(file_list)
            if total_files == 0:
                self.finished_signal.emit(False, f"[{self.server_name}] World folder is empty.")
                return

            self.progress_signal.emit(20, f"[{self.server_name}] Compressing world data ({total_files} files)...")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx, file_path in enumerate(file_list, 1):
                    arcname = os.path.relpath(file_path, world_dir)
                    zipf.write(file_path, arcname)
                    if idx % 5 == 0 or idx == total_files:
                        percent = 20 + int((idx / total_files) * 75)
                        self.progress_signal.emit(percent, f"[{self.server_name}] Backing up: {idx}/{total_files} files")

            self.progress_signal.emit(98, f"[{self.server_name}] Cleaning old backups...")
            clean_old_backups(self.server_name, max_keep=2)

            self.progress_signal.emit(100, f"[{self.server_name}] Backup completed!")
            self.finished_signal.emit(True, f"Backup created successfully: {os.path.basename(zip_path)}")
        except Exception as e:
            self.finished_signal.emit(False, f"Backup failed: {str(e)}")


class ServerProcessManager(QThread):
    log_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.processes = {}
        self.logs = defaultdict(list)

    def get_running_server(self):
        """Returns name of currently running server, or None"""
        for server_name, proc in self.processes.items():
            if proc and proc.poll() is None:
                return server_name
        return None

    def start_server(self, server_name):
        running_server = self.get_running_server()
        if running_server and running_server != server_name:
            return False, f"Server [{running_server}] is already running."

        if server_name in self.processes and self.processes[server_name].poll() is None:
            return False, "Server is already running"

        server_dir = os.path.join(VERSIONS_DIR, server_name)
        memory_gb = get_server_memory(server_name)
        cmd = ["java", f"-Xmx{memory_gb}G", f"-Xms{memory_gb}G", "-jar", "fabric-server-launch.jar", "nogui"]

        try:
            # Read as binary stream to prevent GBK/UTF-8 UnicodeDecodeError on Windows
            proc = subprocess.Popen(
                cmd, cwd=server_dir, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            self.processes[server_name] = proc

            t = threading.Thread(target=self._read_output, args=(server_name, proc), daemon=True)
            t.start()
            return True, "Started successfully"
        except Exception as e:
            return False, str(e)

    def _read_output(self, server_name, process):
        """Robust binary output reader with fallback decoding to prevent UnicodeDecodeError"""
        for line_bytes in iter(process.stdout.readline, b''):
            if not line_bytes:
                break
            try:
                clean_line = line_bytes.decode('utf-8').rstrip()
            except UnicodeDecodeError:
                try:
                    clean_line = line_bytes.decode('gbk', errors='replace').rstrip()
                except Exception:
                    clean_line = line_bytes.decode('ascii', errors='replace').rstrip()

            self.logs[server_name].append(clean_line)
            self.log_signal.emit(server_name, clean_line)

    def get_logs(self, server_name):
        return self.logs.get(server_name, [])

    def stop_server(self, server_name):
        proc = self.processes.get(server_name)
        if proc and proc.poll() is None:
            try:
                proc.stdin.write(b"stop\n")
                proc.stdin.flush()
                return True, "Stop command sent"
            except Exception:
                proc.terminate()
                return True, "Force terminated"
        return False, "Not running"

    def send_cmd(self, server_name, cmd):
        proc = self.processes.get(server_name)
        if proc and proc.poll() is None:
            try:
                proc.stdin.write((cmd + "\n").encode('utf-8'))
                proc.stdin.flush()
                self.logs[server_name].append(f"> {cmd}")
                self.log_signal.emit(server_name, f"> {cmd}")
                return True
            except Exception:
                pass
        return False

    def send_command(self, server_name, cmd):
        return self.send_cmd(server_name, cmd)

    def is_running(self, server_name):
        proc = self.processes.get(server_name)
        return proc is not None and proc.poll() is None

    def get_pid(self, server_name):
        proc = self.processes.get(server_name)
        if proc and proc.poll() is None:
            return proc.pid
        return None