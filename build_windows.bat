@echo off
REM Build script for Desktop Lens Windows executable
REM Prerequisites:
REM   - Python 3.x installed
REM   - GTK3 runtime installed (MSYS2 or official GTK for Windows)
REM   - GStreamer installed (https://gstreamer.freedesktop.org/download/)

echo ========================================
echo Desktop Lens Windows Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.x from https://www.python.org/
    pause
    exit /b 1
)

echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Building executable with PyInstaller...
pyinstaller desktop-lens.spec --clean
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable can be found in: dist\DesktopLens\DesktopLens.exe
echo.
pause
