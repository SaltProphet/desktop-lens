# Overscan Correction Feature Guide

## Overview
Desktop-lens now includes comprehensive overscan correction capabilities to address the common issue where TV displays cut off ~100px from all edges of the screen.

## Problem Statement
TV overscan is a legacy feature from CRT displays that crops the edges of the image. Modern TVs often still apply overscan by default, which can cut off UI elements, taskbars, and content at the screen edges.

## Solution
Desktop-lens provides configurable margins with real-time adjustment capabilities to compensate for overscan and center the viewport perfectly within the visible TV area.

## Features

### 1. Configurable Margins
- **Default**: 100px on all sides (top, bottom, left, right)
- **Storage**: Persisted in `~/.config/desktop-lens.json`
- **Real-time adjustment**: Changes apply immediately without restart

Example configuration:
```json
{
  "x": 100,
  "y": 50,
  "scale": 1.0,
  "margin_top": 100,
  "margin_bottom": 100,
  "margin_left": 100,
  "margin_right": 100
}
```

### 2. 16:9 Aspect Ratio Enforcement
The viewport automatically maintains a 16:9 aspect ratio to prevent UI distortion. This ensures:
- Content appears correctly proportioned
- No stretching or squashing of UI elements
- Consistent appearance across different screen sizes

**Technical Implementation:**
```python
# After calculating viewport dimensions with margins
aspect_ratio = 16.0 / 9.0
viewport_aspect = viewport_width / viewport_height

if viewport_aspect > aspect_ratio:
    viewport_width = int(viewport_height * aspect_ratio)
else:
    viewport_height = int(viewport_width / aspect_ratio)
```

### 3. Centered Viewport Layout
The video viewport is automatically centered within the application window with configurable padding on all sides. This creates a "picture frame" effect where the overscan areas are visible as black borders, helping you align the content perfectly with your TV's visible area.

### 4. Keyboard Shortcuts for Fine-Tuning
Adjust margins in 5px increments using keyboard shortcuts:

#### Top/Left Margin Controls (Ctrl + Arrows)
- **Ctrl + Up**: Decrease top margin (viewport moves up)
- **Ctrl + Down**: Increase top margin (viewport moves down)
- **Ctrl + Left**: Decrease left margin (viewport moves left)
- **Ctrl + Right**: Increase left margin (viewport moves right)

#### Bottom/Right Margin Controls (Shift + Arrows)
- **Shift + Up**: Decrease bottom margin (more space at bottom)
- **Shift + Down**: Increase bottom margin (less space at bottom)
- **Shift + Left**: Decrease right margin (more space at right)
- **Shift + Right**: Increase right margin (less space at right)

## Usage Workflow

### Initial Setup
1. Launch desktop-lens: `./desktop-lens.py`
2. The application starts with 100px margins on all sides
3. Position the window to fill your TV screen

### Fine-Tuning for Your TV
1. Observe which edges are cut off by overscan
2. Use keyboard shortcuts to adjust margins:
   - If top is cut off: Press `Ctrl+Down` repeatedly to add top margin
   - If left is cut off: Press `Ctrl+Right` repeatedly to add left margin
   - If bottom is cut off: Press `Shift+Down` repeatedly to add bottom margin
   - If right is cut off: Press `Shift+Right` repeatedly to add right margin
3. Adjust until the entire viewport is visible on your TV
4. Close the application - settings are automatically saved

### Adjusting Scale
Use the slider at the bottom to scale the desktop view (0.7x to 1.0x) while maintaining the 16:9 aspect ratio.

## Technical Details

### GStreamer Pipeline Integration
The margins affect the GStreamer video capture dimensions:
```
Available width = Screen width - margin_left - margin_right
Available height = Screen height - margin_top - margin_bottom
Final dimensions = Apply scale × Enforce 16:9 ratio
```

### GTK Layout Structure
```
Window
└── VBox
    ├── ImageBox (centered with margins)
    │   └── Image (video viewport)
    └── Scale slider
```

The `ImageBox` uses GTK margin properties (`set_margin_top`, `set_margin_bottom`, `set_margin_start`, `set_margin_end`) and alignment properties (`set_halign(CENTER)`, `set_valign(CENTER)`) to create the centered layout.

### Minimum Dimensions
To prevent errors, the viewport maintains minimum dimensions of 320x180 pixels even with extreme margin settings.

## Troubleshooting

### Margins too large for screen
If your margins exceed the screen dimensions, the viewport will be constrained to minimum size (320x180). Reduce margins using the keyboard shortcuts.

### Aspect ratio doesn't look right
The 16:9 aspect ratio is enforced automatically. If content appears distorted, check that:
1. Your source desktop resolution is compatible
2. The scale factor is set appropriately
3. Margins haven't forced the viewport too small

### Keyboard shortcuts not working
Ensure the desktop-lens window has focus. The window must accept focus for keyboard events to work (this is now enabled by default).

## Configuration File Location
`~/.config/desktop-lens.json`

All settings are automatically saved when you close the application.
