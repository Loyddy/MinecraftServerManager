import os
import json
import re
from config import CONFIG_FILE, BACKUPS_DIR, VERSIONS_DIR


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get('backup_interval_minutes', 30)
        except Exception:
            pass
    return 30


def save_config(minutes):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({'backup_interval_minutes': minutes}, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Config Save Failed]: {e}")


def clean_old_backups(server_name, max_keep=2):
    server_backup_dir = os.path.join(BACKUPS_DIR, server_name)
    if not os.path.exists(server_backup_dir):
        return
    zips = [os.path.join(server_backup_dir, f) for f in os.listdir(server_backup_dir) if f.endswith('.zip')]
    zips.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    if len(zips) > max_keep:
        for f in zips[max_keep:]:
            try:
                os.remove(f)
            except Exception:
                pass


def get_server_memory(server_name):
    bat_path = os.path.join(VERSIONS_DIR, server_name, 'start.bat')
    if not os.path.exists(bat_path):
        return 2
    try:
        with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
            m = re.search(r'-Xmx(\d+)G', f.read(), re.IGNORECASE)
            if m:
                return int(m.group(1))
    except Exception:
        pass
    return 2


def get_prop_val(server_name, key, default):
    prop_path = os.path.join(VERSIONS_DIR, server_name, 'server.properties')
    if not os.path.exists(prop_path):
        return default
    try:
        with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if line.startswith(f"{key}="):
                    val = line.split('=', 1)[1]
                    if val.lower() == 'true':
                        return True
                    if val.lower() == 'false':
                        return False
                    try:
                        return int(val)
                    except ValueError:
                        return val
    except Exception:
        pass
    return default


def set_prop_val(server_name, key, value):
    server_dir = os.path.join(VERSIONS_DIR, server_name)
    if not os.path.exists(server_dir):
        os.makedirs(server_dir, exist_ok=True)

    prop_path = os.path.join(server_dir, 'server.properties')
    lines = []

    if os.path.exists(prop_path):
        try:
            with open(prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            lines = []

    str_value = str(value).lower() if isinstance(value, bool) else str(value)
    found = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('#') and stripped.startswith(f"{key}="):
            new_lines.append(f"{key}={str_value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines.append(f"{key}={str_value}\n")

    try:
        with open(prop_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"[Set Prop Error]: {e}")
        return False