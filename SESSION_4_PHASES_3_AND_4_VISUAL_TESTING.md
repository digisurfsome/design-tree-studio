# Agent OS: Design Tree Studio - Session 4

## Phases 3 + 4: Visual Feedback & Flexibility/Testing

**Prerequisites:** Phases 1, 2A, and 2B must be complete. You should have:
- Full Agent OS service working
- Flash Labels, Gap Detection, Gap Percentage
- Click-to-Rant voice input working
- Real-Time Tagging with timestamps working
- Raw rant preservation working

---

## 📋 STANDARDS LAYER

### Technology Stack
- **Framework:** Streamlit (Python web app)
- **Database:** SQLAlchemy ORM with PostgreSQL (Railway) or SQLite (local)
- **AI:** OpenAI API (GPT-4 Turbo)
- **Editor Component:** Monaco-style or code block component (if available in Streamlit)
- **Deployment:** Railway with Dockerfile

### Architecture
```
design-tree-studio/
├── app/
│   ├── services/
│   │   ├── agent_os_service.py
│   │   ├── lab_service.py       # [NEW] Testing/config management
│   │   └── [existing services]
│   ├── ui/
│   │   ├── layout.py           # Add cockpit mode
│   │   ├── agent_os_panel.py   # Add overlays, multi-view
│   │   ├── lab_panel.py        # [NEW] Testing controls
│   │   └── [existing UI]
│   └── streamlit_app.py
```

---

## 🎯 PRODUCT LAYER

### Vision
Provide visual feedback that helps users see their ideas organizing AND give them controls to test different approaches to find what works best.

### Core Philosophy for This Phase
- Visual feedback matters - seeing ideas organize helps produce better ideas
- Test everything - don't hard-code one approach, build flexibility
- Cockpit mode - everything accessible, user decides what to use
- Data-driven decisions - learn what works through actual use

---

## 🔧 SPEC LAYER

### Phase 3 Features: Visual Feedback

---

#### Mechanism 12: Raw Rant + Tag Overlay Toggle

**What It Does:**
Toggle filter that shows tags overlaid on raw rant. See connections without losing original.

**How It Works:**
1. Default view: Raw text (clean, readable)
2. Toggle on: Tags appear inline as highlights/annotations
3. Hover on tag: Shows Agent OS location
4. Click on tag: Jumps to that section in Agent OS view

**Visual Design:**
```
DEFAULT (Tags Off):
"I want to build a task manager for small teams. The main
feature is a dashboard where you can see all tasks at once.
Users should be able to drag and drop to reorder..."

TOGGLE ON (Tags Visible):
"I want to build a task manager for small teams [VISION]. The main
feature is a dashboard where you can see all tasks at once [REQUIREMENT].
Users should be able to drag and drop to reorder [USER STORY]..."
```

**Requirements:**
1. Toggle button to show/hide tag overlay
2. Tags shown as inline highlights or badges
3. Different colors for different Agent OS sections
4. Hover shows full section path (e.g., "SPEC → Requirements → Functional")
5. Optional: Click tag to navigate
6. Raw text never modified - tags are overlay only

**Color Coding:**
- Standards: Blue
- Product (Vision, Users): Purple
- Spec (Requirements): Green
- Spec (User Stories): Orange
- Spec (Technical): Red
- Gaps/Questions: Yellow

**Acceptance Criteria:**
- [ ] Toggle button visible
- [ ] Tags appear as overlay when on
- [ ] Tags use section-appropriate colors
- [ ] Hover shows Agent OS location
- [ ] Raw text unchanged underneath
- [ ] Toggle off removes all overlays

---

#### Mechanism 13: Multi-Monaco Live Fill

**What It Does:**
Watch multiple Agent OS sections being filled simultaneously. Mini editor windows show cursors filling different sections at once.

**How It Works:**
1. As user rants, AI classifies content in real-time
2. Multiple small editor panels visible
3. Each panel = one Agent OS section
4. Content appears in appropriate panel as detected
5. Like watching a team of writers working simultaneously

**Visual Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Chat/Rant Area                                      │
├───────────────┬───────────────┬─────────────────────┤
│ 📝 Overview   │ 📋 Require... │ 👤 User Stories     │
│ ───────────── │ ───────────── │ ─────────────────── │
│ A task manager│ 1. Dashboard  │ As a PM, I want     │
│ for small...  │ 2. Drag/drop  │ to see all tasks... │
│               │ 3. Filter...  │                     │
├───────────────┼───────────────┼─────────────────────┤
│ ⚙️ Technical  │ ✓ Acceptance  │ 📊 Metrics          │
│ ───────────── │ ───────────── │ ─────────────────── │
│ REST API      │ [ ] Can view  │ (empty)             │
│ JSON response │ [ ] Can drag  │                     │
└───────────────┴───────────────┴─────────────────────┘
```

**Requirements:**
1. Grid of mini editor/display panels
2. One panel per Agent OS section (6-8 panels)
3. Content populates in real-time as classified
4. Visual indication when new content added (flash/highlight)
5. Empty sections show as placeholder
6. Scrollable if content exceeds panel size
7. Panel labels match Agent OS section names

**Technical Specification:**
- Use Streamlit columns or grid layout
- Each panel is expander or container
- Subscribe to classification events
- Animate new content appearance (if possible)
- Consider `streamlit-monaco-editor` for code-like feel (optional)

**Acceptance Criteria:**
- [ ] Grid of panels visible
- [ ] Panels labeled with section names
- [ ] Content appears as user rants
- [ ] New content highlights briefly
- [ ] Empty sections show placeholder
- [ ] All Agent OS sections represented

---

#### Mechanism 14: Click-to-Expand Live Fill

**What It Does:**
Any mini Monaco/editor window can expand for more detail.

**How It Works:**
1. User sees grid of mini panels
2. Click on any panel
3. Panel expands to larger view
4. See full context for that section
5. Click again or close button to shrink

**Requirements:**
1. Panels are clickable
2. Clicked panel expands (modal or in-place)
3. Expanded view shows full section content
4. Easy to close/shrink back
5. Multiple panels can be expanded (optional)
6. Can edit content in expanded view

**UI Behavior:**
- Option A: Modal popup with full content
- Option B: Panel grows in-place, others shrink
- Option C: Side panel slides out with content
- Recommendation: Start with Streamlit expander or modal

**Acceptance Criteria:**
- [ ] Can click on any panel
- [ ] Panel expands to show more
- [ ] Full content visible when expanded
- [ ] Can close/collapse panel
- [ ] Content editable when expanded (optional)

---

### Phase 4 Features: Flexibility & Testing

---

#### Mechanism 4: Cockpit Dashboard Mode

**What It Does:**
Like airplane cockpit - many small panels, all visible. Tap any to expand. Everything accessible at once.

**How It Works:**
1. Dashboard view with all tool panels visible
2. Each panel is a different feature/mode
3. Tap to expand any panel
4. Multiple can be expanded simultaneously
5. Drag to rearrange (optional)

**Panel Options:**
```
┌──────────┬──────────┬──────────┬──────────┐
│ 💬 Chat  │ 🌳 Tree  │ 📊 Gaps  │ 🎙️ Voice │
├──────────┼──────────┼──────────┼──────────┤
│ 📝 Spec  │ 🏷️ Tags  │ 💡 Ideas │ ⚙️ Config│
└──────────┴──────────┴──────────┴──────────┘
```

**Requirements:**
1. Grid layout with all main features
2. Each panel shows mini preview
3. Click to expand any panel
4. Click again to shrink
5. Visual indicator of expanded state
6. Remember user's preferred layout (optional)

**Technical Specification:**
- Alternative layout mode in `layout.py`
- Toggle between standard and cockpit mode
- Use session state for expanded panels
- Ensure all features accessible in both modes

**Acceptance Criteria:**
- [ ] Cockpit mode toggle available
- [ ] Grid of feature panels visible
- [ ] Each panel shows preview content
- [ ] Can expand any panel
- [ ] Can shrink panels back
- [ ] All features accessible

---

#### Mechanism 5: Independent Mode Testing

**What It Does:**
Test each approach separately before combining. Systematic way to find what works.

**How It Works:**
1. "Lab Mode" or "Test Mode" toggle
2. Select which feature to test in isolation
3. Use only that feature for a session
4. Track results/effectiveness
5. Compare different approaches with data

**Test Modes Available:**
- Only tagging mode (Real-Time Tagging)
- Only batch mode (Post-rant consolidation)
- Only flash labels (Visual prompts)
- Combined modes (after individual tests)

**Requirements:**
1. Lab Mode toggle/section
2. Ability to enable/disable individual features
3. Track usage metrics per mode
4. Notes/feedback capture per test
5. Comparison view of different approaches

**UI Specification:**
```
┌─────────────────────────────────────┐
│ 🧪 LAB MODE                         │
├─────────────────────────────────────┤
│ Active Test: Real-Time Tagging Only │
│                                     │
│ Features:                           │
│ [✓] Real-Time Tagging              │
│ [ ] Flash Labels                    │
│ [ ] Click-to-Rant                   │
│ [ ] Post-Rant Analysis              │
│                                     │
│ Session Notes:                      │
│ [________________________]          │
│                                     │
│ [Start Test] [End & Review]         │
└─────────────────────────────────────┘
```

**Acceptance Criteria:**
- [ ] Lab Mode toggle available
- [ ] Can select which features to enable
- [ ] Disabled features hidden/inactive
- [ ] Can add session notes
- [ ] Basic metrics tracked (time, completeness)

---

#### Lab Mode (Extended from Mechanism 5)

**What It Does:**
Structured testing environment for experimenting with different feature combinations.

**Requirements:**
1. Create test configurations
2. Save and name configurations
3. Switch between configurations
4. Track results per configuration
5. A/B testing support (optional)

**Acceptance Criteria:**
- [ ] Can create named configurations
- [ ] Configurations saved
- [ ] Can switch between saved configs
- [ ] Results tracked per config

---

#### Config Levers

**What It Does:**
Adjustable settings that change how features behave. Fine-tune without code changes.

**Settings to Expose:**
```
General:
- Auto-detect nodes: [On/Off]
- Detection sensitivity: [Low/Medium/High]
- Flash label timing: [Immediate/After 5s/Manual]

Voice:
- Transcription model: [Whisper-1/Local]
- Voice timeout: [5s/10s/30s/Continuous]

Display:
- Panel layout: [Standard/Cockpit]
- Color theme: [Default/High Contrast]
- Animation speed: [Off/Fast/Normal]

Agent OS:
- Required sections: [Minimal/Standard/Complete]
- Gap threshold: [50%/70%/90%]
- Auto-consolidate: [On/Off]
```

**Requirements:**
1. Settings panel with organized categories
2. Each setting clearly explained
3. Changes apply immediately (or on save)
4. Reset to defaults option
5. Settings persist per user/project

**Acceptance Criteria:**
- [ ] Settings panel accessible
- [ ] Settings organized by category
- [ ] Changes save and persist
- [ ] Reset to defaults works
- [ ] Settings affect feature behavior

---

## 🎬 TASK

**Build Phases 3 + 4: Visual & Testing Features**

1. **Enhance `app/ui/agent_os_panel.py`**
   - Tag Overlay Toggle
   - Multi-panel live fill view
   - Click-to-expand functionality

2. **Create `app/ui/lab_panel.py`**
   - Lab Mode controls
   - Feature toggles
   - Config management
   - Test notes capture

3. **Enhance `app/ui/layout.py`**
   - Cockpit mode layout option
   - Mode toggle (standard/cockpit)
   - Config settings panel

4. **Create `app/services/lab_service.py`**
   - Save/load configurations
   - Track test metrics
   - Manage feature flags

5. **Add settings storage**
   - User preferences
   - Feature configurations
   - Lab mode settings

---

## ✅ TESTING CHECKLIST

After implementation, verify:

**Tag Overlay:**
- [ ] Toggle shows/hides tags
- [ ] Tags appear as colored highlights
- [ ] Hover shows Agent OS location
- [ ] Raw text unchanged when toggled

**Multi-Panel View:**
- [ ] Grid of panels visible
- [ ] Content populates correctly
- [ ] New content highlights
- [ ] Empty sections show placeholder

**Click-to-Expand:**
- [ ] Panels are clickable
- [ ] Expansion works
- [ ] Full content visible when expanded
- [ ] Can collapse back

**Cockpit Mode:**
- [ ] Mode toggle works
- [ ] All features visible in grid
- [ ] Panels expand/collapse
- [ ] All features accessible

**Lab Mode:**
- [ ] Can toggle lab mode
- [ ] Can enable/disable features
- [ ] Disabled features hidden
- [ ] Can add notes
- [ ] Configurations saveable

**Config Levers:**
- [ ] Settings panel accessible
- [ ] Changes save properly
- [ ] Settings affect behavior
- [ ] Reset works

**Integration:**
- [ ] Works with all previous features
- [ ] Voice features still work
- [ ] No performance issues
- [ ] No layout breaks

---

## ⚠️ IMPORTANT NOTES

- **Visual polish matters here** - These features are about the experience
- **Don't over-engineer** - Simple implementations first, enhance later
- **User controls** - User decides what to see, what to test
- **Keep it fast** - UI should feel responsive
- **Mobile consideration** - Cockpit mode may need mobile alternative

---

**End of Session 4 Spec**
