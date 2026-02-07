# Troubleshooting Guide

## Common Issues and Solutions

### AttributeError: 'gi.repository.Gdk' object has no attribute 'Pixbuf'

**Symptom:**
```
AttributeError: 'gi.repository.Gdk' object has no attribute 'Pixbuf'
```

**Cause:**
This error occurs when trying to use `Gdk.Pixbuf` instead of the correct `GdkPixbuf.Pixbuf`. In PyGObject/GTK, `GdkPixbuf` is a separate namespace from `Gdk`.

**Solution:**
Make sure you have the latest version of `desktop-lens.py` from this repository. The issue has been fixed in the current version.

If you're running an older version or modified version, ensure:

1. The imports at the top of the file include:
   ```python
   gi.require_version('GdkPixbuf', '2.0')
   from gi.repository import Gtk, Gdk, Gst, GLib, GstVideo, GdkPixbuf
   ```

2. Any code creating Pixbuf objects uses `GdkPixbuf.Pixbuf`, not `Gdk.Pixbuf`:
   ```python
   # CORRECT:
   pixbuf_obj = GdkPixbuf.Pixbuf.new_from_bytes(...)
   
   # INCORRECT:
   pixbuf_obj = Gdk.Pixbuf.new_from_bytes(...)
   ```

**To update:**
```bash
cd /path/to/desktop-lens
git pull origin main
```

### Missing GdkPixbuf Library

**Symptom:**
```
ValueError: Namespace GdkPixbuf not available
```

**Solution:**
Install the required GdkPixbuf typelib:
```bash
# Debian/Ubuntu:
sudo apt-get install gir1.2-gdkpixbuf-2.0

# Fedora:
sudo dnf install gdk-pixbuf2-devel

# Arch:
sudo pacman -S gdk-pixbuf2
```

### GStreamer Pipeline Issues

**Symptom:**
```
Not Negotiated error from GStreamer pipeline
```

**Solution:**
Ensure you have the required GStreamer plugins:
```bash
sudo apt-get install gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```

See README.md for full installation instructions.
