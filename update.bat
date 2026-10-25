@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Updating Dalamud merged plugin repo ===
where python >nul 2>nul
if %errorlevel%==0 (
    python update.py %*
) else (
    py -3 update.py %*
)
echo.
echo === Done (exit code %errorlevel%) ===
pause
