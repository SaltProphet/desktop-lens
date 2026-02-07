#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gtk, Gdk, Gst, GLib
import json
import os
import sys

CONFIG_FILE = os.path.expanduser("~/.config/desktop-lens.json")

class DesktopLens(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.init_gstreamer()
        self.init_ui()
        self.connect("delete-event", self.on_quit)
        self.connect("destroy", self.on_destroy)
        
    def load_config(self):
        self.config = {"x": 0, "y": 0, "scale": 1.0}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
    
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            x, y = self.get_position()
            self.config["x"] = x
            self.config["y"] = y
            self.config["scale"] = self.scale_value
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f)
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
        
        hw_type = self.detect_hw_acceleration()
        
        if hw_type == "vaapi":
            vaapipostproc = Gst.ElementFactory.make("vaapipostproc", "hwscale")
            vaapipostproc.set_property("scale-method", 2)
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            
            self.pipeline.add(self.src)
            self.pipeline.add(vaapipostproc)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(self.appsink)
            
            self.src.link(vaapipostproc)
            vaapipostproc.link(self.capsfilter)
            self.capsfilter.link(self.appsink)
            self.videoscale = vaapipostproc
        elif hw_type == "gl":
            glupload = Gst.ElementFactory.make("glupload", "upload")
            glcolorconvert = Gst.ElementFactory.make("glcolorconvert", "glconvert")
            glscale = Gst.ElementFactory.make("glcolorscale", "glscale")
            gldownload = Gst.ElementFactory.make("gldownload", "download")
            videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            
            self.pipeline.add(self.src)
            self.pipeline.add(glupload)
            self.pipeline.add(glcolorconvert)
            self.pipeline.add(glscale)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(gldownload)
            self.pipeline.add(videoconvert)
            self.pipeline.add(self.appsink)
            
            self.src.link(glupload)
            glupload.link(glcolorconvert)
            glcolorconvert.link(glscale)
            glscale.link(self.capsfilter)
            self.capsfilter.link(gldownload)
            gldownload.link(videoconvert)
            videoconvert.link(self.appsink)
            self.videoscale = glscale
        else:
            videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
            if not videoconvert:
                sys.exit("Failed to create videoconvert element")
                
            self.videoscale = Gst.ElementFactory.make("videoscale", "scale")
            if not self.videoscale:
                sys.exit("Failed to create videoscale element")
            self.videoscale.set_property("method", 3)
                
            self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
            if not self.capsfilter:
                sys.exit("Failed to create capsfilter element")
                
            self.appsink = Gst.ElementFactory.make("appsink", "sink")
            if not self.appsink:
                sys.exit("Failed to create appsink element")
            
            self.pipeline.add(self.src)
            self.pipeline.add(videoconvert)
            self.pipeline.add(self.videoscale)
            self.pipeline.add(self.capsfilter)
            self.pipeline.add(self.appsink)
            
            self.src.link(videoconvert)
            videoconvert.link(self.videoscale)
            self.videoscale.link(self.capsfilter)
            self.capsfilter.link(self.appsink)
        
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.set_property("max-buffers", 1)
        self.appsink.set_property("drop", True)
        self.appsink.connect("new-sample", self.on_new_sample)
        
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_bus_message)
        
        self.scale_value = self.config["scale"]
        self.update_videoscale_caps()
        
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            sys.exit("Failed to start GStreamer pipeline")
        
    def update_videoscale_caps(self):
        screen = Gdk.Screen.get_default()
        width = int(screen.get_width() * self.scale_value)
        height = int(screen.get_height() * self.scale_value)
        
        caps_str = f"video/x-raw,width={width},height={height}"
        caps = Gst.Caps.from_string(caps_str)
        
        self.capsfilter.set_property("caps", caps)
        
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
    
    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            struct = caps.get_structure(0)
            width = struct.get_value("width")
            height = struct.get_value("height")
            format_str = struct.get_value("format")
            
            success, mapinfo = buffer.map(Gst.MapFlags.READ)
            if success:
                pixbuf = GLib.Bytes.new(mapinfo.data)
                GLib.idle_add(self.update_image, pixbuf, width, height, format_str)
                buffer.unmap(mapinfo)
        
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
                    return False
                
                pixbuf_obj = Gdk.Pixbuf.new_from_bytes(
                    pixbuf, Gdk.Colorspace.RGB, has_alpha, 8, width, height, rowstride
                )
                self.image.set_from_pixbuf(pixbuf_obj)
            except (GLib.Error, ValueError):
                pass
        return False
        
    def init_ui(self):
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.move(self.config["x"], self.config["y"])
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)
        
        self.image = Gtk.Image()
        vbox.pack_start(self.image, True, True, 0)
        
        slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.7, 1.0, 0.01)
        slider.set_value(self.scale_value)
        slider.connect("value-changed", self.on_scale_changed)
        vbox.pack_start(slider, False, False, 0)
        
        self.set_default_size(800, 600)
        self.show_all()
        
    def on_scale_changed(self, slider):
        self.scale_value = slider.get_value()
        self.update_videoscale_caps()
        
    def on_quit(self, *args):
        self.save_config()
        self.cleanup_pipeline()
        Gtk.main_quit()
        return False
    
    def on_destroy(self, *args):
        """Ensure proper cleanup on window destruction"""
        self.cleanup_pipeline()
    
    def cleanup_pipeline(self):
        """Properly clean up GStreamer resources to prevent leaks"""
        if hasattr(self, 'pipeline') and self.pipeline:
            bus = self.pipeline.get_bus()
            if bus:
                bus.remove_signal_watch()
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None

if __name__ == "__main__":
    app = DesktopLens()
    Gtk.main()
