# Windows Quick Start Guide

Get Desktop Lens running on Windows in 5 minutes!

## Option 1: Run from Source (Quickest)

### Prerequisites
1. **Python 3.x** - [Download](https://www.python.org/downloads/)
2. **GTK3 Runtime** - [Download MSYS2](https://www.msys2.org/)
   ```bash
   # In MSYS2 terminal:
   pacman -S mingw-w64-ucrt-x86_64-gtk3 mingw-w64-ucrt-x86_64-python-gobject
   ```
3. **GStreamer** - [Download](https://gstreamer.freedesktop.org/download/)
   - Install "Complete" version

### Run the Application
```bash
git clone https://github.com/SaltProphet/desktop-lens.git
cd desktop-lens
pip install -r requirements.txt
python desktop-lens.py
```

## Option 2: Build Windows Executable

### Build Steps
```bash
# Clone the repository
git clone https://github.com/SaltProphet/desktop-lens.git
cd desktop-lens

# Run build script
build_windows.bat

# Executable will be at:
# dist\DesktopLens\DesktopLens.exe
```

## Option 3: Download Pre-built Executable

Check the [Releases](https://github.com/SaltProphet/desktop-lens/releases) page for pre-built executables.

**Note:** GTK3 and GStreamer must still be installed on your system.

## Controls

- **Space**: Freeze/unfreeze display
- **Ctrl+Alt+H**: Hide/show window
- **Ctrl+Alt+G**: Toggle ghost mode (click-through)
- **Ctrl + Arrow Keys**: Adjust top/left margins
- **Shift + Arrow Keys**: Adjust bottom/right margins

## Troubleshooting

### "Python not found"
Install Python from https://www.python.org/ and check "Add to PATH"

### "GTK not found"
Install GTK3 runtime and add to PATH

### "Failed to create Windows screen capture element"
Install GStreamer with "Complete" option from https://gstreamer.freedesktop.org/download/

### Hall of Mirrors Effect
Press **Space** to freeze the display while adjusting settings

## Need Help?

- Full Installation Guide: [WINDOWS_INSTALL.md](WINDOWS_INSTALL.md)
- Build Guide: [WINDOWS_BUILD.md](WINDOWS_BUILD.md)
- General Docs: [README.md](README.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an Issue: [GitHub Issues](https://github.com/SaltProphet/desktop-lens/issues)
