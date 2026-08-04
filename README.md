# Minecraft Server Manager

A lightweight Minecraft server management panel built with Python Flask and Tailwind CSS...

---

# 📖 Part 1 — Project Overview

## ✨ Features

### 🚀 One-Click Fabric Deployment
- Automatically fetch the latest official Fabric version list.
- Download the Fabric Installer with a single click.
- Generate all required server files automatically.
- Accept the Minecraft EULA automatically during deployment.

### 🖥️ Multi-Instance Management
- Create and manage multiple Fabric server instances independently.
- Start, stop, or delete any server with one click.
- Keep different Minecraft versions separated and organized.

### 💾 Dynamic Memory Configuration
- Adjust Java memory allocation (`-Xms` / `-Xmx`) directly from the web interface.
- Visual memory slider for quick and convenient configuration.
- No manual editing of startup scripts required.

### 📜 Real-Time Console
- Stream server logs in real time.
- Send console commands instantly, including:
  - `say`
  - `op`
  - `stop`
  - `whitelist`
  - and any other Minecraft server command.

### 📊 Performance Monitoring
Monitor server status in real time, including:

- CPU usage
- Memory usage (MB)
- Online player count
- Online player list

### 🧩 Mod Manager
Manage Fabric Mods directly from the browser.

- Drag & drop `.jar` files to upload
- Click-to-upload support
- One-click enable/disable Mods
- Disabled Mods are automatically renamed with the `.disabled` extension

### 💾 Backup System
Protect your worlds with automatic and manual backups.

- One-click manual world backup
- Automatic scheduled backups running in the background
- Configurable global backup interval
- Automatic cleanup keeps only the two most recent backups for each server instance to save disk space

---

## 📁 Project Structure

```text
Root-Directory/
│
├── Assistant/
│   ├── main.py
│   ├── config.json
│   └── index.html
│
├── Versions/
│   ├── [version]_fabric/
│   │   ├── eula.txt
│   │   ├── fabric-installer.jar
│   │   ├── fabric-server-launch.jar
│   │   ├── start.bat
│   │   ├── world/
│   │   ├── logs/
│   │   └── mods/
│   │
│   └── ...
│
└── backups/
    ├── [version]_fabric/
    │   ├── world_auto_YYYYMMDD_HHMMSS.zip
    │   └── world_YYYYMMDD_HHMMSS.zip
    │
    └── ...
```

### Directory Description

| Directory | Description |
|------------|-------------|
| `Assistant/` | Backend application, configuration, and frontend page |
| `Versions/` | Automatically generated Fabric server instances |
| `backups/` | Automatically generated world backup archives |

---

# 🚀 Part 2 — Getting Started

## Requirements

- Python 3.7+
- Java Runtime Environment (JRE/JDK)
- Java 17 or Java 21 recommended for Minecraft 1.20+

---

## Step 1 — Prepare the Project

When you first download the project, only the following folder is required:

```text
Root-Directory/
│
└── Assistant/
    ├── main.py
    ├── config.json
    └── index.html
```
<img width="1403" height="379" alt="image" src="https://github.com/user-attachments/assets/761fdcf1-d589-4c89-accb-5e5815e5346d" />


> **Note**
>
> The `Versions` and `backups` directories are created automatically after the first successful launch.

---

## Step 2 — Install Dependencies

Enter the `Assistant` directory.

Install the required Python packages in the termial(should be in the same file as main.py).
<img width="1425" height="883" alt="image" src="https://github.com/user-attachments/assets/6e009074-5a30-4141-85ec-4b3fa21aeceb" />

```bash
pip install Flask==2.3.3 requests==2.31.0 psutil==5.9.5 Werkzeug==2.3.7
```
<img width="2030" height="430" alt="image" src="https://github.com/user-attachments/assets/a2e1359c-0971-4a0b-acb9-70c543f0920c" />

---

## Step 3 — Launch the Application

Run the backend.

```bash
python main.py
```

or simply run `main.py` using your preferred Python IDE.

After a few seconds, your default browser will automatically open:

```text
http://localhost:5000
```
The page should be look like this👇👇👇
<img width="1797" height="1511" alt="image" src="https://github.com/user-attachments/assets/77265c05-2783-4bf5-984a-44bcc03c9b2b" />


---

## Step 4 — Deploy a Fabric Server

1. Look at **Deploy Fabric Server**
2. Select the Minecraft version.
3. Click **One-Click Download & Build**.
4. Wait for deployment to finish.

The application will automatically:

- Download the Fabric Installer
- Generate startup files
- Accept the EULA
- Create the server instance

---

## Step 5 — Manage Your Server

After deployment, you can manage the server directly from the web dashboard.

- ▶ Start / Stop Server
- 🗑 Delete Server
- 💾 Configure Memory
- 📜 Live Console
- ⌨ Execute Commands
- 📊 Monitor CPU & RAM
- 👥 View Online Players
- 🧩 Upload Mods
- 🔄 Enable / Disable Mods
- 💾 Manual Backup
- ⏰ Automatic Backup

---

# ❤️ Built With

- **Python**
- **Flask**
- **Tailwind CSS**
- **Minecraft Fabric**

---

# 📄 License

This project is intended for learning and personal server management.

Feel free to modify and extend it for your own use.
