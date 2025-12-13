# Agent OS: Design Tree Studio - Session 2

## Phase 2A: Core Mechanisms - Detection & Display

**Prerequisites:** Phase 1 must be complete. You should have:
- `app/services/agent_os_service.py` exists and working
- `app/ui/agent_os_panel.py` exists with live tree view
- Agent OS tab visible in main layout
- Detection/classification logic working
- Consolidate button functional

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
│   ├── services/
│   │   ├── agent_os_service.py  # Enhance for gap detection
│   │   └── [existing services]
│   ├── ui/
│   │   ├── layout.py          # Add flash labels
│   │   ├── agent_os_panel.py  # Add gap percentage display
│   │   └── [existing UI]
│   └── streamlit_app.py
```

### Coding Patterns
- Services layer for all business logic
- UI uses Streamlit components with session state
- Follow existing patterns in codebase

---

## 🎯 PRODUCT LAYER

### Vision
Guide the user's rant by showing what's needed and what's missing - without interrupting their flow.

### Core Philosophy for This Phase
- Flash Labels show what's NEEDED, not what's been SAID
- Gap Detection finds what's MISSING, not what's been captured
- User learns Agent OS structure by seeing it in action
- Don't interrupt - display information passively

---

## 🔧 SPEC LAYER

### This Session: 3 Mechanisms

---

#### Mechanism 1: Flash Labels (Real-Time Prompts)

**What It Does:**
When a new idea/branch is created, show what Agent OS fields still need filling. Labels flash/display on screen to guide the rant.

**How It Works:**
1. User starts talking about a new feature or concept
2. System detects this is a new branch/topic
3. Flash labels appear: [Overview] [Requirements] [User Stories] [Technical] [Metrics]
4. As user covers each area, that label dims or gets checkmark
5. Remaining labels stay visible as prompts

**Requirements:**
1. Labels for all Agent OS Spec subsections:
   - Overview
   - Requirements (Functional)
   - Requirements (Technical)
   - User Stories
   - Acceptance Criteria
   - Technical Specification
   - Success Metrics
2. Labels appear when new feature/topic detected
3. Labels update in real-time as content is classified
4. Visual distinction between filled vs unfilled
5. Non-intrusive - shouldn't block content

**UI Specification:**
- Position: Near the Agent OS panel or above chat
- Style: Pill-shaped labels or tags
- States: Empty (bright/pulsing), Partial (dimmed), Complete (checkmark or green)
- Clickable: Clicking a label could scroll to that section (optional)

**Technical Specification:**
- Track which Agent OS sections have content
- Compare against full template to find gaps
- Update UI on each new classification
- Store section completion state in session state

**Acceptance Criteria:**
- [ ] Labels appear for new features/topics
- [ ] Labels show correct Agent OS sections
- [ ] Labels update when content is detected
- [ ] Visual difference between empty/filled states
- [ ] Doesn't interrupt user flow

---

#### Mechanism 7: Gap Detection

**What It Does:**
System identifies what's missing from the Agent OS spec. Tells user "You covered X, Y, Z but missing A, B."

**How It Works:**
1. System tracks all Agent OS sections
2. Compares what's been filled vs what's needed
3. Identifies specific gaps
4. Can prompt user to fill gaps (without interrupting flow)

**Requirements:**
1. Analyze current Agent OS document completeness
2. List all empty/incomplete sections
3. Prioritize gaps by importance
4. Provide specific prompts for what's missing
5. Allow user to voice-fill gaps on demand

**Gap Analysis Logic:**
```
Required sections = [Overview, Requirements, User Stories, Acceptance Criteria, Technical Spec]
Optional sections = [Success Metrics, Edge Cases, Dependencies]

For each required section:
  - Empty = Critical gap
  - Partial (< 2 items) = Minor gap
  - Complete (2+ items) = Filled

Output: List of gaps with severity and suggested prompts
```

**Example Output:**
```
GAPS DETECTED:
❌ User Stories - No user stories captured yet
   Prompt: "Who will use this? What do they want to do?"

⚠️ Technical Spec - Only partial info
   Prompt: "What API endpoints or data models are needed?"

❌ Acceptance Criteria - Empty
   Prompt: "How do we know when this is done?"
```

**Technical Specification:**
- Add `detect_gaps()` method to `agent_os_service.py`
- Return structured gap data with severity and prompts
- Integrate with UI to display gaps

**Acceptance Criteria:**
- [ ] Correctly identifies empty sections
- [ ] Distinguishes between partial and empty
- [ ] Provides helpful prompts for each gap
- [ ] Updates as content is added
- [ ] Works with consolidate function

---

#### Mechanism 15: Gap Percentage + Fill Request

**What It Does:**
Show exact completion percentage and itemized list of what's missing.

**Display:**
```
Agent OS: 87% complete
Missing: 8 items across 5 sections

[View Gaps] → Expands to show:
- User Stories (0/2 minimum)
- Acceptance Criteria (0/3 minimum)
- Technical Spec: API Endpoints (empty)
- Technical Spec: Data Models (empty)
- Success Metrics (0/1 minimum)
```

**Requirements:**
1. Calculate percentage based on weighted sections
2. Show percentage prominently in UI
3. List specific missing items
4. Make it feel like progress (gamification)
5. "Fill Request" button to help complete gaps

**Percentage Calculation:**
```
Section Weights:
- Overview: 10%
- Requirements (Functional): 15%
- Requirements (Technical): 10%
- User Stories: 15%
- Acceptance Criteria: 15%
- Technical Spec: 20%
- Success Metrics: 10%
- Gaps/Questions: 5%

Each section score = (items_filled / minimum_required) * weight
Total = sum of all section scores, capped at 100%
```

**UI Specification:**
- Circular progress indicator OR progress bar
- Percentage number prominently displayed
- Color coding: Red (<50%), Yellow (50-80%), Green (>80%)
- Expandable details section
- "Help me complete" button for AI-assisted gap filling

**Fill Request Feature:**
When user clicks "Help me complete" or similar:
1. AI generates questions for missing sections
2. Questions are queued (not interrupting)
3. User can answer when ready
4. Answers auto-populate Agent OS sections

**Acceptance Criteria:**
- [ ] Percentage displays correctly
- [ ] Updates in real-time as content added
- [ ] Color coding works
- [ ] Can expand to see specific gaps
- [ ] Fill request generates helpful questions
- [ ] Answers populate correct sections

---

## 🎬 TASK

**Build Phase 2A: Detection & Display Mechanisms**

1. **Enhance `app/services/agent_os_service.py`**
   - Add `detect_gaps()` method
   - Add `calculate_completion_percentage()` method
   - Add `generate_fill_prompts()` method
   - Add section tracking logic

2. **Enhance `app/ui/agent_os_panel.py`**
   - Add Flash Labels component
   - Add Gap Percentage display
   - Add expandable gap details
   - Add "Fill Request" button

3. **Update `app/ui/layout.py`** (if needed)
   - Ensure Flash Labels visible during chat
   - Position appropriately

4. **Add session state tracking**
   - Track which sections have content
   - Track completion percentage
   - Update in real-time

---

## ✅ TESTING CHECKLIST

After implementation, verify:

**Flash Labels:**
- [ ] Labels appear when talking about new feature
- [ ] Correct labels shown for Agent OS sections
- [ ] Labels update as content detected
- [ ] Filled sections visually distinct
- [ ] Doesn't interrupt chat flow

**Gap Detection:**
- [ ] Empty sections correctly identified
- [ ] Partial sections correctly identified
- [ ] Helpful prompts generated for each gap
- [ ] Updates when new content added

**Gap Percentage:**
- [ ] Percentage calculates correctly
- [ ] Progress display shows in UI
- [ ] Color coding works (red/yellow/green)
- [ ] Can expand to see specific gaps
- [ ] Fill Request generates questions
- [ ] Answering questions fills sections

**Integration:**
- [ ] Works with existing chat flow
- [ ] Works with Consolidate button
- [ ] Doesn't break Phase 1 features
- [ ] No errors in Process Log

---

## ⚠️ IMPORTANT NOTES

- **Don't interrupt flow** - These features DISPLAY information, they don't demand input
- **Passive guidance** - User sees what's needed without being forced to fill it
- **Gamification** - The percentage should feel motivating, not stressful
- **Queue, don't interrupt** - Fill requests are offered, not required

---

**End of Session 2 Spec**
