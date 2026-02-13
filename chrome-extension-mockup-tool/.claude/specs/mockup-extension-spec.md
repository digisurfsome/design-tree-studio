# Agent OS Spec: UI Mockup Chrome Extension

## 📋 STANDARDS LAYER

### Technology Stack
- **Platform**: Chrome Extension (Manifest V3)
- **Languages**: JavaScript, HTML5, CSS3
- **APIs**: Chrome Tabs API, Chrome Downloads API, HTML5 Canvas
- **Libraries**: None (vanilla JS for lightweight extension)

### Architecture
```
chrome-extension-mockup-tool/
├── manifest.json          # Extension config (Manifest V3)
├── popup/
│   ├── popup.html         # Extension popup UI
│   ├── popup.css          # Popup styles
│   └── popup.js           # Popup logic
├── content/
│   └── content.js         # Injected into pages
├── editor/
│   ├── editor.html        # Full mockup editor page
│   ├── editor.css         # Editor styles
│   └── editor.js          # Canvas manipulation logic
├── background/
│   └── service-worker.js  # Background service worker
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Coding Patterns
- Event-driven architecture
- Canvas-based rendering for performance
- State management via simple object store
- No external dependencies

---

## 🎯 PRODUCT LAYER

### Vision
A Chrome extension that lets developers quickly screenshot any web app, select UI chunks, drag them around to create layout mockups, and export the result - eliminating the communication gap between vision and implementation.

### Target Users
- Non-technical founders building apps with AI
- Developers who need to quickly mockup UI changes
- Anyone who struggles to communicate "tighten up the spacing"

### Core Use Cases
1. **Screenshot & Chunk**: Capture page, lasso UI elements, make them draggable
2. **Rearrange Layout**: Drag chunks to show desired spacing/arrangement
3. **Annotate**: Add arrows, text, rectangles to highlight changes
4. **Export**: Save mockup as PNG to share with AI/devs

### Value Proposition
"Show, don't tell" - Instead of explaining "make it tighter," show exactly what you want.

---

## 🔧 SPEC LAYER

### Feature: Core Mockup Tool

#### User Flow
1. User clicks extension icon on any webpage
2. Popup shows "Capture Page" button
3. Click captures visible viewport as image
4. Opens editor in new tab with screenshot
5. User draws rectangles around UI chunks
6. Each chunk becomes a draggable layer
7. User drags chunks to desired positions
8. User adds annotations (optional)
9. User clicks "Export" to download PNG

#### Functional Requirements

**FR1: Screenshot Capture**
- Capture visible viewport with one click
- Works on any website
- Preserves full resolution

**FR2: Chunk Selection Tool**
- Rectangle selection mode
- Draw box around any area
- Selected area becomes "chunk" (draggable layer)
- Visual indicator shows selected chunks
- Can create unlimited chunks

**FR3: Chunk Manipulation**
- Click and drag any chunk to move it
- Chunks maintain their visual content
- Layering: most recently selected on top
- Delete chunk option (right-click or X button)

**FR4: Annotation Tools**
- Arrow tool: Draw arrows to point at things
- Rectangle tool: Draw outlined rectangles
- Text tool: Add text labels
- Color picker: Red, blue, green, yellow, black
- Line thickness: thin, medium, thick

**FR5: Export**
- "Export PNG" button
- Downloads composite image
- Filename: mockup-[timestamp].png

#### UI Specification

**Popup (200x150px)**
```
┌─────────────────────┐
│   🎨 UI Mockup      │
│                     │
│  [Capture Page]     │
│                     │
│  Keyboard: Alt+M    │
└─────────────────────┘
```

**Editor (Full Tab)**
```
┌─────────────────────────────────────────────────┐
│ Toolbar                                          │
│ [Select] [Arrow] [Rect] [Text] | Colors | [Export] │
├─────────────────────────────────────────────────┤
│                                                  │
│                                                  │
│            Canvas Area                           │
│         (Screenshot + Chunks)                    │
│                                                  │
│                                                  │
├─────────────────────────────────────────────────┤
│ Status: Ready | Chunks: 3 | Zoom: 100%          │
└─────────────────────────────────────────────────┘
```

#### Technical Specification

**Screenshot Capture**
```javascript
// Use chrome.tabs.captureVisibleTab
chrome.tabs.captureVisibleTab(null, {format: 'png'}, (dataUrl) => {
  // Send to editor
});
```

**Chunk Data Structure**
```javascript
{
  id: 'chunk-001',
  x: 100,           // Current position
  y: 150,
  width: 200,
  height: 80,
  originalX: 100,   // Where it was cut from
  originalY: 150,
  imageData: '...'  // Canvas image data
}
```

**Canvas Layers**
1. Base layer: Original screenshot (static)
2. Hole layer: Black/gray where chunks were cut
3. Chunk layers: Draggable pieces
4. Annotation layer: Arrows, text, shapes

#### Acceptance Criteria
- [ ] Extension installs without errors
- [ ] Capture works on any website
- [ ] Can create 5+ chunks without lag
- [ ] Chunks drag smoothly (60fps)
- [ ] Annotations render clearly
- [ ] Export produces valid PNG
- [ ] Works in Chrome 120+

#### Edge Cases
- Very long pages (only capture visible)
- Pages with iframes (capture visible only)
- Dark mode pages (preserve colors)
- High DPI displays (handle devicePixelRatio)

---

## 🎬 TASK

Build the complete Chrome extension following this spec. Create all files, make it installable as an unpacked extension, and ready to use.
