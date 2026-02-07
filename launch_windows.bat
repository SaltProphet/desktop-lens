@echo off
REM Desktop Lens Launcher for Windows
REM This script checks for prerequisites before launching

echo ========================================
echo Desktop Lens Launcher
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check GStreamer
gst-inspect-1.0 --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: GStreamer not found or not in PATH
    echo Desktop Lens requires GStreamer for screen capture.
    echo Download from: https://gstreamer.freedesktop.org/download/
    echo.
    pause
)

REM Launch application
echo Starting Desktop Lens...
echo.
python desktop-lens.py
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    echo Check the error message above for details.
    echo.
    pause
)
