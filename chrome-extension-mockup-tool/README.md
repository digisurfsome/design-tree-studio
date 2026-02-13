# UI Mockup Tool - Chrome Extension

A Chrome extension that lets you screenshot any webpage, select UI elements as draggable chunks, rearrange them to create layout mockups, and export the result.

## Features

- **Screenshot Capture**: One-click capture of any webpage
- **Chunk Selection**: Draw rectangles to cut out UI elements
- **Drag & Drop**: Move chunks around to show desired layout
- **Annotations**: Add arrows, rectangles, and text
- **Export**: Save mockup as PNG

## Installation

### 1. Create Icons (Required)

Before loading the extension, you need to create icon files.

**Option A: Use any image editor**
Create 3 PNG files in the `icons/` folder:
- `icon16.png` (16x16 pixels)
- `icon48.png` (48x48 pixels)
- `icon128.png` (128x128 pixels)

**Option B: Quick placeholder icons**
1. Open `icons/generate-icons.html` in Chrome
2. Right-click each canvas and "Save Image As" with the correct filename

### 2. Load in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `chrome-extension-mockup-tool` folder
5. The extension icon should appear in your toolbar

## Usage

### Basic Workflow

1. Navigate to any webpage you want to mockup
2. Click the extension icon (or press `Alt+M`)
3. Click **Capture Page**
4. In the editor:
   - Use **Select Tool (✂️)** to draw rectangles around UI elements
   - Selected areas become draggable chunks
   - Drag chunks to show desired spacing/arrangement
   - Add annotations (arrows, rectangles, text) as needed
5. Click **Export** to save your mockup

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Alt+M` | Capture current page |
| `V` | Select/Cut tool |
| `M` | Move tool |
| `A` | Arrow tool |
| `R` | Rectangle tool |
| `T` | Text tool |
| `Ctrl+Z` | Undo |
| `Escape` | Cancel current action |

### Tools

- **Select (✂️)**: Draw a rectangle to cut out a UI chunk
- **Move (✋)**: Drag chunks to new positions
- **Arrow (➡️)**: Draw arrows to point at things
- **Rectangle (⬜)**: Draw outlined rectangles
- **Text (📝)**: Add text labels

### Colors & Line Width

- Click color buttons to change annotation color
- Use dropdown to change line thickness (Thin/Medium/Thick)

## Use Case Example

**Problem**: "I want the spacing tighter between these UI elements"

**Solution**:
1. Screenshot your app
2. Cut out each UI element as a chunk
3. Drag them closer together
4. Export the mockup
5. Share with your AI/developer: "Make it look like THIS"

## File Structure

```
chrome-extension-mockup-tool/
├── manifest.json          # Extension config
├── popup/
│   ├── popup.html         # Extension popup
│   ├── popup.css
│   └── popup.js
├── editor/
│   ├── editor.html        # Main editor page
│   ├── editor.css
│   └── editor.js
├── background/
│   └── service-worker.js  # Background tasks
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   ├── icon128.png
│   └── generate-icons.html
└── README.md
```

## Troubleshooting

**Extension won't load**
- Make sure all icon files exist in the `icons/` folder
- Check Chrome's extension error log at `chrome://extensions/`

**Screenshot is blank**
- Some pages block screenshots (e.g., Netflix, banking sites)
- Try on a different page

**Chunks not dragging**
- Switch to Move tool (✋) or Select tool (✂️)
- Make sure you're clicking on the chunk, not the background

## License

MIT - Use however you want!
