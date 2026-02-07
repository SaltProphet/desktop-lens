#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, Gst, GLib, GstVideo, GdkPixbuf
import json
import os
import sys
import argparse
import subprocess
import cairo
from pynput import keyboard
from threading import Thread

CONFIG_FILE = os.path.expanduser("~/.config/desktop-lens.json")
AUTO_SHOW_DELAY_SECONDS = 5  # Auto-show window after hiding via hotkey or button

class DesktopLens(Gtk.Window):
    def __init__(self):
        super().__init__()
        # Set window icon and WM_CLASS early for proper desktop integration
        self.set_wmclass("desktop-lens", "DesktopLens")
        self.set_icon_with_fallback()
        self.frozen = False
        self.frozen_pixbuf = None
        self.use_opacity_fallback = False  # Set to True if xid exclusion fails
        # Check if VideoOverlay mode should be used (set USE_VIDEO_OVERLAY=1 to enable)
        self.use_video_overlay = os.environ.get("USE_VIDEO_OVERLAY", "0") == "1"
        self.ghost_mode = False  # Track ghost mode state
        self.load_config()
        self.init_gstreamer()
        self.init_ui()
        self.connect("delete-event", self.on_quit)
        self.connect("destroy", self.on_destroy)
        # Set xid after the window is realized to exclude it from capture
        self.connect("realize", self.on_window_realized)
        # Start global hotkey listener in a separate thread
        self.init_global_hotkeys()
        
    def set_icon_with_fallback(self):
        """Set window icon with fallback if asset is missing"""
        # Try multiple possible icon locations
        icon_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.svg"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png"),
            "/usr/share/icons/hicolor/scalable/apps/desktop-lens.svg",
            "/usr/share/pixmaps/desktop-lens.svg"
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    self.set_icon_from_file(icon_path)
                    print(f"Loaded icon from: {icon_path}")
                    return
                except Exception as e:
                    print(f"Failed to load icon from {icon_path}: {e}")
        
        print("Warning: Could not load application icon")
    
    def load_config(self):
        self.config = {
            "x": 0, 
            "y": 0, 
            "scale": 1.0,
            "margin_top": 100,
            "margin_bottom": 100,
            "margin_left": 100,
            "margin_right": 100,
            "crop_to_region": False,
            "capture_endx": 0,
            "capture_endy": 0,
            "ghost_mode": False,
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
        self.ghost_mode = self.config.get("ghost_mode", False)
    
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            x, y = self.get_position()
            self.config["x"] = x
            self.config["y"] = y
            self.config["scale"] = self.scale_value
            self.config["margin_top"] = self.margin_top
            self.config["margin_bottom"] = self.margin_bottom
            self.config["margin_left"] = self.margin_left
            self.config["margin_right"] = self.margin_right
            self.config["crop_to_region"] = getattr(self, 'crop_to_region', False)
            self.config["capture_endx"] = getattr(self, 'capture_endx', 0)
            self.config["capture_endy"] = getattr(self, 'capture_endy', 0)
            self.config["ghost_mode"] = self.ghost_mode
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except (IOError, OSError):
            pass
    
    def detect_hw_acceleration(self):
        """Detect available hardware acceleration elements"""
        if Gst.ElementFactory.find("vaapipostproc"):
            return "vaapi"
        elif Gst.ElementFactory.find("glupload") and Gst.ElementFactory.find("glcolorconvert"):
            return "gl"
        return "software"
    
    def init_gstreamer(self):
        Gst.init(None)
        self.pipeline = Gst.Pipeline.new("desktop-lens")
        
        self.src = Gst.ElementFactory.make("ximagesrc", "src")
        if not self.src:
            sys.exit("Failed to create ximagesrc element. Ensure gstreamer1.0-plugins-good is installed.")
        self.src.set_property("use-damage", False)
        
        # Apply capture region cropping if configured
        self.crop_to_region = self.config.get("crop_to_region", False)
        self.capture_endx = self.config.get("capture_endx", 0)
        self.capture_endy = self.config.get("capture_endy", 0)
        
        if self.crop_to_region and self.capture_endx > 0 and self.capture_endy > 0:
            self.src.set_property("endx", self.capture_endx)
            self.src.set_property("endy", self.capture_endy)
            print(f"Cropping capture to region: 0,0 to {self.capture_endx},{self.capture_endy}")
        
        if self.use_video_overlay:
            # Use VideoOverlay mode with xvimagesink
            print("Using VideoOverlay mode with xvimagesink")
            self.init_gstreamer_overlay()
        else:
            # Use appsink mode (default)
            print("Using appsink mode")
            self.init_gstreamer_appsink()
        
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)
        
        self.scale_value = self.config["scale"]
        self.margin_top = self.config["margin_top"]
        self.margin_bottom = self.config["margin_bottom"]
        self.margin_left = self.config["margin_left"]
        self.margin_right = self.config["margin_right"]
        self.update_videoscale_caps()
        
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            sys.exit("Failed to start GStreamer pipeline")
    
    def init_gstreamer_overlay(self):
        """Initialize GStreamer pipeline using VideoOverlay (xvimagesink)"""
        videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
        if not videoconvert:
            sys.exit("Failed to create videoconvert element")
            
        self.videoscale = Gst.ElementFactory.make("videoscale", "scale")
        if not self.videoscale:
            sys.exit("Failed to create videoscale element")
        self.videoscale.set_property("method", 3)
        self.videoscale.set_property("add-borders", True)
            
        self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
        if not self.capsfilter:
            sys.exit("Failed to create capsfilter element")
            
        self.videosink = Gst.ElementFactory.make("xvimagesink", "sink")
        if not self.videosink:
            sys.exit("Failed to create xvimagesink element")
        self.videosink.set_property("force-aspect-ratio", False)
        
        self.pipeline.add(self.src)
        self.pipeline.add(videoconvert)
        self.pipeline.add(self.videoscale)
        self.pipeline.add(self.capsfilter)
        self.pipeline.add(self.videosink)
        
        self.src.link(videoconvert)
        videoconvert.link(self.videoscale)
        self.videoscale.link(self.capsfilter)
        self.capsfilter.link(self.videosink)
    
    def init_gstreamer_appsink(self):
        """Initialize GStreamer pipeline using appsink (default mode)"""
        hw_type = self.detect_hw_acceleration()
        
        if hw_type == "vaapi":
            vaapipostproc = Gst.ElementFactory.make("vaapipostproc", "hwscale")
            vaapipostproc.set_property("scale-method", 2)
            videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
            # Add capsfilter to force RGBA format after videoconvert
            rgba_capsfilter = Gst.ElementFactory.make("capsfilter", "rgba_filter")
            rgba_caps = Gst.Caps.from_string("video/x-raw,format=RGBA")
            rgba_capsfilter.set_property("caps", rgba_caps)
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            
            self.pipeline.add(self.src)
            self.pipeline.add(vaapipostproc)
            self.pipeline.add(videoconvert)
            self.pipeline.add(rgba_capsfilter)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(self.appsink)
            
            self.src.link(vaapipostproc)
            vaapipostproc.link(videoconvert)
            videoconvert.link(rgba_capsfilter)
            rgba_capsfilter.link(self.capsfilter)
            self.capsfilter.link(self.appsink)
            self.videoscale = vaapipostproc
        elif hw_type == "gl":
            glupload = Gst.ElementFactory.make("glupload", "upload")
            glcolorconvert = Gst.ElementFactory.make("glcolorconvert", "glconvert")
            glscale = Gst.ElementFactory.make("glcolorscale", "glscale")
            gldownload = Gst.ElementFactory.make("gldownload", "download")
            videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
            # Add capsfilter to force RGBA format after videoconvert
            rgba_capsfilter = Gst.ElementFactory.make("capsfilter", "rgba_filter")
            rgba_caps = Gst.Caps.from_string("video/x-raw,format=RGBA")
            rgba_capsfilter.set_property("caps", rgba_caps)
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            
            self.pipeline.add(self.src)
            self.pipeline.add(glupload)
            self.pipeline.add(glcolorconvert)
            self.pipeline.add(glscale)
            self.pipeline.add(gldownload)
            self.pipeline.add(videoconvert)
            self.pipeline.add(rgba_capsfilter)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(self.appsink)
            
            self.src.link(glupload)
            glupload.link(glcolorconvert)
            glcolorconvert.link(glscale)
            glscale.link(gldownload)
            gldownload.link(videoconvert)
            videoconvert.link(rgba_capsfilter)
            rgba_capsfilter.link(self.capsfilter)
            self.capsfilter.link(self.appsink)
            self.videoscale = glscale
        else:
            videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
            if not videoconvert:
                sys.exit("Failed to create videoconvert element")
            
            # Add capsfilter to force RGBA format after videoconvert
            rgba_capsfilter = Gst.ElementFactory.make("capsfilter", "rgba_filter")
            rgba_caps = Gst.Caps.from_string("video/x-raw,format=RGBA")
            rgba_capsfilter.set_property("caps", rgba_caps)
                
            self.videoscale = Gst.ElementFactory.make("videoscale", "scale")
            if not self.videoscale:
                sys.exit("Failed to create videoscale element")
            self.videoscale.set_property("method", 3)
            self.videoscale.set_property("add-borders", True)
                
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            if not self.capsfilter:
                sys.exit("Failed to create capsfilter element")
                
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            if not self.appsink:
                sys.exit("Failed to create appsink element")
            
            self.pipeline.add(self.src)
            self.pipeline.add(videoconvert)
            self.pipeline.add(rgba_capsfilter)
            self.pipeline.add(self.videoscale)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(self.appsink)
            
            self.src.link(videoconvert)
            videoconvert.link(rgba_capsfilter)
            rgba_capsfilter.link(self.videoscale)
            self.videoscale.link(self.capsfilter)
            self.capsfilter.link(self.appsink)
        
        # Set appsink properties with explicit RGBA caps
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.set_property("max-buffers", 1)
        self.appsink.set_property("drop", True)
        # Set caps to RGBA format
        appsink_caps = Gst.Caps.from_string("video/x-raw,format=RGBA")
        self.appsink.set_property("caps", appsink_caps)
        self.appsink.connect("new-sample", self.on_new_sample)
    
    def update_videoscale_caps(self):
        screen = Gdk.Screen.get_default()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Calculate available viewport dimensions after removing margins
        viewport_width = screen_width - self.margin_left - self.margin_right
        viewport_height = screen_height - self.margin_top - self.margin_bottom
        
        # Ensure minimum dimensions before any calculations
        viewport_width = max(viewport_width, 320)
        viewport_height = max(viewport_height, 180)
        
        # Apply scale factor
        viewport_width = int(viewport_width * self.scale_value)
        viewport_height = int(viewport_height * self.scale_value)
        
        # Maintain 16:9 aspect ratio
        aspect_ratio = 16.0 / 9.0
        viewport_aspect = viewport_width / viewport_height
        
        if viewport_aspect > aspect_ratio:
            # Width is too large, constrain by height
            viewport_width = int(viewport_height * aspect_ratio)
        else:
            # Height is too large, constrain by width
            viewport_height = int(viewport_width / aspect_ratio)
        
        # Ensure final minimum dimensions
        viewport_width = max(viewport_width, 320)
        viewport_height = max(viewport_height, 180)
        
        caps_str = f"video/x-raw,format=RGBA,width={viewport_width},height={viewport_height}"
        caps = Gst.Caps.from_string(caps_str)
        
        self.capsfilter.set_property("caps", caps)
        
        # Update the layout if image widget exists
        if hasattr(self, 'image_box'):
            self.update_viewport_layout()
        
    def on_bus_message(self, bus, message):
        """Handle GStreamer bus messages to prevent UI freezes"""
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer Error: {err}, {debug}", file=sys.stderr)
        elif t == Gst.MessageType.WARNING:
            warn, debug = message.parse_warning()
            print(f"GStreamer Warning: {warn}, {debug}", file=sys.stderr)
        elif t == Gst.MessageType.EOS:
            self.pipeline.set_state(Gst.State.NULL)
        return True
    
    def on_window_realized(self, widget):
        """Configure ximagesrc to avoid capturing this window and apply ghost mode if enabled"""
        # If using VideoOverlay mode, set the window handle
        if self.use_video_overlay and hasattr(self, 'videosink') and hasattr(self, 'drawing_area'):
            drawing_window = self.drawing_area.get_window()
            if drawing_window:
                xid = drawing_window.get_xid()
                self.videosink.set_window_handle(xid)
                print(f"VideoOverlay: Set window handle to XID {xid}")
        
        window = self.get_window()
        if window:
            xid = window.get_xid()
            print(f"Window realized with XID: {xid}")
            
            # Set the xid property on ximagesrc to exclude this window from capture
            # This prevents the hall of mirrors effect
            try:
                self.src.set_property("xid", xid)
                print(f"Set ximagesrc xid property to {xid} to exclude window from capture")
            except Exception as e:
                print(f"Warning: Could not set xid property on ximagesrc: {e}")
                print("Note: XID exclusion may not be supported by your ximagesrc version or compositor")
                # Fallback: Use opacity approach during capture
                self.use_opacity_fallback = True
            
            # Apply ghost mode if it was enabled in config
            if self.ghost_mode:
                try:
                    empty_region = cairo.Region()
                    window.input_shape_combine_region(empty_region, 0, 0)
                    print("Ghost mode restored from config")
                except Exception as e:
                    print(f"Failed to restore ghost mode: {e}")
                    self.ghost_mode = False
    
    def on_new_sample(self, sink):
        # If frozen, don't update the image
        if self.frozen:
            return Gst.FlowReturn.OK
        
        # If using opacity fallback, reduce window opacity during capture
        if self.use_opacity_fallback:
            self.set_opacity(0.001)
            
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            struct = caps.get_structure(0)
            width = struct.get_value("width")
            height = struct.get_value("height")
            format_str = struct.get_value("format")
            
            print(f"Received sample: {width}x{height}, format={format_str}")
            
            success, mapinfo = buffer.map(Gst.MapFlags.READ)
            if success:
                pixbuf = GLib.Bytes.new(mapinfo.data)
                GLib.idle_add(self.update_image, pixbuf, width, height, format_str)
                buffer.unmap(mapinfo)
        
        # Restore opacity immediately after capture if using fallback
        # Using direct call instead of idle_add to prevent opacity from staying low
        if self.use_opacity_fallback:
            self.set_opacity(1.0)
        
        return Gst.FlowReturn.OK
    
    def update_image(self, pixbuf, width, height, format_str):
        if hasattr(self, 'image'):
            try:
                if format_str in ("RGB", "BGR"):
                    rowstride = width * 3
                    has_alpha = False
                elif format_str in ("RGBA", "BGRA", "RGBx", "BGRx"):
                    rowstride = width * 4
                    has_alpha = format_str in ("RGBA", "BGRA")
                else:
                    print(f"Unsupported format: {format_str}")
                    return False
                
                pixbuf_obj = GdkPixbuf.Pixbuf.new_from_bytes(
                    pixbuf, GdkPixbuf.Colorspace.RGB, has_alpha, 8, width, height, rowstride
                )
                
                # Store the pixbuf for freeze functionality
                if not self.frozen:
                    self.frozen_pixbuf = pixbuf_obj
                    self.image.set_from_pixbuf(pixbuf_obj)
                    self.image.queue_draw()  # Force redraw
                    print(f"Image updated: {width}x{height}")
                # If frozen, keep displaying the frozen image
            except (GLib.Error, ValueError) as e:
                print(f"Error updating image: {e}")
                pass
        return False
        
    def update_viewport_layout(self):
        """Update the padding around the viewport based on margins"""
        if hasattr(self, 'image_box'):
            self.image_box.set_margin_top(self.margin_top)
            self.image_box.set_margin_bottom(self.margin_bottom)
            self.image_box.set_margin_start(self.margin_left)
            self.image_box.set_margin_end(self.margin_right)
        
    def init_ui(self):
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_accept_focus(False)  # Change from True to False - never steal focus
        self.move(self.config["x"], self.config["y"])
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)
        
        # Create a centered container for the viewport with margins
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.image_box.set_halign(Gtk.Align.CENTER)
        self.image_box.set_valign(Gtk.Align.CENTER)
        
        # Apply initial margins
        self.image_box.set_margin_top(self.margin_top)
        self.image_box.set_margin_bottom(self.margin_bottom)
        self.image_box.set_margin_start(self.margin_left)
        self.image_box.set_margin_end(self.margin_right)
        
        if self.use_video_overlay:
            # Use a DrawingArea for VideoOverlay rendering
            self.drawing_area = Gtk.DrawingArea()
            self.drawing_area.set_size_request(800, 450)  # Default 16:9 size
            self.image_box.pack_start(self.drawing_area, True, True, 0)
        else:
            # Use Gtk.Image for appsink rendering
            self.image = Gtk.Image()
            self.image_box.pack_start(self.image, True, True, 0)
        
        vbox.pack_start(self.image_box, True, True, 0)
        
        # Controls container at the bottom
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        controls_box.set_margin_start(5)
        controls_box.set_margin_end(5)
        controls_box.set_margin_top(5)
        controls_box.set_margin_bottom(5)
        
        # Scale slider
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.7, 1.0, 0.01)
        slider.set_value(self.scale_value)
        slider.connect("value-changed", self.on_scale_changed)
        slider.set_hexpand(True)
        controls_box.pack_start(slider, True, True, 0)
        
        # Toggle Freeze button
        self.freeze_button = Gtk.Button(label="Freeze")
        self.freeze_button.connect("clicked", self.on_toggle_freeze)
        controls_box.pack_start(self.freeze_button, False, False, 0)
        
        # Hide Window button (toggle visibility)
        self.hide_button = Gtk.Button(label="Hide Window")
        self.hide_button.connect("clicked", self.on_toggle_hide)
        controls_box.pack_start(self.hide_button, False, False, 0)
        
        # Crop Region button (toggle capture area cropping)
        self.crop_button = Gtk.Button(label="Crop: OFF")
        self.crop_button.connect("clicked", self.on_toggle_crop)
        controls_box.pack_start(self.crop_button, False, False, 0)
        if self.crop_to_region:
            self.crop_button.set_label("Crop: ON")
        
        # Ghost Mode button (toggle click-through)
        self.ghost_button = Gtk.Button(label="Ghost: OFF")
        self.ghost_button.connect("clicked", self.on_toggle_ghost)
        controls_box.pack_start(self.ghost_button, False, False, 0)
        if self.ghost_mode:
            self.ghost_button.set_label("Ghost: ON")
        
        vbox.pack_start(controls_box, False, False, 0)
        
        # Connect keyboard events
        self.connect("key-press-event", self.on_key_press)
        
        self.set_default_size(800, 600)
        self.show_all()
        
    def on_scale_changed(self, slider):
        self.scale_value = slider.get_value()
        # Pause the pipeline briefly to prevent flickering
        if hasattr(self, 'pipeline'):
            self.pipeline.set_state(Gst.State.PAUSED)
        self.update_videoscale_caps()
        # Resume the pipeline after a 50ms delay to ensure caps are fully applied
        # This prevents visual glitches during the transition
        if hasattr(self, 'pipeline'):
            GLib.timeout_add(50, self._resume_pipeline)
    
    def _resume_pipeline(self):
        """Resume pipeline after a brief delay to prevent flickering"""
        if hasattr(self, 'pipeline'):
            self.pipeline.set_state(Gst.State.PLAYING)
        return False
    
    def on_toggle_freeze(self, button):
        """Toggle freeze mode to snapshot the desktop"""
        self.frozen = not self.frozen
        if self.frozen:
            self.freeze_button.set_label("Unfreeze")
            # Display the last captured frame
            if self.frozen_pixbuf:
                self.image.set_from_pixbuf(self.frozen_pixbuf)
        else:
            self.freeze_button.set_label("Freeze")
    
    def on_toggle_hide(self, button):
        """Toggle window visibility to avoid hall of mirrors"""
        if self.is_visible():
            self.hide()
            # Auto-show after configured delay to allow user to see the result
            # without having to manually re-launch the application
            GLib.timeout_add_seconds(AUTO_SHOW_DELAY_SECONDS, self._show_window)
        
    def _show_window(self):
        """Show the window after hiding"""
        self.show_all()
        return False
    
    def on_toggle_crop(self, button):
        """Toggle capture region cropping to avoid hall of mirrors"""
        self.crop_to_region = not self.crop_to_region
        
        if self.crop_to_region:
            # Get the primary monitor dimensions
            screen = Gdk.Screen.get_default()
            display = screen.get_display()
            monitor = display.get_primary_monitor()
            if monitor:
                geometry = monitor.get_geometry()
                self.capture_endx = geometry.width
                self.capture_endy = geometry.height
                self.src.set_property("endx", self.capture_endx)
                self.src.set_property("endy", self.capture_endy)
                self.crop_button.set_label("Crop: ON")
                print(f"Enabled region cropping to {self.capture_endx}x{self.capture_endy}")
            else:
                # Fallback if we can't get monitor info
                self.crop_to_region = False
                print("Could not determine monitor dimensions")
        else:
            # Reset to full screen capture
            self.src.set_property("endx", 0)
            self.src.set_property("endy", 0)
            self.capture_endx = 0
            self.capture_endy = 0
            self.crop_button.set_label("Crop: OFF")
            print("Disabled region cropping")
    
    def toggle_ghost_mode(self):
        """Toggle ghost mode (click-through window)"""
        self.ghost_mode = not self.ghost_mode
        
        window = self.get_window()
        if not window:
            print("Window not realized yet")
            return
        
        if self.ghost_mode:
            # Enable ghost mode: make window click-through
            try:
                empty_region = cairo.Region()
                window.input_shape_combine_region(empty_region, 0, 0)
                print("Ghost mode ENABLED - window is now click-through")
                if hasattr(self, 'ghost_button'):
                    self.ghost_button.set_label("Ghost: ON")
            except Exception as e:
                print(f"Failed to enable ghost mode: {e}")
                self.ghost_mode = False
        else:
            # Disable ghost mode: restore normal input region
            try:
                # Get screen dimensions to create full input region
                screen = Gdk.Screen.get_default()
                screen_width = screen.get_width()
                screen_height = screen.get_height()
                # Create a full region covering the entire window
                full_region = cairo.Region(cairo.RectangleInt(0, 0, screen_width, screen_height))
                window.input_shape_combine_region(full_region, 0, 0)
                print("Ghost mode DISABLED - window accepts input")
                if hasattr(self, 'ghost_button'):
                    self.ghost_button.set_label("Ghost: OFF")
            except Exception as e:
                print(f"Failed to disable ghost mode: {e}")
    
    def on_toggle_ghost(self, button):
        """Handle ghost mode button click"""
        self.toggle_ghost_mode()
    
    def toggle_visibility(self):
        """Toggle window visibility (for Ctrl+Alt+H hotkey)"""
        if self.is_visible():
            self.hide()
            print("Window hidden via hotkey")
            # Auto-show after configured delay
            GLib.timeout_add_seconds(AUTO_SHOW_DELAY_SECONDS, self._show_window_from_hotkey)
        else:
            self.show_all()
            print("Window shown via hotkey")
    
    def _show_window_from_hotkey(self):
        """Show the window after hiding via hotkey"""
        self.show_all()
        print(f"Window auto-shown after {AUTO_SHOW_DELAY_SECONDS} seconds")
        return False
    
    def init_global_hotkeys(self):
        """Initialize global hotkey listener using pynput"""
        # Track currently pressed keys (accessed from pynput thread)
        # Using set operations which are atomic in CPython for thread safety
        self.current_keys = set()
        
        def on_press(key):
            """Handle key press events"""
            try:
                # Add key to currently pressed set
                self.current_keys.add(key)
                
                # Check for Ctrl+Alt+G or Ctrl+Alt+H
                ctrl_pressed = keyboard.Key.ctrl_l in self.current_keys or keyboard.Key.ctrl_r in self.current_keys
                alt_pressed = keyboard.Key.alt_l in self.current_keys or keyboard.Key.alt_r in self.current_keys
                
                if ctrl_pressed and alt_pressed:
                    # Check for G or H key
                    if hasattr(key, 'char') and key.char and key.char.lower() == 'g':
                        # Ctrl+Alt+G: Toggle Ghost Mode
                        GLib.idle_add(self.toggle_ghost_mode)
                    elif hasattr(key, 'char') and key.char and key.char.lower() == 'h':
                        # Ctrl+Alt+H: Toggle Visibility
                        GLib.idle_add(self.toggle_visibility)
            except AttributeError:
                pass
        
        def on_release(key):
            """Handle key release events"""
            # Remove key from currently pressed set (discard never raises exception)
            self.current_keys.discard(key)
        
        # Start keyboard listener in a daemon thread (daemon must be set before start)
        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release, daemon=True)
        self.keyboard_listener.start()
        print("Global hotkey listener started (Ctrl+Alt+G for Ghost Mode, Ctrl+Alt+H for Visibility)")
    
    def stop_global_hotkeys(self):
        """Stop the global hotkey listener"""
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
            print("Global hotkey listener stopped")
    
    def apply_margin_changes(self):
        """Helper method to apply margin changes"""
        self.update_viewport_layout()
        self.update_videoscale_caps()
    
    def on_key_press(self, widget, event):
        """Handle keyboard shortcuts for margin adjustments"""
        # Note: Ghost mode hotkeys (Ctrl+Alt+G/H) are handled by the global
        # pynput listener since set_accept_focus(False) prevents this handler
        # from receiving keyboard events in most cases.
        
        # Space key to toggle freeze
        if event.keyval == Gdk.KEY_space:
            self.on_toggle_freeze(None)
            return True
        # Check if Ctrl key is pressed
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.KEY_Up:
                self.margin_top = max(0, self.margin_top - 5)
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Down:
                self.margin_top += 5
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Left:
                self.margin_left = max(0, self.margin_left - 5)
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Right:
                self.margin_left += 5
                self.apply_margin_changes()
                return True
        # Check if Shift key is pressed for bottom/right margins
        elif event.state & Gdk.ModifierType.SHIFT_MASK:
            if event.keyval == Gdk.KEY_Up:
                self.margin_bottom = max(0, self.margin_bottom - 5)
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Down:
                self.margin_bottom += 5
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Left:
                self.margin_right = max(0, self.margin_right - 5)
                self.apply_margin_changes()
                return True
            elif event.keyval == Gdk.KEY_Right:
                self.margin_right += 5
                self.apply_margin_changes()
                return True
        return False
        
    def on_quit(self, *args):
        self.save_config()
        self.stop_global_hotkeys()
        self.cleanup_pipeline()
        Gtk.main_quit()
        return False
    
    def on_destroy(self, *args):
        """Ensure proper cleanup on window destruction"""
        self.stop_global_hotkeys()
        self.cleanup_pipeline()
    
    def cleanup_pipeline(self):
        """Properly clean up GStreamer resources to prevent leaks"""
        if hasattr(self, 'pipeline') and self.pipeline:
            bus = self.pipeline.get_bus()
            if bus:
                bus.remove_signal_watch()
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

def install_desktop_integration():
    """Install desktop entry and icon for system integration"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_source = os.path.join(script_dir, "assets", "icon.svg")
    
    # Create assets directory if it doesn't exist
    assets_dir = os.path.join(script_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create icon if it doesn't exist
    if not os.path.exists(icon_source):
        icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="20" width="80" height="60" rx="5" fill="#333" stroke="#fff" stroke-width="2"/>
  <circle cx="50" cy="50" r="15" fill="none" stroke="#fff" stroke-width="2"/>
  <line x1="10" y1="50" x2="90" y2="50" stroke="#fff" stroke-width="1" stroke-dasharray="4"/>
</svg>"""
        with open(icon_source, 'w') as f:
            f.write(icon_svg)
        print(f"Created icon at: {icon_source}")
    
    # Create .desktop file
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)
    
    desktop_file_path = os.path.join(desktop_dir, "desktop-lens.desktop")
    desktop_content = f"""[Desktop Entry]
Name=Desktop Lens
Comment=Correct TV Overscan Viewport
Exec=python3 {os.path.join(script_dir, "desktop-lens.py")}
Icon={icon_source}
Terminal=false
Type=Application
Categories=Utility;Video;AudioVideo;
StartupNotify=true
Keywords=overscan;tv;mirror;screen;display
"""
    
    with open(desktop_file_path, 'w') as f:
        f.write(desktop_content)
    
    # Set appropriate permissions for .desktop file
    os.chmod(desktop_file_path, 0o644)
    
    print(f"Desktop integration installed successfully!")
    print(f"  - Desktop file: {desktop_file_path}")
    print(f"  - Icon: {icon_source}")
    print("\nYou can now find 'Desktop Lens' in your application menu.")
    print("You may need to log out and back in for the icon to appear in the menu.")
    
    # Update desktop database
    try:
        subprocess.run(["update-desktop-database", desktop_dir], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass  # update-desktop-database not available, that's okay

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desktop Lens - TV Overscan Correction Tool")
    parser.add_argument("--install", action="store_true", 
                       help="Install desktop integration (menu entry and icon)")
    args = parser.parse_args()
    
    if args.install:
        install_desktop_integration()
        sys.exit(0)
    
    app = DesktopLens()
    Gtk.main()
