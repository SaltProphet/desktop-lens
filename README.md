# desktop-lens
A Python/GStreamer tool to correct TV overscan by creating a resizable, hardware-accelerated viewport mirror of the Linux desktop.

## Features
- Captures the root X11 window using ximagesrc
- Hardware-accelerated scaling (VAAPI/OpenGL) with software fallback
- GStreamer pipeline: ximagesrc → (hw-accelerated scaling) → appsink
- Borderless, always-on-top GTK3 window
- Dynamic scale adjustment via slider (0.7x to 1.0x)
- **Configurable margins** to compensate for TV overscan (default: 100px all sides)
- **16:9 aspect ratio** maintained automatically
- **Keyboard shortcuts** for fine-tuning viewport position
- JSON persistence for window position, scale factor, and margins
- Graceful GStreamer shutdown with proper resource cleanup
- Bus monitoring for error handling and UI responsiveness

## Requirements
- Python 3
- GStreamer 1.0 and plugins (gstreamer1.0-plugins-base, gstreamer1.0-plugins-good)
- GTK 3
- PyGObject

## Installation
```bash
# Install system dependencies (Debian/Ubuntu)
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

## Overscan Correction
The viewport is automatically centered with configurable margins to compensate for TV overscan. The default margins are 100px on all sides, but can be adjusted using keyboard shortcuts to perfectly align the viewport with your TV's visible area. The aspect ratio is maintained at 16:9 to prevent UI distortion.
