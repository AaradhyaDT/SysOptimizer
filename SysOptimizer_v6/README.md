# ⚡ SysOptimizer

A lightweight **CPU / RAM / Disk optimizer and task manager** for Windows.  
Built with Python + CustomTkinter + psutil. Runs as a single `.exe`.

---

## Features

| Feature | Detail |
|---|---|
| Live CPU & RAM meters | Animated ring gauges with 60-second sparkline history |
| Disk usage | Per-partition usage bars for all mounted drives |
| Process table | All running processes with CPU %, Memory, Status, User |
| Kill tasks | Select any process and kill it (system processes are protected) |
| Kill High-CPU | One-click kill all user processes above 30% CPU |
| Empty Recycle Bin | Direct call via PowerShell |
| Export Report | Saves a detailed `.txt` report to your Desktop |
| Auto-refresh | Metrics every 2s · Process list every 5s |
| Filter | Real-time name filter in the process table |
| Sort | Click any column header to sort ascending/descending |

---

## How to Build the `.exe`

### Prerequisites
- Python 3.10 or newer  
- pip

### Steps

```bat
cd SysOptimizer
build.bat
```

The compiled executable will be at:
```
dist\SysOptimizer.exe
```

Single file, no installation required. Copy it anywhere.

---

## Running as Administrator (recommended)

To kill system-level processes, right-click `SysOptimizer.exe` → **Run as administrator**.

Or edit `optimizer.spec`, set `uac_admin=True`, and rebuild — it will auto-prompt for elevation on launch.

---

## Manual run (without compiling)

```bat
pip install psutil customtkinter
python optimizer.py
```

---

## Protected processes

The following process categories are **never killable** through the UI (safety guard):

- Core Windows services: `svchost.exe`, `csrss.exe`, `lsass.exe`, `winlogon.exe`, etc.
- Desktop shell: `explorer.exe`, `dwm.exe`
- Security: `msmpeng.exe` (Windows Defender)
- The optimizer process itself

---

## File structure

```
SysOptimizer/
├── optimizer.py      ← Main app (all-in-one)
├── optimizer.spec    ← PyInstaller build config
├── build.bat         ← One-click build script
└── README.md
```
