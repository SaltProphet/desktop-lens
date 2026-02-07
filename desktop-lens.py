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
        
    def load_config(self):
        self.config = {"x": 0, "y": 0, "scale": 1.0}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except (json.JSONDecodeError, IOError):
                pass
    
    def save_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        x, y = self.get_position()
        self.config["x"] = x
        self.config["y"] = y
        self.config["scale"] = self.scale_value
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)
    
    def init_gstreamer(self):
        Gst.init(None)
        self.pipeline = Gst.Pipeline.new("desktop-lens")
        
        self.src = Gst.ElementFactory.make("ximagesrc", "src")
        self.src.set_property("use-damage", False)
        
        videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
        self.videoscale = Gst.ElementFactory.make("videoscale", "scale")
        self.capsfilter = Gst.ElementFactory.make("capsfilter", "filter")
        self.appsink = Gst.ElementFactory.make("appsink", "sink")
        
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.connect("new-sample", self.on_new_sample)
        
        self.pipeline.add(self.src)
        self.pipeline.add(videoconvert)
        self.pipeline.add(self.videoscale)
        self.pipeline.add(self.capsfilter)
        self.pipeline.add(self.appsink)
        
        self.src.link(videoconvert)
        videoconvert.link(self.videoscale)
        self.videoscale.link(self.capsfilter)
        self.capsfilter.link(self.appsink)
        
        self.scale_value = self.config["scale"]
        self.update_videoscale_caps()
        
        self.pipeline.set_state(Gst.State.PLAYING)
        
    def update_videoscale_caps(self):
        screen = Gdk.Screen.get_default()
        width = int(screen.get_width() * self.scale_value)
        height = int(screen.get_height() * self.scale_value)
        
        caps_str = f"video/x-raw,width={width},height={height}"
        caps = Gst.Caps.from_string(caps_str)
        
        self.capsfilter.set_property("caps", caps)
        
    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            struct = caps.get_structure(0)
            width = struct.get_value("width")
            height = struct.get_value("height")
            
            success, mapinfo = buffer.map(Gst.MapFlags.READ)
            if success:
                pixbuf = GLib.Bytes.new(mapinfo.data)
                GLib.idle_add(self.update_image, pixbuf, width, height)
                buffer.unmap(mapinfo)
        
        return Gst.FlowReturn.OK
    
    def update_image(self, pixbuf, width, height):
        if hasattr(self, 'image'):
            try:
                pixbuf_obj = Gdk.Pixbuf.new_from_bytes(
                    pixbuf, Gdk.Colorspace.RGB, False, 8, width, height, width * 3
                )
                self.image.set_from_pixbuf(pixbuf_obj)
            except (GLib.Error, ValueError):
                pass
        return False
        
    def init_ui(self):
        self.set_decorated(False)
        self.set_keep_above(True)
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
        self.pipeline.set_state(Gst.State.NULL)
        Gtk.main_quit()
        return False

if __name__ == "__main__":
    app = DesktopLens()
    Gtk.main()
