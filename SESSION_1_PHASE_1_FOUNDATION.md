# Agent OS: Design Tree Studio - Session 1

## Phase 1: Foundation (MVP)

---

## 📋 STANDARDS LAYER

### Technology Stack
- **Framework:** Streamlit (Python web app)
- **Database:** SQLAlchemy ORM with PostgreSQL (Railway) or SQLite (local)
- **AI:** OpenAI API (GPT-4 Turbo)
- **Deployment:** Railway with Dockerfile

### Architecture
```
design-tree-studio/
├── app/
│   ├── core/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── database.py        # DB connection
│   │   └── repositories.py    # Data access
│   ├── services/
│   │   ├── chat_service.py    # OpenAI chat integration
│   │   ├── node_service.py    # Node CRUD operations
│   │   ├── baton_service.py   # Context handoff system
│   │   ├── node_detector.py   # Auto-detect nodes from chat
│   │   ├── process_log.py     # Logging service
│   │   └── agent_os_service.py  # [NEW] Agent OS generation
│   ├── ui/
│   │   ├── layout.py          # Main UI components
│   │   ├── node_tree_panel.py # Tree visualization
│   │   └── agent_os_panel.py  # [NEW] Agent OS display
│   └── streamlit_app.py       # Main entry point
```

### Coding Patterns
- **Services layer** for all business logic
- **Models** use SQLAlchemy with proper relationships
- **UI** uses Streamlit components with session state
- **Node model** uses `name` (not `title`) and `node_type` (not `domain`)

### Key Files to Understand First
- `app/services/node_detector.py` - Current auto-detection (you will enhance this)
- `app/ui/layout.py` - Main chat interface (you will add Agent OS tab here)
- `app/services/__init__.py` - All service exports (add new service here)

---

## 🎯 PRODUCT LAYER

### Vision
Turn stream-of-consciousness rants into production-ready Agent OS specs without stopping to organize. The brainstorm IS the documentation - it just needs real-time organization.

### Target Users
- "Vibe coders" who build with AI by talking/ranting
- Non-technical founders who think by speaking
- People who produce ideas faster than they can type

### Core Philosophy
1. Brainstorm = Documentation (same thing, just needs organizing)
2. Voice-first (speaking speed > typing speed)
3. Nothing ever lost (raw rant always preserved)
4. System teaches user (they learn Agent OS by using it)

---

## 🔧 SPEC LAYER

### Phase 1 Features to Build

#### Feature 1: Agent OS Document Structure

**Overview:**
Create the 3-layer document template that all Agent OS output will follow.

**Requirements:**
1. Template must have three layers: STANDARDS, PRODUCT, SPECS
2. Each layer has defined subsections (see format below)
3. Template should be reusable for any feature/project
4. Include GAPS/QUESTIONS section at the end
5. Include COMPLETION percentage tracker

**Agent OS Output Format:**
```markdown
# Agent OS: [Feature/Project Name]

## STANDARDS LAYER
### Technology Stack
- [Tech decisions mentioned]
### Architecture
- [Structural decisions]
### Coding Patterns
- [Style/pattern decisions]

---

## PRODUCT LAYER
### Vision
[What problem does this solve? Ultimate goal?]
### Target Users
[Who is this for?]
### Core Use Cases
1. [Use case 1]
2. [Use case 2]
### Roadmap
- Phase 1: [Current]
- Phase 2: [Next]
- Future: [Long-term]

---

## SPEC LAYER
### Feature: [Name]
#### Overview
[Brief description]
#### Requirements
**Functional:**
1. [Requirement 1]
**Technical:**
1. [Requirement 1]
#### User Stories
- As a [user], I want to [action] so that [benefit]
#### Acceptance Criteria
- [ ] [Criterion 1]
#### Technical Specification
- API Endpoints: [if any]
- Data Models: [if any]
- Dependencies: [what's needed first]
- Edge Cases: [what to handle]
#### Success Metrics
[How do we measure if this worked?]

---

## GAPS / QUESTIONS
- [ ] [Missing info 1]

## COMPLETION: [X]%
```

**Acceptance Criteria:**
- [ ] Template structure defined as Python class or data structure
- [ ] Can generate empty template
- [ ] Can populate template with content
- [ ] Can export to markdown string

---

#### Feature 2: Enhanced Detection (Classify to Agent OS Sections)

**Overview:**
Upgrade the existing `node_detector.py` to classify rant segments into Agent OS sections, not just nodes.

**Requirements:**
1. Analyze conversation text in real-time
2. Classify each piece of information to correct Agent OS location
3. Use this detection logic:

| User Says | Classification | Agent OS Location |
|-----------|---------------|-------------------|
| "I want it built in React" | Tech Decision | STANDARDS → Tech Stack |
| "This is for small remote teams" | Target User | PRODUCT → Target Users |
| "The whole point is simplicity" | Vision | PRODUCT → Vision |
| "Users need to create tasks fast" | Use Case | PRODUCT → Use Cases |
| "The dashboard shows all tasks" | Feature Requirement | SPEC → Requirements |
| "When they click, it should..." | User Story | SPEC → User Stories |
| "It has to work offline" | Technical Requirement | SPEC → Edge Cases |
| "Success means 2x faster" | Metric | SPEC → Success Metrics |
| "Should handle 1000 users" | Constraint | SPEC → Technical Spec |

4. Return structured data with classification and confidence score
5. Handle ambiguous statements gracefully

**Technical Specification:**
- Enhance `app/services/node_detector.py` OR create new `agent_os_detector.py`
- Use OpenAI API for classification
- Return JSON structure with: `{text, classification, agent_os_location, confidence}`

**Acceptance Criteria:**
- [ ] Can classify single statements
- [ ] Can classify full conversation
- [ ] Returns proper Agent OS locations
- [ ] Handles edge cases without crashing

---

#### Feature 3: Raw Rant Preservation

**Overview:**
ALWAYS keep original unstructured rant, no matter what processing happens.

**Requirements:**
1. Every word recorded verbatim
2. Never modify the original
3. Store with timestamp
4. Can always access source material
5. Separate from processed/organized version

**Technical Specification:**
- Add `raw_rant` field to appropriate model OR create new `RawRant` model
- Store in database with timestamps
- Link to session/project

**Acceptance Criteria:**
- [ ] Raw rant saved on every message
- [ ] Original text never modified
- [ ] Can retrieve full rant history
- [ ] Timestamps recorded

---

#### Feature 4: Simple Live Tree View

**Overview:**
Show ideas organizing into Agent OS structure as user talks.

**Requirements:**
1. Visual tree showing Agent OS layers
2. Updates in real-time as chat happens
3. Shows which sections have content
4. Expandable/collapsible sections
5. Build on existing `node_tree_panel.py` patterns

**Technical Specification:**
- Create `app/ui/agent_os_panel.py`
- Use Streamlit expanders or tree component
- Subscribe to detection results
- Update UI on each new classification

**Acceptance Criteria:**
- [ ] Tree displays three layers (Standards, Product, Specs)
- [ ] Shows subsections under each layer
- [ ] Indicates which sections have content
- [ ] Updates without full page refresh

---

#### Feature 5: Consolidate Button (Process Rant → Agent OS)

**Overview:**
One-click button to process entire rant and generate complete Agent OS document.

**Requirements:**
1. "Consolidate" or "Generate Agent OS" button in UI
2. Takes full conversation/rant as input
3. Runs through detection/classification
4. Outputs complete Agent OS document
5. Shows in panel and allows export

**Technical Specification:**
- Add button to `layout.py` or `agent_os_panel.py`
- Call `agent_os_service.py` to process
- Display result in expandable view
- Add "Copy" and "Download" options

**Acceptance Criteria:**
- [ ] Button visible in UI
- [ ] Processes current session's conversation
- [ ] Generates valid Agent OS markdown
- [ ] Can copy or download result

---

## 🎬 TASK

**Build Phase 1: Foundation**

Create the core Agent OS infrastructure:

1. **Create `app/services/agent_os_service.py`**
   - Agent OS template structure
   - Detection/classification logic
   - Document generation

2. **Create `app/ui/agent_os_panel.py`**
   - Live tree view component
   - Consolidate button
   - Output display

3. **Modify `app/ui/layout.py`**
   - Add Agent OS tab to main interface
   - Integrate new panel

4. **Modify `app/services/__init__.py`**
   - Export new service

5. **Ensure raw rant preservation**
   - Add storage mechanism
   - Never lose original text

---

## ✅ TESTING CHECKLIST

After implementation, verify:

- [ ] Can create empty Agent OS template
- [ ] Classification correctly identifies Standards vs Product vs Spec items
- [ ] Raw rant is preserved in database
- [ ] Live tree view shows in UI
- [ ] Tree updates when new content is classified
- [ ] Consolidate button generates complete document
- [ ] Generated document follows correct format
- [ ] Can copy/download generated document
- [ ] No errors in Process Log
- [ ] Works with existing chat flow (doesn't break anything)

---

## ⚠️ IMPORTANT NOTES

- **Don't break existing features** - Chat, nodes, baton system must still work
- **Raw rant is sacred** - Never modify or lose original text
- **User thinks by speaking** - Don't interrupt flow, queue questions
- **This is foundation** - Future phases build on this, make it solid

---

**End of Session 1 Spec**
