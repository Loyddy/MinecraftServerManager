# Minecraft Fabric Server Manager

A lightweight Minecraft Fabric server management panel built with Python Flask and Tailwind CSS...

---

# 📖 Part 1 — Project Overview

## ✨ Features

### 🚀 One-Click Deployment
...

### 🖥️ Multi-Instance Management
...

### 💾 Dynamic Memory Configuration
...

### 📜 Real-Time Console
...

### 📊 Performance Monitoring
...

### 🧩 Mod Manager
...

### 💾 Backup System
...

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

> **Note**
>
> The `Versions` and `backups` directories are created automatically after the first successful launch.

---

## Step 2 — Install Dependencies

Open a terminal inside the `Assistant` directory.

```bash
cd Assistant
```

Install the required Python packages.

```bash
pip install -r requirements.txt
```

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

---

## Step 4 — Deploy a Fabric Server

1. Open **Deploy Fabric Server**
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
