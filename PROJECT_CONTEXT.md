# AI Interview Agent — Full Project Context

> **Purpose of this document:** Upload this to Claude or any AI assistant to get full context on this project's architecture, current state, known issues, and next steps. Everything needed to continue development is here.

---

## 1. What This Project Is

An **AI-powered technical interview agent** built for a hackathon. It conducts personalized, multi-turn technical interviews for graduates of the "AI Cohort" — a 31-day AI engineering program.

### Hackathon Requirements (all must be met)
- [x] Conduct a conversational technical interview
- [x] Ask a **minimum of 8 questions** covering **at least 4 different curriculum days**
- [x] Generate **follow-up questions** based on previous responses
- [x] Maintain **conversation context** throughout the interview
- [x] Produce **structured feedback** at the end (`summary`, `strengths`, `gaps`, `next`)
- [x] Expose `POST /api/interview` HTTP endpoint matching the technical spec
- [x] Use provided `curriculum.json` and `candidates.json` data

### API Contract (Technical Spec)
```
POST /api/interview

# 1. Start Interview (first request)
Request:  { "sessionId": "abc-123", "candidate": { ...candidate.json } }
Response: { "reply": "Welcome...", "done": false }

# 2. Conversation Turn (subsequent requests)
Request:  { "sessionId": "abc-123", "message": "..." }
Response: { "reply": "...", "done": false }

# 3. End Interview (final response)
Response: { "reply": "Thank you...", "done": true, "feedback": { "summary": "...", "strengths": [...], "gaps": [...], "next": [...] } }
```

---

## 2. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI (Python) | Async, fast, auto-docs |
| **LLM** | Gemini API (Google AI Studio) | Free-tier capable native REST (`httpx`) API |
| **Session Store** | Breeth API + in-memory fallback | Breeth = hackathon sponsor prize ("Best Use of Breeth") |
| **Frontend** | Vanilla HTML/CSS/JS (dark mode) | Single `static/index.html`, no build step |
| **Deployment Config** | `render.yaml` (Render.com blueprint) | One-click deploy |

### Environment Variables (`.env`)
```env
GEMINI_API_KEY=AIza...                   # REQUIRED — get from Google AI Studio
BREETH_API_KEY=ck_live_...               # OPTIONAL — session persistence
BREETH_PROJECT_ID=interview-agent        # OPTIONAL — Breeth project scope
```

---

## 3. File Structure & What Each File Does

```
interview-agent/
├── main.py                 # FastAPI app — routes, CORS, static files
├── interview_engine.py     # Core logic — candidate analysis, prompt building, LLM calls
├── models.py               # Pydantic models (InterviewRequest, InterviewResponse, FeedbackModel)
├── session_store.py        # Session persistence (Breeth API → in-memory fallback)
├── requirements.txt        # Python dependencies
├── .env                    # API keys (gitignored)
├── .env.example            # Template for .env
├── .gitignore              # Excludes .env, .venv, __pycache__
├── render.yaml             # Render.com deployment blueprint
├── AI_USAGE_LOG.md         # Hackathon compliance — AI tools used log
├── README.md               # Project documentation
├── test_filter.py          # Unit test for UI error stripping/regex boundaries
├── test_skip.py            # E2E test for multi-turn flow & skip logic
├── test_live_error_paste.py# E2E test simulating UI error string pasting mid-chat
├── data/
│   ├── curriculum.json     # 31-day AI Cohort curriculum (8 modules)
│   └── candidates.json     # 20 candidate profiles with mission results
└── static/
    ├── index.html          # Demo UI (dark-mode, single-page app)
    └── errors.json         # Shared exact-match error strings for UI & Backend filter
```

---

## 4. Architecture Deep Dive

### 4.1 `main.py` — FastAPI Server (135 lines)
- Loads `.env` via `python-dotenv`
- Mounts `static/` for the demo UI
- Routes:
  - `GET /` → serves `index.html`
  - `GET /health` → health check with active session count
  - `GET /api/candidates` → summary list of all 20 candidates
  - `GET /api/candidates/{id}` → full candidate object
  - `POST /api/interview` → **main interview endpoint** (matches hackathon spec exactly)
- Interview flow logic:
  - No session found + `candidate` provided → calls `interview_engine.start_interview()`
  - Session exists + `message` provided → calls `interview_engine.continue_interview()`
  - Session already done → returns 400

### 4.2 `interview_engine.py` — Core Engine (309 lines)

**Constants:**
- `MAX_QUESTIONS = 8`

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `_chat(messages, max_tokens=200)` | Native Google AI Studio REST API call (httpx) with auto-retries |
| `analyze_candidate(candidate)` | Parses missions into strategy: strong/efficient/struggled/failed/skipped |
| `_sanitize_message(content)` | Regex strips dynamic UI error substrings without deleting candidate answers |
| `_build_system_prompt(strategy)` | Compact system prompt (~200 tokens) with interview rules |
| `_build_feedback_prompt(strategy, history)` | Transcript + JSON output schema for feedback generation |
| `start_interview(candidate)` | Creates session, sends primer, returns welcome + session dict |
| `continue_interview(session, message)` | Sliding window context, sanitizes input, handles final turn + feedback |
| `_generate_feedback(session)` | Dedicated LLM call for structured JSON feedback with fallback |

**Adaptive Logic (from `analyze_candidate`):**
```
strong    → passed on 1st attempt  → probe deeper (tradeoffs, architecture)
efficient → passed on 2nd attempt  → solid; use as warm-up
struggled → passed on 3+ attempts  → check foundations, be supportive
failed    → did not pass           → surface the gap honestly
skipped   → not attempted          → ask why, gauge current awareness
```

**Sliding Window Context (in `continue_interview`):**
- System prompt is reconstructed fresh each turn (not from history[0])
- Dialogue = all non-system, non-primer messages from history
- Only last 10 dialogue messages sent to LLM (`dialogue[-10:]`)
- This keeps payloads small and fast for the Gemini free tier

**max_tokens settings:**
- `start_interview`: 200
- `continue_interview`: 200
- `_generate_feedback`: 250

### 4.3 `session_store.py` — Persistence (125 lines)

**Priority chain:**
1. **Breeth API** (if `BREETH_API_KEY` is set and valid)
   - Write: `POST /v1/episodes` with `extract_intent: true`
   - Read: `POST /v1/search` with `query: "session_id:{id}"`
2. **In-memory dict** (always, as fast cache + fallback)

**Public interface:**
- `get_session(session_id)` → dict or None
- `set_session(session_id, data)` → writes to memory + Breeth
- `delete_session(session_id)` → removes from memory
- `active_count()` → number of active sessions

### 4.4 `models.py` — Pydantic Models (22 lines)
```python
InterviewRequest:  sessionId (str), candidate (optional dict), message (optional str)
InterviewResponse: reply (str), done (bool), feedback (optional FeedbackModel)
FeedbackModel:     summary (str), strengths (list[str]), gaps (list[str]), next (list[str])
```

### 4.5 `static/index.html` — Demo UI
- Single-page dark-mode app
- Candidate selector dropdown → profile card
- Chat interface with typing indicators
- Feedback report modal on interview completion
- `MAX_QUESTIONS = 8` (synced with backend)

---

## 5. Current State & Known Issues

### ✅ Working
- Server starts cleanly (`uvicorn main:app --reload --port 8000`)
- Candidate list loads in UI
- Interview starts (welcome message from Gemini)
- Multi-turn conversation works
- Model fallback chain works
- Strict filtering of exact UI error strings injected by the user (protects live flow & feedback)
- `.env` keys are configured and valid
- GitHub repo is live: https://github.com/rounak22kumar-tech/interview-agent
- **Deployed live to Render.com**: `https://interview-agent-nmlc.onrender.com`
- **Full E2E suite passes** (verifying limits, empty inputs, skipping, error string paste)

### ⚠️ Known Issues

| Issue | Severity | Details |
|-------|----------|---------|
| **Gemini Free-Tier Rate Limits** | MEDIUM | Can hit 429 Too Many Requests if multiple users test simultaneously. Handled by client-side retry, but can still fail. |
| **Breeth 403 Forbidden** | MEDIUM | `POST /v1/episodes` returns 403. The key (`ck_live_...`) is set but the endpoint rejects writes. Likely needs a project created in Breeth dashboard first, or the API payload format differs. **App works fine via in-memory fallback.** |
| **`requirements.txt` includes `supabase`** | LOW | We switched to Breeth but `supabase==2.7.4` is still in requirements. It installs but isn't used. Can be removed to reduce install time. |

### Git History (key commits)
```
898f5ec  Initial commit: AI Interview Agent
59e2df9  Update MAX_QUESTIONS to 8 and enforce 4+ curriculum days rule
f2a8b8a  Fix Windows CP1252 print unicode encoding error
f106386  Fix token limit error by implementing sliding window context memory
27d5498  Optimize system prompt size and add model fallback for 0-credit OpenRouter tiers
1e06939  Fix NameError MODEL definition ordering in interview_engine.py
01d049f  Lower max_tokens to 200 to comply with OpenRouter free-tier credit quota
```

---

## 6. How to Run Locally

```powershell
# 1. Navigate to project
cd C:\Users\Rounak Kumar\.gemini\antigravity\scratch\interview-agent

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Run server
uvicorn main:app --reload --port 8000

# 4. Open browser
# http://localhost:8000
```

---

## 7. Priority Next Steps

### LOW — Polish
1. **Fix Breeth integration** — create project in Breeth dashboard, verify API payload format, fix 403
2. **Graceful error handling** — return user-friendly JSON errors instead of 500 on LLM failures
3. **Add error retry with exponential backoff** in `_chat()`
4. **Rate limiting** on `/api/interview` endpoint

---

## 8. Hackathon Scoring Context

### Tools Requested by User (for integration/mention)
- **Gemini API** ✅ — LLM gateway (implemented natively via REST)
- **Breeth** ⚠️ — session memory (integrated but 403 on writes)
- **Supabase** — was in plan, replaced by Breeth
- **Railway** — deployment target (not deployed yet)
- **GummySearch, Exploding Topics, Magic Patterns, Bolt.new, Chaotech.in** — mentioned by user, documented in AI_USAGE_LOG.md as research/design tools

### Sponsor Prize: "Best Use of Breeth"
Breeth integration is in place architecturally. To qualify:
- Fix the 403 error (likely needs project setup in Breeth dashboard)
- Demonstrate that interview sessions are persisted as intent-aware episodes
- Show that Breeth's `extract_intent` flag captures interview patterns

---

## 9. Complete Source Code Reference

All source files are in: `C:\Users\Rounak Kumar\.gemini\antigravity\scratch\interview-agent\`
GitHub: https://github.com/rounak22kumar-tech/interview-agent

### Key API Keys (in `.env`, gitignored)
- Gemini: `AIza...` (free tier)
- Breeth: `ck_live_...` (hackathon access)

---

*Last updated: 2026-08-08 21:00 IST*
*Total codebase: ~600 lines of Python + ~1200 lines of HTML/CSS/JS*
