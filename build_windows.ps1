# Build script for Desktop Lens Windows executable
# Prerequisites:
#   - Python 3.x installed
#   - GTK3 runtime installed (MSYS2 or official GTK for Windows)
#   - GStreamer installed (https://gstreamer.freedesktop.org/download/)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Desktop Lens Windows Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.x from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Python dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller desktop-lens.spec --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The executable can be found in: dist\DesktopLens\DesktopLens.exe" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
