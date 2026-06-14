@echo off
REM ─── SysOptimizer Build Script ───────────────────────────────────────────────
REM Run this from the folder containing optimizer.py
REM Requirements: Python 3.10+, pip

echo [1/3] Installing dependencies...
pip install psutil customtkinter pyinstaller --quiet

echo [2/3] Building executable...
pyinstaller optimizer.spec --clean --noconfirm

echo [3/3] Done!
echo.
echo Output: dist\SysOptimizer.exe
echo.
echo NOTE: If you want administrator access (to kill system processes),
echo       edit optimizer.spec and set:  uac_admin=True
echo       then rebuild.
pause
