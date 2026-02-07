# desktop-lens
A Python/GStreamer tool to correct TV overscan by creating a resizable, hardware-accelerated viewport mirror of your desktop.

**Now with Windows support!** 🎉

## Platform Support
- **Linux**: Native support with X11 (ximagesrc)
- **Windows**: Screen capture via GStreamer DirectShow plugins
- macOS: Not yet supported (contributions welcome!)

## Features
- Cross-platform screen capture (X11 on Linux, DirectShow on Windows)
- Hardware-accelerated scaling (VAAPI/OpenGL/DirectX) with software fallback
- GStreamer pipeline with platform-specific capture sources
- Borderless, always-on-top GTK3 window
- Dynamic scale adjustment via slider (0.7x to 1.0x)
- **Configurable margins** to compensate for TV overscan (default: 100px all sides)
- **16:9 aspect ratio** maintained automatically
- **Global hotkeys** for ghost mode and visibility toggle
- **Keyboard shortcuts** for fine-tuning viewport position
- JSON persistence for window position, scale factor, and margins
- Graceful GStreamer shutdown with proper resource cleanup
- Bus monitoring for error handling and UI responsiveness

## Requirements
- Python 3
- GStreamer 1.0 and plugins
- GTK 3
- PyGObject

## Installation

### Linux (Debian/Ubuntu)
```bash
# Install system dependencies
sudo apt-get install python3 python3-pip gstreamer1.0-tools \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  gir1.2-gtk-3.0 gir1.2-gstreamer-1.0

# Optional: Hardware acceleration support
# For VAAPI (Intel/AMD GPUs):
sudo apt-get install gstreamer1.0-vaapi libva2

# For OpenGL (NVIDIA/Mesa):
sudo apt-get install gstreamer1.0-gl

# Install Python dependencies
pip3 install -r requirements.txt
```

### Windows

See the detailed [Windows Installation Guide](WINDOWS_INSTALL.md) for complete instructions.

**Quick start:**
1. Install Python 3.x from [python.org](https://www.python.org/)
2. Install GTK3 runtime (via MSYS2 or official installer)
3. Install GStreamer from [gstreamer.freedesktop.org](https://gstreamer.freedesktop.org/download/)
4. Run: `pip install -r requirements.txt`
5. Run: `python desktop-lens.py`

Or build a Windows executable:
```bash
# Run the build script
build_windows.bat

# Executable will be at: dist\DesktopLens\DesktopLens.exe
```


## Usage
```bash
./desktop-lens.py
```

Configuration is automatically saved to `~/.config/desktop-lens.json` and includes:
- Window X/Y position
- Scale factor (0.7-1.0)
- Margin settings (top, bottom, left, right) - default 100px each

## Performance
The application automatically detects and uses hardware acceleration when available:
- **VAAPI** (Intel/AMD GPUs): 70-90% CPU reduction vs software
- **OpenGL** (NVIDIA/Mesa): 60-80% CPU reduction vs software
- **Software fallback**: Optimized bilinear scaling for legacy systems

See [PERFORMANCE_AUDIT.md](PERFORMANCE_AUDIT.md) for detailed performance analysis.

## Controls
- **Scale slider**: Adjust the desktop scale (0.7x to 1.0x)
- **Freeze button** (or **Space key**): Snapshot the current desktop view and freeze it (useful for aligning margins without the hall of mirrors effect)
- **Hide Window button**: Temporarily hide the window for 5 seconds (allows capturing without self-recursion)
- **Crop button**: Toggle region cropping to limit capture to primary monitor only (prevents hall of mirrors on multi-monitor setups)
- **Drag window**: Reposition the window
- **Ctrl + Arrow Keys**: Adjust top/left margins by ±5px
  - `Ctrl+Up`: Decrease top margin (viewport moves up)
  - `Ctrl+Down`: Increase top margin (viewport moves down)
  - `Ctrl+Left`: Decrease left margin (viewport moves left)
  - `Ctrl+Right`: Increase left margin (viewport moves right)
- **Shift + Arrow Keys**: Adjust bottom/right margins by ±5px
  - `Shift+Up`: Decrease bottom margin (more space at bottom)
  - `Shift+Down`: Increase bottom margin (less space at bottom)
  - `Shift+Left`: Decrease right margin (more space at right)
  - `Shift+Right`: Increase right margin (less space at right)
- **Close window**: Save settings and exit

## Hall of Mirrors Prevention
The application provides multiple automatic and manual ways to prevent the "hall of mirrors" effect (when the application captures itself):

**Automatic Prevention:**
1. **XID Exclusion** (Linux only): The application automatically sets its window ID (XID) on ximagesrc to exclude itself from capture
2. **Opacity Fallback** (Linux/Windows): If XID exclusion is not supported, the window automatically becomes nearly transparent (opacity 0.001) during frame capture, then restores to full opacity

**Manual Controls:**
1. **Freeze button/Space key**: Snapshot the desktop and pause updates, allowing you to adjust margins without recursion
2. **Hide Window button**: Temporarily hide the application window for 5 seconds
3. **Crop Region button** (Linux only): Limit capture to the primary monitor area, useful for multi-monitor setups

## Platform-Specific Notes

### Linux
- Uses `ximagesrc` for X11 screen capture
- Supports hardware acceleration via VAAPI and OpenGL
- XID-based window exclusion prevents capturing itself
- Region cropping available for multi-monitor setups

### Windows
- Uses `gdiscreencapsrc`, `dx9screencapsrc`, or `d3d11screencapturesrc` (automatically detected)
- Configuration stored in `%APPDATA%\Local\desktop-lens.json`
- Uses opacity-based approach for hall of mirrors prevention (XID not available on Windows)
- See [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md) for detailed installation instructions

## Overscan Correction
The viewport is automatically centered with configurable margins to compensate for TV overscan. The default margins are 100px on all sides, but can be adjusted using keyboard shortcuts to perfectly align the viewport with your TV's visible area. The aspect ratio is maintained at 16:9 to prevent UI distortion.

See [OVERSCAN_GUIDE.md](OVERSCAN_GUIDE.md) for detailed setup instructions and troubleshooting.
