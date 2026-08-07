# AI Interview Agent

LLM-driven adaptive interviewer for AI Cohort graduates. Hits the `/api/interview` contract from the technical spec, personalizing every session using each candidate's course performance data.

---

## How It Works

```
POST /api/interview  {sessionId, candidate}   → welcome + Q1
POST /api/interview  {sessionId, message}     → next question
…
POST /api/interview  {sessionId, message}     → {done:true, feedback:{…}}
```

**Adaptive logic** (in `interview_engine.py`):

| Signal | Behavior |
|--------|----------|
| Passed on 1st attempt | Probe deeper — tradeoffs, edge cases, architecture |
| Passed on 3+ attempts | Check foundations — ask what finally clicked |
| Did not pass | Surface the gap constructively |
| Skipped | Probe gently — "what's your current understanding?" |
| Job role / years | Calibrate depth: foundational / intermediate / expert |

---

## Quick Start

```bash
# 1. Clone & enter
cd interview-agent

# 2. Install deps
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# → add ANTHROPIC_API_KEY to .env

# 4. Run
uvicorn main:app --reload

# 5. Open
# Demo UI:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## API Reference

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

**Response** (ongoing):
```json
{ "reply": "...", "done": false }
```

**Response** (final):
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

### `GET /api/candidates`
Returns summary list of all 20 candidates.

### `GET /api/candidates/{id}`
Returns full candidate object (pass as `candidate` in first interview call).

### `GET /health`
Health check — returns `{ "status": "ok", "active_sessions": N }`.

---

## Deploy to Render

1. Push repo to GitHub
2. New Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env var: `ANTHROPIC_API_KEY` = your key
6. Deploy → get your live URL

Or use the included `render.yaml` for Blueprint deploy.

---

## Project Structure

```
interview-agent/
├── main.py               # FastAPI app + all routes
├── models.py             # Pydantic request/response schemas
├── session_store.py      # In-memory sessions (Breeth-ready)
├── interview_engine.py   # Claude adaptive logic + prompts
├── data/
│   ├── curriculum.json   # 31-day curriculum question bank
│   └── candidates.json   # 20 candidates with mission data
├── static/
│   └── index.html        # Demo UI (no build step)
├── requirements.txt
├── .env.example
├── render.yaml
└── AI_USAGE_LOG.md       # Hackathon required artifact
```

---

## Breeth Integration (optional)

The `session_store.py` uses in-memory storage by default. To persist sessions across restarts via Breeth:

1. Set `BREETH_API_KEY` in `.env`
2. Replace the `_sessions` dict in `session_store.py` with Breeth `save`/`search` calls
3. See `session_store.py` for the exact comment/hook

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | Your Claude API key |
| `ANTHROPIC_MODEL` | ❌ | `claude-opus-4-5` | Override the model |
| `BREETH_API_KEY` | ❌ | — | Enable Breeth session persistence |
