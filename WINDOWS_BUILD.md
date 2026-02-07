# Windows Build and Distribution Guide

This document provides guidance for building and distributing Desktop Lens on Windows.

## Build Environment Setup

### Required Software

1. **Python 3.10+**
   - Download from https://www.python.org/downloads/
   - Add to PATH during installation

2. **GTK3 Runtime for Windows**
   
   **Option A: MSYS2 (Recommended for development)**
   ```bash
   # Install MSYS2 from https://www.msys2.org/
   # Then run in MSYS2 UCRT64 terminal:
   pacman -S mingw-w64-ucrt-x86_64-gtk3
   pacman -S mingw-w64-ucrt-x86_64-python-gobject
   pacman -S mingw-w64-ucrt-x86_64-gstreamer
   pacman -S mingw-w64-ucrt-x86_64-gst-plugins-base
   pacman -S mingw-w64-ucrt-x86_64-gst-plugins-good
   pacman -S mingw-w64-ucrt-x86_64-gst-plugins-bad
   ```

   **Option B: Official GTK Installer**
   - Download from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
   - Install to default location
   - Add bin directory to PATH

3. **GStreamer for Windows**
   - Download both runtime and development installers from:
     https://gstreamer.freedesktop.org/download/
   - Install with "Complete" installation option
   - Add bin directory to PATH (e.g., `C:\gstreamer\1.0\msvc_x86_64\bin`)

### Build Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/SaltProphet/desktop-lens.git
   cd desktop-lens
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the application**
   ```bash
   python desktop-lens.py
   ```
   Verify it works before building the executable.

4. **Build the executable**
   ```bash
   # Using batch file:
   build_windows.bat
   
   # Or using PowerShell:
   .\build_windows.ps1
   
   # Or manually:
   pyinstaller desktop-lens.spec --clean
   ```

5. **Test the executable**
   ```bash
   dist\DesktopLens\DesktopLens.exe
   ```

## Distribution

### Option 1: Distribute Folder

The simplest option is to distribute the entire `dist\DesktopLens` folder:

1. Zip the `dist\DesktopLens` folder
2. Include installation instructions for GTK3 and GStreamer
3. Users extract and run `DesktopLens.exe`

**Pros:** Simple, small download
**Cons:** Requires users to install GTK3 and GStreamer

### Option 2: Installer with Dependencies

Create an installer that bundles GTK3 and GStreamer:

1. **Using Inno Setup:**
   - Download Inno Setup from https://jrsoftware.org/isinfo.php
   - Create a setup script that:
     - Installs DesktopLens.exe
     - Checks for/installs GTK3 runtime
     - Checks for/installs GStreamer runtime
     - Creates shortcuts

2. **Using WiX Toolset:**
   - More complex but creates professional MSI installers
   - Can include GTK3/GStreamer in the installer

**Pros:** Professional, user-friendly
**Cons:** Larger download, more complex to create

### Option 3: Portable Executable with Bundled DLLs

Bundle all required DLLs with the executable:

1. Copy necessary GTK3 DLLs to the `dist\DesktopLens` folder
2. Copy necessary GStreamer DLLs and plugins
3. Create a truly portable application

This requires manually identifying and copying DLLs:
- From GTK3: libgtk-3-0.dll, libgdk-3-0.dll, libgio-2.0-0.dll, etc.
- From GStreamer: All necessary GStreamer DLLs and plugins

**Pros:** Truly portable, no installation required
**Cons:** Very large (200-500MB), complex to maintain

## Recommended Distribution Method

For most users, **Option 1** (folder distribution) is recommended:

1. Build the executable
2. Zip the `dist\DesktopLens` folder
3. Upload to GitHub Releases
4. Link to the WINDOWS_INSTALL.md guide for prerequisite installation

## GitHub Release Checklist

When creating a new release:

1. **Version the release** (e.g., v1.0.0-windows)
2. **Include:**
   - `DesktopLens-windows-{version}.zip` (the built executable folder)
   - Release notes with changes
   - Link to WINDOWS_INSTALL.md
3. **In release notes, include:**
   - Prerequisites (GTK3, GStreamer)
   - Download links for prerequisites
   - Quick start instructions
   - Known limitations on Windows

## Testing Checklist

Before releasing:

- [ ] Test on clean Windows installation
- [ ] Verify GTK3 detection
- [ ] Verify GStreamer screen capture works
- [ ] Test all hotkeys (Ctrl+Alt+G, Ctrl+Alt+H)
- [ ] Test freeze/hide/scale functions
- [ ] Verify config file saves/loads correctly
- [ ] Test window dragging and repositioning
- [ ] Verify icon displays correctly
- [ ] Check for any console errors or warnings

## Troubleshooting Build Issues

### "Failed to create Windows screen capture element"
- GStreamer not installed or not in PATH
- Solution: Reinstall GStreamer with Complete option

### "ImportError: gi module not found"
- PyGObject not installed correctly
- Solution: `pip install pygobject`

### "GTK+ runtime not found"
- GTK3 not installed or not in PATH
- Solution: Install GTK3 runtime and add to PATH

### Icon not appearing in executable
- Icon path incorrect in spec file
- Solution: Verify `assets/icon.ico` exists and spec file path is correct

## Automation

Consider setting up GitHub Actions for automated Windows builds:

```yaml
name: Build Windows Executable

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          # Install GTK3 and GStreamer
          # Install Python deps
          pip install -r requirements.txt
      - name: Build executable
        run: pyinstaller desktop-lens.spec --clean
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: DesktopLens-Windows
          path: dist/DesktopLens/
```

Note: This is a simplified example. You'll need to add proper GTK3/GStreamer installation steps.
