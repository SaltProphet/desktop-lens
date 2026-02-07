# desktop-lens
A Python/GStreamer tool to correct TV overscan by creating a resizable, hardware-accelerated viewport mirror of the Linux desktop.

## Features
- Captures the root X11 window using ximagesrc
- GStreamer pipeline: ximagesrc → videoconvert → videoscale → appsink
- Borderless, always-on-top GTK3 window
- Dynamic scale adjustment via slider (0.7x to 1.0x)
- JSON persistence for window position and scale factor
- Graceful GStreamer shutdown on exit

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

## Controls
- Use the slider at the bottom to adjust the desktop scale
- Drag the window to reposition it
- Close the window to save settings and exit
