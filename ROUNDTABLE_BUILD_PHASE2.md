# Roundtable Coder - Phase 2 Build (F-K)

**SCOPE: Phases F through K**
**Prerequisite: Phases A-E are COMPLETE**

---

## WHAT'S ALREADY BUILT (Phases A-E)

### Phase A: Database Models ✅
- `RoundtableSession` - Sessions with voting threshold, execution mode
- `RoundtableRound` - Rounds with task prompts
- `RoundtableAgent` - Agents with model/provider/role
- `RoundtableResponse` - Responses with votes and metrics
- Location: `app/core/models.py` (lines 468-604)

### Phase B: Service Layer ✅
- Session/Round/Agent CRUD operations
- 7 AI models configured (Opus, Sonnet, GPT-4s, GPT-5.2)
- Location: `app/services/roundtable_service.py`

### Phase C: Execution Engine ✅
- `call_agent()` - API calls to Anthropic/OpenAI
- `execute_round()` - Single/Multi mode execution
- `calculate_consensus()` - Voting consensus
- Location: `app/services/roundtable_service.py` (lines 567-961)

### Phase D: Basic UI ✅
- Session selector, create/delete
- Execution mode toggle (Single/Multi)
- Voting threshold slider
- Round and agent management
- Location: `app/ui/roundtable_panel.py`

### Phase E: Execution UI ✅
- Run button and results display
- Voter responses with vote indicators
- Consensus display
- Location: `app/ui/roundtable_panel.py`

---

## YOUR TASK: Build Phases F-K

### Phase F: Baton Integration (45 min)

**Goal:** Connect Roundtable to the existing Baton system for context persistence.

**Files to modify:**
- `app/services/roundtable_service.py`
- `app/ui/roundtable_panel.py`

**What to add:**

1. **Import from existing baton service:**
```python
from app.services.baton_service import generate_baton, get_latest_baton
```

2. **Add method to RoundtableService:**
```python
def generate_roundtable_baton(self, session_id: int) -> str:
    """Generate a baton snapshot for a roundtable session."""
    session = self.get_session(session_id)
    rounds = self.list_rounds(session_id)

    # Build context from all rounds and responses
    context = f"# Roundtable Session: {session.name}\n\n"
    context += f"Execution Mode: {session.execution_mode}\n"
    context += f"Voting Threshold: {session.voting_threshold * 100}%\n\n"

    for round_obj in rounds:
        context += f"## Round {round_obj.round_number}: {round_obj.name}\n"
        context += f"Task: {round_obj.task_prompt}\n"
        context += f"Status: {round_obj.status}\n\n"

        # Add responses
        responses = self.get_round_responses(round_obj.id)
        if responses["builder"] and responses["builder"]["response"]:
            context += f"### Builder Response\n{responses['builder']['response'].content[:2000]}...\n\n"

    return context
```

3. **Add UI button:**
```python
if st.button("Generate Baton"):
    baton_content = service.generate_roundtable_baton(session.id)
    st.text_area("Baton Content", baton_content, height=300)
```

**Test criteria:**
- [ ] Can generate baton from roundtable session
- [ ] Baton includes all rounds and key responses
- [ ] Can copy baton content for handoff

---

### Phase G: Master Prompt System (30 min)

**Goal:** Add preset prompts and guardrails templates.

**What to add:**

1. **Add prompt presets to roundtable_service.py:**
```python
PROMPT_PRESETS = {
    "coding": {
        "system": "You are an expert software developer...",
        "guardrails": "Always include error handling. Follow PEP8..."
    },
    "review": {
        "system": "You are a senior code reviewer...",
        "guardrails": "Check for security issues, performance..."
    },
    "refactor": {
        "system": "You are refactoring specialist...",
        "guardrails": "Maintain backward compatibility..."
    }
}
```

2. **Add preset selector to UI:**
```python
preset = st.selectbox("Prompt Preset", ["Custom", "Coding", "Review", "Refactor"])
if preset != "Custom":
    # Auto-fill prompts from preset
```

**Test criteria:**
- [ ] Can select from preset prompts
- [ ] Presets auto-fill system prompt and guardrails
- [ ] Custom mode still works

---

### Phase H: GitHub Integration (1 hour)

**Goal:** Allow importing code from GitHub and creating PRs.

**What to add:**

1. **New file: `app/services/github_service.py`**
```python
import requests

class GitHubService:
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"token {token}"}

    def get_file_content(self, repo: str, path: str, branch: str = "main") -> str:
        """Fetch file content from GitHub."""
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers, params={"ref": branch})
        if response.status_code == 200:
            import base64
            return base64.b64decode(response.json()["content"]).decode()
        return ""

    def create_pr(self, repo: str, title: str, body: str, head: str, base: str = "main"):
        """Create a pull request."""
        url = f"https://api.github.com/repos/{repo}/pulls"
        data = {"title": title, "body": body, "head": head, "base": base}
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
```

2. **Add GitHub settings to UI:**
- GitHub token input in Settings
- Repo selector in Roundtable panel
- "Import from GitHub" button
- "Create PR" button after round completion

**Test criteria:**
- [ ] Can fetch file from GitHub
- [ ] Can create PR with round output
- [ ] Token stored securely in settings

---

### Phase I: Audit & Polish (30 min)

**Goal:** Add session history and usage tracking.

**What to add:**

1. **Session history panel:**
```python
def render_session_history(service, session_id):
    stats = service.get_session_stats(session_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rounds", stats["total_rounds"])
    col2.metric("Total Cost", f"${stats['total_cost']:.2f}")
    col3.metric("Total Tokens", f"{stats['total_tokens_in'] + stats['total_tokens_out']:,}")
```

2. **Export session to JSON:**
```python
def export_session(self, session_id: int) -> dict:
    """Export entire session as JSON for backup/transfer."""
    session = self.get_session(session_id)
    rounds = self.list_rounds(session_id)

    return {
        "session": {...},
        "rounds": [...],
        "total_cost": ...,
    }
```

**Test criteria:**
- [ ] Stats display correctly
- [ ] Can export session to JSON
- [ ] History shows all rounds with status

---

### Phase J: Testing System (1 hour)

**Goal:** Add built-in testing that runs after each round.

**What to add:**

1. **Test configuration in session:**
```python
# Add to RoundtableSession model (or as JSON field):
test_config = {
    "tier1": True,   # Syntax, imports, linting
    "tier2": True,   # App start, dependencies
    "tier3": False,  # Playwright UI tests
    "tier4": False,  # CI/CD integration
}
```

2. **Test runner service:**
```python
class TestRunner:
    def run_tier1(self, code: str) -> dict:
        """Run syntax and import checks."""
        results = {"passed": True, "errors": []}

        # Syntax check
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            results["passed"] = False
            results["errors"].append(f"Syntax error: {e}")

        return results

    def run_tier2(self) -> dict:
        """Run app start test."""
        # Try importing main app
        try:
            from app.streamlit_app import main
            return {"passed": True, "errors": []}
        except Exception as e:
            return {"passed": False, "errors": [str(e)]}
```

3. **Auto-run tests after round:**
- Add checkbox "Run tests after execution"
- Show test results in UI
- Block consensus if tests fail

**Test criteria:**
- [ ] Tier 1 tests run on code output
- [ ] Tier 2 tests verify app starts
- [ ] Test results shown in UI
- [ ] Can configure which tiers to run

---

### Phase K: Additional Models (30 min)

**Goal:** Add Gemini and o1 models.

**Update AVAILABLE_MODELS in roundtable_service.py:**
```python
AVAILABLE_MODELS = {
    # ... existing models ...

    # OpenAI o1 Reasoning
    "o1": {
        "id": "o1",
        "provider": "openai",
        "max_tokens": 200000,
    },
    "o1-mini": {
        "id": "o1-mini",
        "provider": "openai",
        "max_tokens": 128000,
    },

    # Google Gemini
    "Gemini 2.0 Flash": {
        "id": "gemini-2.0-flash-exp",
        "provider": "google",
        "max_tokens": 1000000,
    },
    "Gemini 1.5 Pro": {
        "id": "gemini-1.5-pro",
        "provider": "google",
        "max_tokens": 2000000,
    },
}
```

**Add Google client to service:**
```python
if google_key:
    import google.generativeai as genai
    genai.configure(api_key=google_key)
    self.google_client = genai
```

**Update call_agent() to handle Google:**
```python
elif agent.provider == "google":
    model = self.google_client.GenerativeModel(agent.model)
    response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
    content = response.text
    # Token counting for Gemini...
```

**Test criteria:**
- [ ] Gemini models appear in dropdown
- [ ] Can call Gemini API
- [ ] o1 models work correctly

---

## TESTING PROTOCOL

After each phase:
1. **Syntax check:** `python -m py_compile <file>`
2. **Import check:** `python -c "from app.services.roundtable_service import RoundtableService"`
3. **App start:** `streamlit run app/streamlit_app.py` (verify no errors)
4. **Functionality:** Test the specific feature added

---

## FILES REFERENCE

| File | Purpose |
|------|---------|
| `app/core/models.py` | Database models (lines 468-604 are Roundtable) |
| `app/services/roundtable_service.py` | Main service (961 lines) |
| `app/ui/roundtable_panel.py` | UI panel (471 lines) |
| `app/streamlit_app.py` | Main app (tab7 is Roundtable) |
| `ROUNDTABLE_SPEC.md` | Full specification |
| `AGENT_OS_ROUNDTABLE_BLUEPRINT.md` | Blueprint format |

---

## KICKOFF

Start with Phase F (Baton Integration) - it's the foundation for context persistence.

Read `app/services/baton_service.py` first to understand how the existing Baton system works, then integrate it with Roundtable.
