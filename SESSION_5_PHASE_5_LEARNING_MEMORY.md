# Agent OS: Design Tree Studio - Session 5

## Phase 5: Learning & Memory

**Prerequisites:** Phases 1-4 must be complete. You should have:
- Full Agent OS system working
- All core mechanisms functional
- Visual feedback features working
- Lab Mode and Config levers working

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
│   │   ├── idea_bank_service.py  # [NEW] Idea management
│   │   ├── session_service.py    # [NEW] Pause/resume logic
│   │   └── [existing services]
│   ├── ui/
│   │   ├── layout.py
│   │   ├── idea_bank_panel.py    # [NEW] Idea bank UI
│   │   └── [existing UI]
│   └── streamlit_app.py
```

---

## 🎯 PRODUCT LAYER

### Vision
Create a system that grows WITH the user - remembering their best ideas, adapting to time away, and learning their patterns.

### Core Philosophy for This Phase
- Idea Bank is NOT "save for later" - it's "use every day until it's in your DNA"
- Ideas compound with repetition
- Time away determines context refresh depth
- System adapts to the user's patterns

---

## 🔧 SPEC LAYER

### This Session: 2 Mechanisms + Polish

---

#### Mechanism 11: Idea Bank (Daily Warmup)

**What It Does:**
Bank of best ideas reviewed DAILY when logging in. Not a graveyard of saved ideas - a daily practice.

**How It Works:**
1. User logs in
2. First thing shown: Top ideas from the Idea Bank
3. Review for a few minutes
4. Build confidence, remember what you're building
5. Then proceed to work

**The Concept:**
Most "save for later" systems become graveyards. This is different:
- Ideas are ACTIVELY surfaced every login
- User sees them until they're internalized
- Like flashcards for your own brilliant ideas
- Builds confidence before starting work

**Idea Sources:**
- Manually starred/saved by user
- AI-detected "high value" statements
- Completed Agent OS sections marked as "exemplary"
- Patterns that appear frequently in rants

**Requirements:**
1. Save ideas to bank (manual + auto-detect)
2. Display ideas on login/session start
3. Rate/rank ideas (most important first)
4. Retire ideas when "learned" (internalized)
5. Different categories of ideas
6. Quick add from any rant content
7. Daily warmup mode

**Idea Structure:**
```python
{
  "id": "uuid",
  "content": "The text of the idea",
  "source": "rant|manual|ai_detected",
  "category": "vision|feature|insight|pattern",
  "rating": 5,  # 1-5 stars
  "times_shown": 12,
  "last_shown": "2024-01-15",
  "status": "active|retired|archived",
  "project_id": "uuid",
  "created_at": "timestamp"
}
```

**UI Specification:**

**Warmup Modal (on login):**
```
┌─────────────────────────────────────────────┐
│ ☀️ DAILY WARMUP                              │
│ ─────────────────────────────────────────── │
│                                             │
│ 💡 "The brainstorm IS the documentation"    │
│    ⭐⭐⭐⭐⭐  |  Vision  |  Shown 12x       │
│                                             │
│ 💡 "Voice-first, not type-first"            │
│    ⭐⭐⭐⭐☆  |  Pattern  |  Shown 8x        │
│                                             │
│ 💡 "Never interrupt flow state"             │
│    ⭐⭐⭐⭐⭐  |  Insight  |  Shown 15x       │
│                                             │
│ [Got it - Start Working]  [Add to Bank]     │
└─────────────────────────────────────────────┘
```

**Idea Bank Tab:**
```
┌─────────────────────────────────────────────┐
│ 💡 IDEA BANK                  [+ Add Idea]  │
├─────────────────────────────────────────────┤
│ Filter: [All] [Vision] [Features] [Insights]│
├─────────────────────────────────────────────┤
│ ⭐⭐⭐⭐⭐ "The brainstorm IS the..."       │
│ Vision | Active | Shown 12x | [Retire]      │
│                                             │
│ ⭐⭐⭐⭐☆ "Voice-first approach..."         │
│ Pattern | Active | Shown 8x | [Retire]      │
│                                             │
│ ⭐⭐⭐☆☆ "Consider timestamp..."            │
│ Feature | Active | Shown 3x | [Retire]      │
└─────────────────────────────────────────────┘
```

**Quick Add Feature:**
- Select any text in rant
- "Add to Idea Bank" button appears
- Categorize and rate
- Saved to bank

**Acceptance Criteria:**
- [ ] Can save ideas manually
- [ ] Ideas shown on login/warmup
- [ ] Ideas have ratings (stars)
- [ ] Ideas have categories
- [ ] Track times shown
- [ ] Can retire ideas
- [ ] Filter by category
- [ ] Quick add from rant content
- [ ] Warmup dismissible but encouraged

---

#### Mechanism 16: Pause/Resume with Context Refresh

**What It Does:**
Pause work, come back later with appropriately scaled context refresh based on time away.

**How It Works:**
- Away 1 hour → Quick summary: "Here's where you left off..."
- Away 1 day → Medium refresh: Key points + recent work
- Away 1 week → Full walkthrough: Complete context restoration

**Time-Based Scaling:**
```
< 1 hour:    Minimal - Just current task
1-4 hours:   Brief - Current task + recent decisions
4-24 hours:  Medium - Session summary + key context
1-3 days:    Full - Project overview + session recap
3-7 days:    Extended - Full project refresh + what you were working on
7+ days:     Complete - Full onboarding-style refresh
```

**Requirements:**
1. Track last active timestamp
2. Calculate time away on return
3. Generate appropriate refresh content
4. Scale depth based on time away
5. Quick "I remember, skip refresh" option
6. Save pause state for clean resume

**Refresh Content by Level:**

**Minimal (< 1 hour):**
```
"Welcome back! You were working on: [Feature Name]
Last thing you said: [Last rant excerpt]
Continue?"
```

**Brief (1-4 hours):**
```
"You've been away for 2 hours.

Working on: [Feature Name]
Recent decisions:
- Chose REST API over GraphQL
- Dashboard will have 3 main panels

Agent OS: 67% complete
[Continue] [Show More Context]"
```

**Medium (4-24 hours):**
```
"Welcome back! It's been [X] hours.

PROJECT: [Name]
Currently building: [Feature]

Session Summary:
- Started [Feature] spec
- Defined 5 requirements
- Captured 3 user stories
- Outstanding: Technical spec, acceptance criteria

Agent OS: 67% complete
Key gaps: [List]

[Dive In] [Full Refresh] [Start Fresh]"
```

**Full (1-7+ days):**
```
"Welcome back! It's been [X] days.

PROJECT OVERVIEW:
[Full project summary]

WHAT YOU WERE BUILDING:
[Feature description]

WHERE YOU LEFT OFF:
[Detailed session state]

KEY IDEAS (from Idea Bank):
[Top 3 ideas]

AGENT OS STATUS:
[Completion breakdown by section]

RECOMMENDED NEXT STEPS:
1. [Suggestion]
2. [Suggestion]

[Continue Work] [Review Full Spec] [Start Something New]"
```

**Technical Specification:**

1. **Timestamp Tracking:**
   - Record last activity on every action
   - Store in session/user data
   - Calculate delta on return

2. **Refresh Generation:**
   - Pull relevant data based on time level
   - Summarize using AI if needed
   - Cache summaries for quick access

3. **Session State:**
   - Save current feature being worked on
   - Save last rant/activity
   - Save Agent OS completion state
   - Save any pending gaps

4. **UI:**
   - Modal or panel on return
   - Appropriate content for time away
   - Skip option always available
   - "Show more" to go deeper

**Acceptance Criteria:**
- [ ] Last activity timestamp tracked
- [ ] Time away calculated on return
- [ ] Correct refresh level selected
- [ ] Minimal refresh works (< 1 hour)
- [ ] Brief refresh works (1-4 hours)
- [ ] Medium refresh works (4-24 hours)
- [ ] Full refresh works (1+ days)
- [ ] Skip option available
- [ ] Content is relevant and helpful
- [ ] Clean resume to previous state

---

### Polish & Cleanup

This session also includes time for polish:

**Items to Review:**
1. **UI Consistency** - All panels match in style
2. **Error Handling** - Graceful failures everywhere
3. **Loading States** - Show progress, not blank screens
4. **Mobile Check** - Basic functionality on smaller screens
5. **Performance** - No slow operations blocking UI
6. **Edge Cases** - Empty states, long content, special characters

**Testing Full Flow:**
1. New user starts project
2. Rants about feature
3. Uses Real-Time Tagging
4. Views Multi-Panel fill
5. Checks Gap Percentage
6. Saves ideas to Bank
7. Closes session
8. Returns after time
9. Gets context refresh
10. Continues seamlessly

---

## 🎬 TASK

**Build Phase 5: Learning & Memory**

1. **Create `app/services/idea_bank_service.py`**
   - Save/retrieve ideas
   - Rating and categorization
   - Times shown tracking
   - Retire logic
   - Auto-detect valuable ideas

2. **Create `app/ui/idea_bank_panel.py`**
   - Idea Bank tab UI
   - Warmup modal on login
   - Quick add interface
   - Filter and sort controls

3. **Create `app/services/session_service.py`**
   - Activity timestamp tracking
   - Time away calculation
   - Refresh content generation
   - Session state management

4. **Enhance `app/ui/layout.py`**
   - Warmup modal integration
   - Context refresh display
   - Add Idea Bank tab

5. **Add models** (if needed)
   - Idea model (SQLAlchemy)
   - Session state storage

6. **Polish pass on all features**
   - UI consistency
   - Error handling
   - Loading states
   - Edge cases

---

## ✅ TESTING CHECKLIST

After implementation, verify:

**Idea Bank:**
- [ ] Can add ideas manually
- [ ] Can quick-add from rant
- [ ] Ideas display on warmup
- [ ] Rating system works
- [ ] Categories work
- [ ] Filter/sort works
- [ ] Times shown tracked
- [ ] Can retire ideas
- [ ] Warmup modal appears on login

**Pause/Resume:**
- [ ] Activity timestamps recorded
- [ ] Time away calculated correctly
- [ ] Minimal refresh (< 1 hour)
- [ ] Brief refresh (1-4 hours)
- [ ] Medium refresh (4-24 hours)
- [ ] Full refresh (1+ days)
- [ ] Content is relevant
- [ ] Skip option works
- [ ] Resumes to correct state

**Full Flow:**
- [ ] Complete user journey works
- [ ] All features integrate properly
- [ ] No broken features
- [ ] Performance acceptable
- [ ] UI consistent throughout

**Edge Cases:**
- [ ] Empty idea bank handled
- [ ] First-time user (no history)
- [ ] Very long time away
- [ ] Corrupted session state
- [ ] Multiple projects

---

## ⚠️ IMPORTANT NOTES

- **Idea Bank is active, not passive** - It's a daily practice, not storage
- **Respect user time** - Refresh should help, not annoy
- **Skip always available** - Never force user through something
- **This completes core build** - After this, voice integration is future phase

---

## 🎉 COMPLETION CHECK

After Session 5, the following should be fully functional:

**Phase 1:** ✅ Foundation
- Agent OS template
- Detection/classification
- Raw rant preservation
- Live tree view
- Consolidate button

**Phase 2A:** ✅ Detection & Display
- Flash Labels
- Gap Detection
- Gap Percentage

**Phase 2B:** ✅ Input Methods
- Click-to-Rant
- Real-Time Tagging

**Phase 3:** ✅ Visual Feedback
- Tag Overlay Toggle
- Multi-Panel Live Fill
- Click-to-Expand

**Phase 4:** ✅ Flexibility & Testing
- Cockpit Dashboard
- Lab Mode
- Config Levers

**Phase 5:** ✅ Learning & Memory
- Idea Bank
- Pause/Resume

**Future (Phase 6):** Voice Integration
- Voice Output / Read Back
- Better STT
- Voice Commands

---

**End of Session 5 Spec**

---

## 📝 FUTURE: Phase 6 (Voice Integration)

*Not for this session - document for future reference*

**Mechanism 17: Voice Output / Read Back**
- System talks TO user
- "Read me the current spec"
- Listen while doing other tasks

**Mechanism 10: Better Speech-to-Text**
- Custom STT for better accuracy
- Domain-specific vocabulary
- Faster transcription

**Voice Commands:**
- "Tag this as requirements"
- "Show me the gaps"
- "Read the user stories"

*These are marked FUTURE in the blueprint - implement when core system is stable.*

---

**End of All Session Specs**
