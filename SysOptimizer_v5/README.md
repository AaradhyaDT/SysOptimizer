# ⚡ SysOptimizer v4

A **CPU / RAM / Disk optimizer and task manager** for Windows (Acer SFG16 / Intel, but works on any Windows 11 PC).  
Built with Python + CustomTkinter + psutil. Runs as a single `.exe`.

---

## What's New in v4

| Change | Detail |
|---|---|
| 🚀 **Optimizer tab** | Brand-new tab with real optimization features |
| ⚡ **Power Plan switcher** | Silent / Balanced / High Performance — one click |
| 🧹 **RAM Flush** | Trims working sets of all user processes; recovers idle RAM |
| 🚫 **Bloat Disabler** | Toggle Intel Killer, Phone Link, Search Indexer, QuickPanel, etc. |
| 🚀 **Startup Manager** | Scans registry + startup folders; shows all auto-start entries |
| 🎨 **Light mode fixed** | No more flash/rebuild on theme toggle |
| 📊 **Columns centered** | PID, CPU%, Memory, Status, User now properly centered |
| 🔧 **Zoom fixed** | Zoom frame and buttons fully repaint on theme/zoom change |

---

## Features

| Feature | Detail |
|---|---|
| Live CPU & RAM meters | Animated ring gauges with 60-second sparkline history |
| Disk usage | Per-partition usage bars for all mounted drives |
| Process table | All running processes with CPU %, Memory, Status, User |
| Kill tasks | Select any process and kill it (system processes are protected) |
| Kill High-CPU | One-click kill all user processes above 25% CPU |
| Empty Recycle Bin | Direct call via PowerShell |
| Export Report | Saves a detailed `.txt` report to your Desktop |
| Auto-refresh | Metrics every 2s · Process list every 5s |
| Filter | Real-time name filter in the process table |
| Sort | Click any column header to sort ascending/descending |
| **Power Plan** | Switch between Silent, Balanced, High Performance |
| **RAM Flush** | EmptyWorkingSet on all user processes (Admin recommended) |
| **Bloat Toggle** | Enable/disable Killer suite, Intel DSA, Phone Link, Search, QuickPanel, etc. |
| **Startup Scanner** | See everything that auto-launches at login |

---

## Optimizer Tab — Bloat List

The following are toggle-able. All can be re-enabled at any time:

| Item | What it is |
|---|---|
| Killer Network Service | Intel Killer network QoS |
| Killer Analytics Service | Killer telemetry |
| Killer APS | Killer app scheduler (delayed start) |
| Intel Driver & Support Asst. | Background driver updater |
| Phone Link / Mobile | Microsoft phone mirroring |
| Search Indexer (WSearch) | High disk I/O indexing service |
| Xbox Game Bar | Xbox save sync |
| AcerSense Helper | AcerSense background task |
| QuickPanel / OSD | Acer overlay services |

> **Note:** AcerSense itself (for fan control: Silent/Normal/Performance) is listed but recommended to keep enabled unless you manage power plans directly.

---

## How to Build the `.exe`

### Prerequisites
- Python 3.10 or newer
- pip

### Steps

```bat
cd SysOptimizer_v4
build.bat
```

Output: `dist\SysOptimizer.exe`

---

## Running as Administrator (recommended)

For RAM flush, service toggling, and killing system-level processes:  
Right-click `SysOptimizer.exe` → **Run as administrator**

Or set `uac_admin=True` in `optimizer.spec` and rebuild.

---

## Manual run (without compiling)

```bat
pip install psutil customtkinter
python optimizer.py
```

---

## Protected processes

Never killable through the UI:
- Core Windows: `svchost.exe`, `csrss.exe`, `lsass.exe`, `winlogon.exe`, etc.
- Desktop shell: `explorer.exe`, `dwm.exe`
- Security: `msmpeng.exe` (Windows Defender)
- The optimizer process itself

---

## File structure

```
SysOptimizer_v4/
├── optimizer.py       ← Main app (all-in-one, v4)
├── optimizer.spec     ← PyInstaller build config
├── build.bat          ← One-click build script
└── README.md
```

---

## v5 Changes
- **Default theme**: Light (elegant minimalist palette — clean whites, soft blues)
- **Default font**: 20pt
- **Default page**: Optimizer tab
- **New power plan**: 🚀 Ultimate Performance (Chris Titus Tools) — eliminates CPU micro-throttling
- **Performance**: Graphs use `after_idle` deferred rendering (no redundant redraws)
- **Performance**: Perf graphs only update when Performance tab is active
- **Performance**: Disk sidebar only updates when Processes tab is visible
- **Performance**: Poll intervals tuned (perf: 2.5s, procs: 6s) to reduce UI jank
- **Scrolling**: Root-level MouseWheel binding for smooth scroll in all frames
