# AI Usage Log — AI Interview Agent
### ABTalks VicoDathon 2026 · Hackathon Submission

---

## Purpose
This log documents all AI-assisted steps taken during the development of this project, as required by the hackathon evaluation criteria.

---

## Session Log

### Session 1 — Architecture & Design
**Tool:** Claude (claude.ai)
**Prompt intent:** Deliberated tech stack choices — FastAPI vs Node, Claude vs OpenAI, Breeth integration strategy.
**Outcome:** Decided on FastAPI + Claude API + in-memory session store (Breeth-ready interface).

### Session 2 — Spec Review
**Tool:** Claude (claude.ai)
**Prompt intent:** Analyzed technical-spec.md to understand the POST /api/interview contract, sessionId state management, and the done/feedback response shape.
**Outcome:** Mapped spec requirements to FastAPI route handlers and Pydantic models.

### Session 3 — Candidate Analyzer Design
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed adaptive interview logic — how to classify missions as strong/struggled/failed/skipped and use those signals to calibrate Claude's question depth.
**Outcome:** `analyze_candidate()` function in `interview_engine.py`.

### Session 4 — System Prompt Engineering
**Tool:** Antigravity (Gemini)
**Prompt intent:** Crafted the Claude system prompt with explicit per-category behavior rules (strong → go deep, struggled → check foundations, skipped → probe gently, failed → surface gap).
**Outcome:** `_build_system_prompt()` in `interview_engine.py`.

### Session 5 — Feedback Prompt Engineering
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed the post-interview feedback prompt to produce structured JSON (summary, strengths, gaps, next) combining interview answers with course performance signals.
**Outcome:** `_build_feedback_prompt()` and `_generate_feedback()` in `interview_engine.py`.

### Session 6 — Full Project Scaffold
**Tool:** Antigravity (Gemini)
**Prompt intent:** Generated the complete project: `main.py`, `models.py`, `session_store.py`, `interview_engine.py`, `static/index.html`, `requirements.txt`, `render.yaml`.
**Outcome:** Fully working codebase ready for local testing and Render deployment.

### Session 7 — UI Design
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed a premium dark-theme chat UI with candidate selector, interview chat interface, typing indicators, progress tracker, and animated feedback overlay.
**Outcome:** `static/index.html` — single-file, no build step required.

---

## Model Used at Runtime
- **Interview conductor:** `claude-opus-4-5` (configurable via `ANTHROPIC_MODEL` env var)
- **Feedback generator:** Same model, separate API call after interview completion

## Key Design Decisions Aided by AI
1. **Adaptive question strategy** — AI helped define the five candidate signal categories and corresponding prompt behaviors.
2. **Stateless API design** — AI helped reason through sessionId-keyed state management without a persistent DB.
3. **Feedback JSON reliability** — AI suggested stripping markdown fences from Claude output + a graceful fallback for JSON parse failures.
4. **MAX_QUESTIONS = 6** — AI suggested this as the right balance for a demo-length interview (5–8 min) and hackathon Stage 4 live extension.

---

*Last updated: 2026-08-07*
