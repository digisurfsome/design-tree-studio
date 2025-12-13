# Agent OS: Design Tree Studio - Session 3

## Phase 2B: Core Mechanisms - Input Methods

**Prerequisites:** Phases 1 and 2A must be complete. You should have:
- Agent OS service with detection/classification
- Live tree view working
- Flash Labels showing what's needed
- Gap Detection identifying missing sections
- Gap Percentage displaying completion

---

## 📋 STANDARDS LAYER

### Technology Stack
- **Framework:** Streamlit (Python web app)
- **Database:** SQLAlchemy ORM with PostgreSQL (Railway) or SQLite (local)
- **AI:** OpenAI API (GPT-4 Turbo)
- **Voice:** Browser Speech Recognition API (JavaScript) OR Streamlit audio component
- **Deployment:** Railway with Dockerfile

### Architecture
```
design-tree-studio/
├── app/
│   ├── services/
│   │   ├── agent_os_service.py  # Add tagging logic
│   │   ├── voice_service.py     # [NEW] Voice input handling
│   │   └── [existing services]
│   ├── ui/
│   │   ├── layout.py           # Add voice controls
│   │   ├── agent_os_panel.py   # Add click-to-rant, tagging UI
│   │   └── [existing UI]
│   └── streamlit_app.py
```

### Coding Patterns
- Services layer for all business logic
- UI uses Streamlit components with session state
- Voice integration via browser API or Streamlit component
- Preserve raw rant always - tagged version is overlay

---

## 🎯 PRODUCT LAYER

### Vision
Enable voice-first input where users can speak continuously and either target specific fields OR tag sections as they go. No typing. No stopping. Tap and talk at speed of thought.

### Core Philosophy for This Phase
- Voice-first, not type-first
- One continuous rant with organization happening simultaneously
- Two outputs: raw rant (preserved) + tagged structure
- Rant stays natural, organization happens in parallel

### Why This Matters
This is the "core innovation" - Real-Time Tagging is described as "nothing like it exists." These mechanisms are what make the tool revolutionary.

---

## 🔧 SPEC LAYER

### This Session: 2 Mechanisms (Complex)

---

#### Mechanism 2: Click-to-Rant (Tap and Talk)

**What It Does:**
Click on a label/field, then speak - voice fills ONLY that field.

**How It Works:**
1. User sees Flash Labels: [Overview] [Requirements] [User Stories] [Technical]
2. User taps "Requirements"
3. Microphone activates
4. Everything user speaks goes into Requirements section
5. User taps another label to switch targets
6. User taps "Stop" or same label to end

**User Flow:**
```
1. See labels for current feature
2. Tap [User Stories]
3. Speak: "As a project manager, I want to see all tasks in one view..."
4. Tap [Technical Spec]
5. Speak: "This needs a REST API endpoint, returns JSON..."
6. Tap [Done] or tap again to stop
```

**Requirements:**
1. Clickable Flash Labels that activate target mode
2. Voice input captures speech-to-text
3. Voice content routes to selected Agent OS section
4. Visual indicator of which section is active
5. Easy way to switch sections mid-rant
6. Stop/pause functionality
7. Works on desktop browsers (mobile nice-to-have)

**Voice Input Options:**
- **Option A:** Browser Web Speech API (JavaScript)
  - Works in Chrome, Edge
  - Free, no API cost
  - Requires custom Streamlit component or JS injection

- **Option B:** Streamlit audio input + Whisper API
  - Record audio in Streamlit
  - Send to OpenAI Whisper for transcription
  - More reliable but costs per use

- **Recommendation:** Start with Option B (Whisper) for reliability, consider Option A later for real-time

**UI Specification:**
- Labels become clickable when voice mode enabled
- Active label highlighted (glow, border, color change)
- Microphone icon shows recording state
- "Recording to: [Section Name]" indicator
- Stop button always visible

**Technical Specification:**
- Add voice recording component to UI
- Create `voice_service.py` for transcription handling
- Modify Flash Labels to be interactive
- Route transcribed text to selected section in Agent OS
- Update Agent OS document in real-time

**Acceptance Criteria:**
- [ ] Can tap label to select target section
- [ ] Voice recording activates when section selected
- [ ] Speech is transcribed to text
- [ ] Text appears in correct Agent OS section
- [ ] Can switch sections while recording
- [ ] Can stop recording
- [ ] Visual feedback shows active section
- [ ] Raw rant preserved separately

---

#### Mechanism 3: Real-Time Tagging (Tag While Ranting)

**What It Does:**
One continuous rant, but tap buttons to TAG sections as you go. Talk continuously + tap to tag = organized output without stopping flow.

**How It Works:**
1. User starts continuous voice recording (one long rant)
2. As they speak, they tap buttons to mark sections
3. Backend tracks timestamps: "0:00-0:45 = Overview, 0:45-1:30 = Requirements..."
4. Output: Two versions
   - Raw rant (complete, unmodified)
   - Tagged/organized structure (split by timestamps)

**User Flow:**
```
1. Tap [Start Rant]
2. Start speaking about your feature
3. When you start talking about requirements, tap [Requirements] button
4. Keep talking... when you switch to user stories, tap [User Stories]
5. Keep talking... tap more tags as you naturally switch topics
6. Tap [End Rant]
7. System shows: Raw rant + Organized version with tagged sections
```

**Requirements:**
1. Continuous voice recording (not stop/start)
2. Tag buttons for each Agent OS section
3. Timestamp tracking for each tag tap
4. Split transcription by timestamps
5. Display both raw and organized versions
6. Toggle to switch between views
7. Never lose raw version

**Tag Button Panel:**
```
┌─────────────────────────────────────────┐
│  🎙️ Recording: 02:34                    │
├─────────────────────────────────────────┤
│ [Overview] [Requirements] [User Stories]│
│ [Technical] [Acceptance] [Metrics]      │
├─────────────────────────────────────────┤
│  Currently tagging: Requirements (0:45) │
│  Previous: Overview (0:00-0:45)         │
└─────────────────────────────────────────┘
```

**Timestamp Data Structure:**
```python
{
  "raw_transcript": "Full unmodified text...",
  "total_duration": 180,  # seconds
  "tags": [
    {"section": "Overview", "start": 0, "end": 45, "text": "..."},
    {"section": "Requirements", "start": 45, "end": 90, "text": "..."},
    {"section": "User Stories", "start": 90, "end": 140, "text": "..."},
    {"section": "Technical", "start": 140, "end": 180, "text": "..."}
  ]
}
```

**Technical Specification:**

1. **Recording Mode:**
   - Start continuous recording
   - Store audio or stream to transcription
   - Track recording duration

2. **Tagging System:**
   - Tag buttons with timestamps
   - Store tag events: {section, timestamp}
   - Allow changing current tag mid-rant

3. **Post-Processing:**
   - Get full transcription
   - Split by timestamp markers
   - Map text segments to tags
   - Generate organized Agent OS structure

4. **Storage:**
   - Save raw transcript (never modify)
   - Save tag data
   - Save organized version
   - Link all three together

**UI Specification:**

**Recording Panel:**
- Large "Start Rant" button
- Recording time display
- Tag buttons (highlight when tapped)
- Current tag indicator
- Tag history (scrolling list)
- "End Rant" button

**Results Panel:**
- Toggle: [Raw Rant] [Organized]
- Raw view: Full text, timestamps visible as subtle markers
- Organized view: Agent OS sections with content
- Hover on organized: shows original timestamp

**Acceptance Criteria:**
- [ ] Can start continuous recording
- [ ] Tag buttons work during recording
- [ ] Timestamps tracked for each tag
- [ ] Can switch tags mid-rant
- [ ] Recording stops cleanly
- [ ] Full transcription generated
- [ ] Text split by timestamps correctly
- [ ] Raw rant preserved completely
- [ ] Organized version shows tagged sections
- [ ] Can toggle between raw and organized views
- [ ] Tag overlay visible on raw view (optional)

---

## 🎬 TASK

**Build Phase 2B: Input Methods**

1. **Create `app/services/voice_service.py`**
   - Voice recording handling
   - Transcription (Whisper API)
   - Timestamp tracking
   - Tag management

2. **Enhance `app/ui/agent_os_panel.py`**
   - Click-to-Rant: Make Flash Labels clickable
   - Recording UI components
   - Tagging panel for Real-Time Tagging
   - Raw vs Organized toggle view

3. **Enhance `app/services/agent_os_service.py`**
   - Accept tagged content
   - Split transcripts by timestamp
   - Generate Agent OS from tagged rant
   - Store both raw and organized

4. **Add models/storage** (if needed)
   - Store raw rants with timestamps
   - Store tag data
   - Link to Agent OS documents

5. **Update `app/ui/layout.py`**
   - Voice controls accessible
   - Recording state visible

---

## ✅ TESTING CHECKLIST

After implementation, verify:

**Click-to-Rant:**
- [ ] Flash Labels are clickable
- [ ] Tapping label activates voice input
- [ ] Recording indicator visible
- [ ] "Recording to: [Section]" shows current target
- [ ] Speech transcribes correctly
- [ ] Text goes to correct Agent OS section
- [ ] Can switch sections mid-recording
- [ ] Can stop recording
- [ ] Content appears in Agent OS document

**Real-Time Tagging:**
- [ ] "Start Rant" begins continuous recording
- [ ] Recording timer displays
- [ ] Tag buttons work while recording
- [ ] Tapping tag records timestamp
- [ ] Current tag indicator updates
- [ ] Can tap new tag to switch
- [ ] "End Rant" stops recording
- [ ] Full transcript generated
- [ ] Transcript split by timestamps
- [ ] Each section has correct text
- [ ] Raw rant preserved completely
- [ ] Organized view shows Agent OS sections
- [ ] Can toggle between views
- [ ] Tags visible as overlay on raw (optional)

**Integration:**
- [ ] Works with existing Flash Labels
- [ ] Works with Gap Detection
- [ ] Updates completion percentage
- [ ] Consolidate button still works
- [ ] Doesn't break previous features

---

## ⚠️ IMPORTANT NOTES

- **Voice is the priority** - Typing should be secondary
- **Never lose raw rant** - Always preserve original, organized is just a view
- **This is the innovation** - Real-Time Tagging is unique, make it work well
- **Browser support** - Test in Chrome first, document limitations
- **Graceful degradation** - If voice fails, allow manual text entry as fallback

---

## 🔧 TECHNICAL CONSIDERATIONS

**Streamlit Voice Limitations:**
- Streamlit doesn't have native continuous audio recording
- May need `streamlit-webrtc` or custom component
- Consider audio file upload as fallback

**Transcription Approach:**
- Short recordings (<1 min): Full Whisper API call
- Long recordings: May need chunking
- Real-time: Would need streaming (complex, defer for now)

**Timestamp Accuracy:**
- Web Speech API can provide word-level timestamps
- Whisper provides segment-level timestamps
- May need to estimate exact boundaries

---

**End of Session 3 Spec**
