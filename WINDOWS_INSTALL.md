# Windows Installation Guide

This guide will help you install and run Desktop Lens on Windows.

## Prerequisites

Desktop Lens requires the following components to be installed on your Windows system:

### 1. Python 3.x

Download and install Python from [python.org](https://www.python.org/downloads/)

- During installation, make sure to check "Add Python to PATH"
- Recommended: Python 3.10 or newer

### 2. GTK3 Runtime

GTK3 is required for the graphical interface. You have two options:

#### Option A: MSYS2 (Recommended)

1. Download and install MSYS2 from [msys2.org](https://www.msys2.org/)
2. Open MSYS2 UCRT64 terminal
3. Run: `pacman -S mingw-w64-ucrt-x86_64-gtk3 mingw-w64-ucrt-x86_64-python-gobject`

#### Option B: Official GTK for Windows

1. Download GTK3 runtime from [gtk.org](https://www.gtk.org/docs/installations/windows/)
2. Install and add GTK's bin directory to your system PATH

### 3. GStreamer

GStreamer is required for screen capture and video processing.

1. Download GStreamer from [gstreamer.freedesktop.org](https://gstreamer.freedesktop.org/download/)
2. Install both:
   - **gstreamer-1.0-msvc-x86_64-{version}.msi** (runtime)
   - **gstreamer-1.0-devel-msvc-x86_64-{version}.msi** (development files)
3. During installation, select "Complete" installation type to get all plugins
4. Add GStreamer's bin directory to your system PATH (usually `C:\gstreamer\1.0\msvc_x86_64\bin`)

### 4. Verify Installation

Open Command Prompt or PowerShell and verify installations:

```bash
python --version
gst-inspect-1.0 --version
```

## Installation Methods

### Method 1: Run from Source (Development)

1. Clone or download this repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python desktop-lens.py
   ```

### Method 2: Build Windows Executable

If you want to create a standalone `.exe` file:

1. Clone or download this repository
2. Run the build script:
   ```bash
   # Using Command Prompt
   build_windows.bat
   
   # Or using PowerShell
   .\build_windows.ps1
   ```
3. The executable will be created in `dist\DesktopLens\DesktopLens.exe`
4. You can copy the entire `dist\DesktopLens` folder to any location

**Note:** The built executable still requires GTK3 and GStreamer to be installed on the system.

### Method 3: Pre-built Executable (If Available)

Check the [Releases](https://github.com/SaltProphet/desktop-lens/releases) page for pre-built Windows executables.

## Configuration

Configuration is stored in:
- `%APPDATA%\Local\desktop-lens.json`

This file stores:
- Window position
- Scale settings
- Margin settings

## Known Windows Limitations

1. **Screen Capture Source**: Windows uses `gdiscreencapsrc`, `dx9screencapsrc`, or `d3d11screencapturesrc` instead of Linux's `ximagesrc`
2. **XID Exclusion**: The XID-based window exclusion feature (used on Linux to prevent hall of mirrors) is not available on Windows. The app automatically uses opacity fallback method.
3. **Global Hotkeys**: Should work the same as on Linux (Ctrl+Alt+G for ghost mode, Ctrl+Alt+H for visibility)

## Troubleshooting

### Application won't start

1. Verify all prerequisites are installed
2. Check that GTK3 and GStreamer bin directories are in your PATH
3. Try running from command line to see error messages:
   ```bash
   python desktop-lens.py
   ```

### "Failed to create Windows screen capture element" error

This means GStreamer screen capture plugins are not found:
1. Reinstall GStreamer with "Complete" installation
2. Ensure GStreamer's bin directory is in PATH
3. Try: `gst-inspect-1.0 gdiscreencapsrc` to check if plugin is available

### Hall of mirrors effect

On Windows, the application uses an opacity-based approach to prevent capturing itself:
1. Try using the **Freeze** button (or Space key) to pause updates while adjusting
2. Use the **Hide Window** button to temporarily hide the window
3. This is a known limitation of Windows screen capture

### Performance issues

Windows screen capture may have different performance characteristics:
1. Try different screen capture sources (the app will try them automatically)
2. Reduce the scale factor for better performance
3. Close unnecessary applications

## Building a Fully Portable Executable

To create a truly portable executable that includes GTK3 and GStreamer:

1. This requires advanced packaging with tools like:
   - WiX Toolset for MSI installer
   - Inno Setup for custom installer
   - Manual bundling of GTK3/GStreamer DLLs

2. This is beyond the scope of the basic PyInstaller build but can be done if needed.

## Support

For issues specific to Windows support, please open an issue on GitHub with:
- Windows version
- Python version
- GTK version
- GStreamer version
- Complete error messages
