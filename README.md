# SysOptimizer

A lightweight Windows CPU / RAM / Disk optimizer and task manager built with Python, CustomTkinter, and psutil.

## What this repository contains

- `SysOptimizer_v4/`, `SysOptimizer_v5/`, `SysOptimizer_v6/` — source and build artifacts for different versions
- `LICENSE` — project license
- `graphify-out/` — generated code analysis and graph metadata

## Overview

SysOptimizer is a single-window utility that displays live CPU, memory, and disk metrics while letting users manage running processes. It includes process filtering, sorting, high-CPU kill actions, Recycle Bin cleanup, and an exportable report.

## Build and run

### Run the latest source version

1. Open PowerShell.
2. Install dependencies:

```powershell
pip install psutil customtkinter
```

3. Run the app:

```powershell
python SysOptimizer_v6\optimizer.py
```

### Build an executable

```powershell
cd SysOptimizer_v6
build.bat
```

The compiled executable appears under `SysOptimizer_v6\dist\SysOptimizer.exe`.

## Notes

- `graphify-out/` is generated analysis metadata and should not be committed.
- Build directories such as `build/`, `dist/`, and `.spec` files are ignored by the included `.gitignore`.
- The repo currently includes multiple version folders; `SysOptimizer_v6` is the newest source tree.

## Recommended files

- `SysOptimizer_v6\optimizer.py` — current application source
- `SysOptimizer_v6\optimizer.spec` — PyInstaller config
- `SysOptimizer_v6\build.bat` — compile script

## License

This repository includes the existing `LICENSE` file from upstream.