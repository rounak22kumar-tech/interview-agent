# AI Interview Agent

LLM-driven adaptive interviewer for AI Cohort graduates. Hits the `/api/interview` contract from the technical spec, personalizing every session using each candidate's course performance data. 

**Live Demo**: [https://interview-agent-nmlc.onrender.com/](https://interview-agent-nmlc.onrender.com/)

---

## 🌟 Hackathon Features

1. **Adaptive Logic:** Questions scale in difficulty based on the candidate's actual course performance (Mastered, Struggled, Failed, Skipped).
2. **LLM Gateway (OpenRouter):** Built to be model-agnostic. Currently routes to `anthropic/claude-opus-4-5` with automatic fallback to `openrouter/free` if the primary model goes down.
3. **Session Memory (Breeth):** Integrates with the Breeth API for persistent, intent-aware session tracking (with in-memory fallback).
4. **Token Budgeting:** Uses sliding window context (last 10 turns) and per-message truncation to stay safely within free-tier OpenRouter token limits.
5. **Bulletproof Feedback JSON:** If the LLM times out or fails on the final 8th turn, the backend gracefully catches it and generates a dynamic fallback JSON so the UI never crashes.
6. **Defense-in-Depth Error Filtering:** Protects live LLM conversation flows and final feedback generation by dynamically stripping pasted UI system errors (e.g. 502/429 network timeouts) via a precise regex matching system, ensuring candidates are only evaluated on actual technical answers.
7. **Security Hardened:** 
   - Strict IP Rate Limiting (20 req/min)
   - Locked down CORS (allows local & Render domains only)
   - Anti-prompt injection rules built directly into the system prompt

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone & enter
cd interview-agent

# 2. Install deps
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# → add OPENROUTER_API_KEY to .env

# 4. Run
uvicorn main:app --reload

# 5. Open
# Demo UI:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## 📡 API Reference

### `POST /api/interview`

**First call** (start session):
```json
{
  "sessionId": "abc-123",
  "candidate": { ...full candidate object from candidates.json... }
}
```

**Subsequent calls**:
```json
{
  "sessionId": "abc-123",
  "message": "I used ChromaDB with sentence-transformers..."
}
```

**Response** (final 8th turn):
```json
{
  "reply": "Thank you, this concludes our interview.",
  "done": true,
  "feedback": {
    "summary": "...",
    "strengths": ["...", "..."],
    "gaps": ["...", "..."],
    "next": ["...", "..."]
  }
}
```

---

## 🏗️ Project Structure

```text
interview-agent/
├── main.py               # FastAPI app, Routes, Rate Limiting, CORS
├── models.py             # Pydantic schemas
├── session_store.py      # Breeth API persistence + in-memory fallback
├── interview_engine.py   # Adaptive logic, System prompts, Token truncation, Error filtering
├── test_e2e.py           # Automated 8-question judge simulation
├── test_skip.py          # E2E multi-turn skip logic and feedback test
├── test_filter.py        # Regex UI-error bounds unit test
├── test_live_error_paste.py # Simulates mid-interview copy-paste system error
├── data/
│   ├── curriculum.json   # 31-day curriculum question bank
│   └── candidates.json   # 20 candidates with mission data
├── static/
│   ├── index.html        # Premium dark-mode UI
│   └── errors.json       # Shared dynamic error configs (DRY pattern)
├── requirements.txt      
├── render.yaml           # Automated Render deployment config
├── Dockerfile & Procfile # Universal deployment fallbacks
├── PROJECT_CONTEXT.md    # Full context dump for AI handoffs
└── AI_USAGE_LOG.md       # Hackathon required AI session log
```

---

## 🔐 Environment Variables

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `GEMINI_API_KEY` | ✅ | — | Your Google AI Studio API key |
| `BREETH_API_KEY` | ❌ | — | Enable Breeth session persistence |
| `BREETH_PROJECT_ID` | ❌ | `interview-agent` | Scope for Breeth episodes |
