@echo off
REM ============================================================
REM  Build ArgoCD Log Analyzer into a single .exe
REM ============================================================

echo [1/3] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/3] Building argo-log-analyzer.exe ...
pyinstaller --onefile --name argo-log-analyzer --clean main.py

echo.
echo [3/3] Copying .env.example to dist folder...
copy .env.example dist\.env.example

echo.
echo ============================================================
echo  BUILD COMPLETE!
echo  Output: dist\argo-log-analyzer.exe
echo.
echo  Share these 2 files with your team:
echo    1. dist\argo-log-analyzer.exe
echo    2. dist\.env.example  (they rename to .env and add their key)
echo ============================================================
pause
