@echo off
title MPESB Patwari CBT Examination Simulator
cd /d "%~dp0"
echo =======================================================
echo   MPESB Patwari CBT Examination Simulator (Windows)
echo =======================================================
echo Launching application...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
