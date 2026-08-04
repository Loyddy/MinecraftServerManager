import os
import json
import shutil
import subprocess
import threading
import requests
import webbrowser
import time
import re
import psutil
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file

app = Flask(__name__, static_folder='.', static_url_path='')

# 目录结构配置
ASSISTANT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(ASSISTANT_DIR)
VERSIONS_DIR = os.path.join(BASE_DIR, 'Versions')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')
CONFIG_FILE = os.path.join(ASSISTANT_DIR, 'config.json')

# 确保文件夹存在
os.makedirs(VERSIONS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)

# 运行中的服务器进程字典 (server_name: Popen_object)
running_servers = {}
# 控制台实时日志缓存 (server_name: [line1, line2, ...])
server_logs = {}

download_status = {"status": "idle", "msg": ""}

# 存储服务器的自动备份开关配置
auto_backup_config = {}


# --- 配置加载与持久化 ---
def load_config():
    """从 config.json 读取配置，默认备份间隔为 30 分钟"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('backup_interval_minutes', 30) * 60
        except Exception as e:
            print(f"[配置读取失败] 使用默认配置: {str(e)}")
    return 30 * 60


def save_config(backup_interval_seconds):
    """保存备份间隔到 config.json"""
    try:
        config = {'backup_interval_minutes': int(backup_interval_seconds / 60)}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"[配置已保存] 备份间隔: {int(backup_interval_seconds / 60)} 分钟")
    except Exception as e:
        print(f"[配置保存失败]: {str(e)}")


# 全局备份检测间隔时间（单位：秒）
auto_backup_interval = load_config()


def clean_old_backups(server_name, max_keep=2):
    """只保留某个服务器最新创建的 max_keep 个备份压缩包"""
    server_backup_dir = os.path.join(BACKUPS_DIR, server_name)
    if not os.path.exists(server_backup_dir):
        return

    zip_files = [
        os.path.join(server_backup_dir, f)
        for f in os.listdir(server_backup_dir)
        if f.endswith('.zip')
    ]
    zip_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    if len(zip_files) > max_keep:
        for old_file in zip_files[max_keep:]:
            try:
                os.remove(old_file)
                print(f"[清理旧备份] 已删除多余备份: {os.path.basename(old_file)}")
            except Exception as e:
                print(f"[清理旧备份] 删除失败: {str(e)}")


def set_status(msg, status="running"):
    download_status["msg"] = msg
    download_status["status"] = status
    print(f"[状态] {msg}")


def download_file(url, dest):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def get_server_memory(server_name):
    """读取 start.bat 中的内存设置 (-Xmx)，默认为 2G"""
    bat_path = os.path.join(VERSIONS_DIR, server_name, 'start.bat')
    if not os.path.exists(bat_path):
        return 2
    try:
        with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            match = re.search(r'-Xmx(\d+)G', content, re.IGNORECASE)
            if match:
                return int(match.group(1))
    except Exception:
        pass
    return 2


def get_server_properties_value(server_name, key, default):
    """从 server.properties 读取指定配置项的值"""
    prop_path = os.path.join(VERSIONS_DIR, server_name, 'server.properties')
    if not os.path.exists(prop_path):
        return default
    try:
        with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    val = line.strip().split('=')[1]
                    return int(val)
    except Exception:
        pass
    return default


def set_server_properties_value(server_name, key, value):
    """修改 server.properties 中的指定配置项"""
    prop_path = os.path.join(VERSIONS_DIR, server_name, 'server.properties')
    if not os.path.exists(prop_path):
        return False
    try:
        with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(prop_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception:
        return False


def read_process_output(server_name, process):
    """线程：读取子进程标准输出存入内存，供前端控制台实时拉取"""
    server_logs[server_name] = []
    for line in iter(process.stdout.readline, ''):
        if not line:
            break
        server_logs[server_name].append(line)
        if len(server_logs[server_name]) > 800:
            server_logs[server_name].pop(0)


def install_server_task(version):
    server_name = f"{version}_fabric"
    target_dir = os.path.join(VERSIONS_DIR, server_name)
    os.makedirs(target_dir, exist_ok=True)

    try:
        set_status(f"正在准备 {server_name} 的环境...")

        # 自动同意 EULA
        with open(os.path.join(target_dir, 'eula.txt'), 'w') as f:
            f.write("eula=true\n")

        start_bat_path = os.path.join(target_dir, 'start.bat')

        set_status("正在获取 Fabric Installer...")
        installer_url = requests.get("https://meta.fabricmc.net/v2/versions/installer").json()[0]['url']
        installer_path = os.path.join(target_dir, 'fabric-installer.jar')
        download_file(installer_url, installer_path)

        set_status(f"正在安装 Fabric 服务端 ({version})...")
        subprocess.run(["java", "-jar", "fabric-installer.jar", "server", "-mcversion", version, "-downloadMinecraft"],
                       cwd=target_dir, check=True)

        # 默认分配 2G 内存
        with open(start_bat_path, 'w', encoding='utf-8') as f:
            f.write("@echo off\njava -Xmx2G -Xms2G -jar fabric-server-launch.jar nogui\npause")

        auto_backup_config[server_name] = True
        set_status(f"{server_name} 安装完成！", "done")
    except Exception as e:
        set_status(f"安装失败: {str(e)}", "error")


def auto_backup_task():
    """后台定时自动备份线程"""
    while True:
        time.sleep(auto_backup_interval)
        for server_name, process in list(running_servers.items()):
            if auto_backup_config.get(server_name, True) and process.poll() is None:
                world_dir = os.path.join(VERSIONS_DIR, server_name, 'world')
                if os.path.exists(world_dir):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    server_backup_dir = os.path.join(BACKUPS_DIR, server_name)
                    os.makedirs(server_backup_dir, exist_ok=True)

                    backup_filename = f"world_auto_{timestamp}"
                    backup_path = os.path.join(server_backup_dir, backup_filename)
                    try:
                        shutil.make_archive(backup_path, 'zip', world_dir)
                        print(
                            f"[自动备份] 成功！服务器 [{server_name}] 已保存至 backups/{server_name}/{backup_filename}.zip")
                        clean_old_backups(server_name, max_keep=2)
                    except Exception as e:
                        print(f"[自动备份] 失败！服务器 [{server_name}] 报错: {str(e)}")


@app.route('/')
def serve_ui():
    return send_file('index.html')


@app.route('/api/fabric_versions', methods=['GET'])
def get_fabric_versions():
    try:
        res = requests.get("https://meta.fabricmc.net/v2/versions/game")
        versions_data = res.json()
        versions = [v['version'] for v in versions_data]
        return jsonify(versions)
    except Exception as e:
        return jsonify({"error": f"拉取 Fabric 版本列表失败: {str(e)}"}), 500


@app.route('/api/install', methods=['POST'])
def install_server():
    data = request.json
    version = data.get('version')

    if not version:
        return jsonify({"error": "未选择游戏版本！"}), 400

    if download_status['status'] == "running":
        return jsonify({"error": "当前有正在下载的任务，请稍后再试！"}), 400

    threading.Thread(target=install_server_task, args=(version,)).start()
    return jsonify({"message": "安装任务已启动！"})


@app.route('/api/install_status', methods=['GET'])
def get_install_status():
    return jsonify(download_status)


@app.route('/api/servers', methods=['GET'])
def list_servers():
    servers = []
    if os.path.exists(VERSIONS_DIR):
        for s in os.listdir(VERSIONS_DIR):
            if os.path.isdir(os.path.join(VERSIONS_DIR, s)):
                is_running = s in running_servers and running_servers[s].poll() is None
                is_auto_backup = auto_backup_config.get(s, True)
                memory_gb = get_server_memory(s)
                view_distance = get_server_properties_value(s, 'view-distance', 10)
                sim_distance = get_server_properties_value(s, 'simulation-distance', 10)
                servers.append({
                    "name": s,
                    "running": is_running,
                    "auto_backup": is_auto_backup,
                    "memory": memory_gb,
                    "view_distance": view_distance,
                    "simulation_distance": sim_distance
                })
    return jsonify({
        "servers": servers,
        "backup_interval_minutes": int(auto_backup_interval / 60)
    })


@app.route('/api/set_backup_interval', methods=['POST'])
def set_backup_interval():
    global auto_backup_interval
    data = request.json
    minutes = data.get('minutes', 30)
    try:
        minutes = int(minutes)
        if minutes < 1:
            return jsonify({"error": "时间间隔不能小于 1 分钟！"}), 400
        auto_backup_interval = minutes * 60
        save_config(auto_backup_interval)
        return jsonify({"message": f"自动备份间隔已调整为 {minutes} 分钟并已保存到配置文件！"})
    except ValueError:
        return jsonify({"error": "请输入有效的整数时间！"}), 400


@app.route('/api/set_memory', methods=['POST'])
def set_memory():
    data = request.json
    server_name = data.get('name')
    memory = data.get('memory', 2)

    if server_name in running_servers and running_servers[server_name].poll() is None:
        return jsonify({"error": "服务器正在运行中，修改内存需要先停止服务器！"}), 400

    bat_path = os.path.join(VERSIONS_DIR, server_name, 'start.bat')
    if not os.path.exists(bat_path):
        return jsonify({"error": "找不到 start.bat 文件"}), 404

    try:
        with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        content = re.sub(r'-Xmx\d+G', f'-Xmx{memory}G', content, flags=re.IGNORECASE)
        content = re.sub(r'-Xms\d+G', f'-Xms{memory}G', content, flags=re.IGNORECASE)

        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({"message": f"服务器 [{server_name}] 分配内存已更新为 {memory} GB！"})
    except Exception as e:
        return jsonify({"error": f"修改内存配置失败: {str(e)}"}), 500


@app.route('/api/set_distances', methods=['POST'])
def set_distances():
    data = request.json
    server_name = data.get('name')
    view_distance = data.get('view_distance')
    sim_distance = data.get('simulation_distance')

    if not server_name:
        return jsonify({"error": "未提供服务器名称"}), 400

    prop_path = os.path.join(VERSIONS_DIR, server_name, 'server.properties')
    if not os.path.exists(prop_path):
        return jsonify({"error": "找不到 server.properties 文件（请确保服务器至少完整运行并生成过配置文件）"}), 404

    try:
        if view_distance is not None:
            vd = int(view_distance)
            if not (8 <= vd <= 32):
                return jsonify({"error": "视距必须在 8 到 32 之间"}), 400
            set_server_properties_value(server_name, 'view-distance', vd)

        if sim_distance is not None:
            sd = int(sim_distance)
            if not (4 <= sd <= 16):
                return jsonify({"error": "模拟距离必须在 4 到 16 之间"}), 400
            set_server_properties_value(server_name, 'simulation-distance', sd)

        return jsonify({"message": f"服务器 [{server_name}] 的视距和模拟距离配置已更新！"})
    except Exception as e:
        return jsonify({"error": f"更新距离配置失败: {str(e)}"}), 500


@app.route('/api/toggle_auto_backup', methods=['POST'])
def toggle_auto_backup():
    data = request.json
    server_name = data.get('name')
    enabled = data.get('enabled', True)
    auto_backup_config[server_name] = enabled
    state_str = "开启" if enabled else "关闭"
    return jsonify({"message": f"服务器 [{server_name}] 的自动备份已{state_str}"})


@app.route('/api/start', methods=['POST'])
def start_server():
    server_name = request.json.get('name')
    server_dir = os.path.join(VERSIONS_DIR, server_name)
    bat_path = os.path.join(server_dir, 'start.bat')

    if not os.path.exists(bat_path):
        return jsonify({"error": "找不到 start.bat 文件"}), 404

    if server_name in running_servers and running_servers[server_name].poll() is None:
        return jsonify({"error": "服务器已经在运行中！"}), 400

    memory_gb = get_server_memory(server_name)
    cmd = ["java", f"-Xmx{memory_gb}G", f"-Xms{memory_gb}G", "-jar", "fabric-server-launch.jar", "nogui"]

    try:
        process = subprocess.Popen(
            cmd,
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        running_servers[server_name] = process
        threading.Thread(target=read_process_output, args=(server_name, process), daemon=True).start()
        return jsonify({"message": "服务器后台启动成功！"})
    except Exception as e:
        return jsonify({"error": f"启动失败，请检查是否安装 Java: {str(e)}"}), 500


@app.route('/api/stop', methods=['POST'])
def stop_server():
    server_name = request.json.get('name')
    proc = running_servers.get(server_name)
    if proc and proc.poll() is None:
        try:
            proc.stdin.write("stop\n")
            proc.stdin.flush()
            return jsonify({"message": "已向服务器发送停止指令 (stop)..."})
        except Exception as e:
            proc.terminate()
            return jsonify({"message": "已强行中断服务器进程"})
    return jsonify({"error": "服务器未在运行状态"}), 404


@app.route('/api/console/logs', methods=['GET'])
def get_console_logs():
    server_name = request.args.get('name')
    if server_name in server_logs and len(server_logs[server_name]) > 0:
        return jsonify({"logs": server_logs[server_name]})

    log_path = os.path.join(VERSIONS_DIR, server_name, 'logs', 'latest.log')
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-200:]
            return jsonify({"logs": lines})
        except Exception as e:
            return jsonify({"logs": [f"读取日志文件失败: {str(e)}"]})

    return jsonify({"logs": ["服务端尚无实时日志。"]})


@app.route('/api/console/send', methods=['POST'])
def send_command():
    data = request.json
    server_name = data.get('name')
    command = data.get('command', '').strip()

    proc = running_servers.get(server_name)
    if proc and proc.poll() is None:
        try:
            proc.stdin.write(command + "\n")
            proc.stdin.flush()
            return jsonify({"message": f"指令 [{command}] 已发送"})
        except Exception as e:
            return jsonify({"error": f"发送指令失败: {str(e)}"}), 500
    return jsonify({"error": "服务器未运行！"}), 400


@app.route('/api/mods/list', methods=['GET'])
def list_mods():
    server_name = request.args.get('name')
    mods_dir = os.path.join(VERSIONS_DIR, server_name, 'mods')

    if not os.path.exists(mods_dir):
        os.makedirs(mods_dir, exist_ok=True)
        return jsonify({"mods": []})

    mods = []
    for f in os.listdir(mods_dir):
        if f.endswith('.jar') or f.endswith('.jar.disabled'):
            mods.append({
                "name": f,
                "enabled": f.endswith('.jar'),
                "size": round(os.path.getsize(os.path.join(mods_dir, f)) / (1024 * 1024), 2)
            })
    return jsonify({"mods": mods})


@app.route('/api/mods/toggle', methods=['POST'])
def toggle_mod():
    data = request.json
    server_name = data.get('name')
    filename = data.get('filename')

    mods_dir = os.path.join(VERSIONS_DIR, server_name, 'mods')
    filepath = os.path.join(mods_dir, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "找不到指定 Mod 文件"}), 404

    if filename.endswith('.jar'):
        new_path = filepath + '.disabled'
    elif filename.endswith('.jar.disabled'):
        new_path = filepath.replace('.jar.disabled', '.jar')
    else:
        return jsonify({"error": "非 Mod 文件"}), 400

    os.rename(filepath, new_path)
    return jsonify({"message": "Mod 状态更新成功！"})


@app.route('/api/mods/upload', methods=['POST'])
def upload_mod():
    server_name = request.form.get('name')
    file = request.files.get('file')

    if not file or not (file.filename.endswith('.jar') or file.filename.endswith('.jar.disabled')):
        return jsonify({"error": "请上传 .jar 格式的模组文件"}), 400

    mods_dir = os.path.join(VERSIONS_DIR, server_name, 'mods')
    os.makedirs(mods_dir, exist_ok=True)

    filename = secure_filename(file.filename)
    file.save(os.path.join(mods_dir, filename))
    return jsonify({"message": f"Mod [{filename}] 上传成功！"})


@app.route('/api/mods/delete', methods=['POST'])
def delete_mod():
    data = request.json
    server_name = data.get('name')
    filename = data.get('filename')

    if not server_name or not filename:
        return jsonify({"error": "参数不完整"}), 400

    mods_dir = os.path.join(VERSIONS_DIR, server_name, 'mods')
    filepath = os.path.join(mods_dir, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "找不到指定的 Mod 文件"}), 404

    try:
        os.remove(filepath)
        return jsonify({"message": f"Mod [{filename}] 已成功删除！"})
    except Exception as e:
        return jsonify({"error": f"删除 Mod 失败: {str(e)}"}), 500


@app.route('/api/performance', methods=['GET'])
def get_performance():
    server_name = request.args.get('name')
    proc = running_servers.get(server_name)

    if not proc or proc.poll() is not None:
        return jsonify({"running": False, "cpu": 0, "memory_mb": 0, "players": []})

    try:
        p = psutil.Process(proc.pid)
        cpu_percent = p.cpu_percent(interval=0.05)
        memory_mb = round(p.memory_info().rss / (1024 * 1024), 1)

        players = []
        log_path = os.path.join(VERSIONS_DIR, server_name, 'logs', 'latest.log')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                joined = set(re.findall(r'\]: (\w+) joined the game', content))
                left = set(re.findall(r'\]: (\w+) left the game', content))
                players = list(joined - left)

        return jsonify({
            "running": True,
            "cpu": cpu_percent,
            "memory_mb": memory_mb,
            "players_online": len(players),
            "players": players
        })
    except Exception as e:
        return jsonify({"running": False, "error": str(e)})


@app.route('/api/backup', methods=['POST'])
def backup_server():
    server_name = request.json.get('name')
    world_dir = os.path.join(VERSIONS_DIR, server_name, 'world')

    if not os.path.exists(world_dir):
        return jsonify({"error": "未找到 world 存档文件夹，请至少启动过一次服务器！"}), 404

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    server_backup_dir = os.path.join(BACKUPS_DIR, server_name)
    os.makedirs(server_backup_dir, exist_ok=True)

    backup_filename = f"world_{timestamp}"
    backup_path = os.path.join(server_backup_dir, backup_filename)

    try:
        shutil.make_archive(backup_path, 'zip', world_dir)
        clean_old_backups(server_name, max_keep=2)
        return jsonify({"message": f"备份成功！保存到 backups/{server_name}/{backup_filename}.zip"})
    except Exception as e:
        return jsonify({"error": f"备份失败: {str(e)}"}), 500


@app.route('/api/delete', methods=['POST'])
def delete_server():
    server_name = request.json.get('name')
    if not server_name:
        return jsonify({"error": "未提供服务器名称"}), 400

    server_dir = os.path.join(VERSIONS_DIR, server_name)

    if server_name in running_servers and running_servers[server_name].poll() is None:
        return jsonify({"error": "服务器正在运行中，请先停止后再删除！"}), 400

    if not os.path.exists(server_dir):
        return jsonify({"error": "找不到该服务器文件夹"}), 404

    try:
        shutil.rmtree(server_dir)
        if server_name in running_servers:
            del running_servers[server_name]
        if server_name in auto_backup_config:
            del auto_backup_config[server_name]
        return jsonify({"message": f"服务器 [{server_name}] 已删除！"})
    except Exception as e:
        return jsonify({"error": f"删除失败: {str(e)}"}), 500


if __name__ == '__main__':
    url = "http://127.0.0.1:5000"
    print(f"Minecraft Fabric 面板启动中: {url}")
    threading.Thread(target=auto_backup_task, daemon=True).start()
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host='127.0.0.1', port=5000, debug=False)