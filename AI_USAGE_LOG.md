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
**Outcome:** Decided on FastAPI + OpenRouter (LLM gateway) + in-memory session store (Breeth-ready interface).

### Session 2 — Spec Review
**Tool:** Claude (claude.ai)
**Prompt intent:** Analyzed technical-spec.md to understand the POST /api/interview contract, sessionId state management, and the done/feedback response shape.
**Outcome:** Mapped spec requirements to FastAPI route handlers and Pydantic models.

### Session 3 — Candidate Analyzer Design
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed adaptive interview logic — how to classify missions as strong/struggled/failed/skipped and use those signals to calibrate the interviewer LLM's question depth.
**Outcome:** `analyze_candidate()` function in `interview_engine.py`.

### Session 4 — System Prompt Engineering
**Tool:** Antigravity (Gemini)
**Prompt intent:** Crafted the system prompt with explicit per-category behavior rules (strong → go deep, struggled → check foundations, skipped → probe gently, failed → surface gap).
**Outcome:** `_build_system_prompt()` in `interview_engine.py`.

### Session 5 — Feedback Prompt Engineering
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed the post-interview feedback prompt to produce structured JSON (summary, strengths, gaps, next) combining interview answers with course performance signals.
**Outcome:** `_build_feedback_prompt()` and `_generate_feedback()` in `interview_engine.py`.

### Session 6 — Full Project Scaffold
**Tool:** Antigravity (Gemini)
**Prompt intent:** Generated the complete project: `main.py`, `models.py`, `session_store.py`, `interview_engine.py`, `static/index.html`, `requirements.txt`, `render.yaml`.
**Outcome:** Fully working codebase ready for local testing and cloud deployment.

### Session 7 — UI Design
**Tool:** Antigravity (Gemini)
**Prompt intent:** Designed a premium dark-theme chat UI with candidate selector, interview chat interface, typing indicators, progress tracker, and animated feedback overlay.
**Outcome:** `static/index.html` — single-file, no build step required.

### Session 8 — Bug Fixes & Hardening
**Tool:** Antigravity (Gemini)
**Prompt intent:** Resolved multiple runtime issues — Windows CP1252 Unicode crash (emoji in print statements), OpenRouter free-tier token limit errors (402), NameError on module-level constant ordering.
**Outcome:** Compact system prompt (~200 tokens), sliding window context (last 10 turns), lazy singleton client pattern.

### Session 9 — Model Fallback & Input Safety
**Tool:** Antigravity (Gemini)
**Prompt intent:** Fixed hardcoded free model slugs that returned 404 (models rotated off OpenRouter). Added per-message input truncation to prevent exceeding free-tier input token ceiling mid-interview.
**Outcome:** `openrouter/auto` fallback (auto-routes to available free models), `_trim_messages()` caps each message at 300 chars, graceful 502 JSON errors instead of bare 500s.

### Session 10 — End-to-End Verification
**Tool:** Antigravity (Gemini)
**Prompt intent:** Created and ran automated e2e test simulating a full 8-question interview (start → 8 answers → feedback JSON → session rejection).
**Outcome:** `test_e2e.py` — all 10 checks passed, feedback JSON validated with correct schema.

---

## Model Used at Runtime
- **LLM Gateway:** OpenRouter (`openrouter.ai`) — routes to any model via OpenAI-compatible API
- **Primary model:** `anthropic/claude-opus-4-5` (configurable via `OPENROUTER_MODEL` env var)
- **Fallback:** `openrouter/auto` — auto-selects best available model
- **Feedback generator:** Same model, separate API call after interview completion

## Session Persistence
- **Primary:** Breeth API (`thebreeth.com`) — intent-aware memory episodes
- **Fallback:** In-memory Python dict (for local dev and when Breeth is unavailable)

## Key Design Decisions Aided by AI
1. **Adaptive question strategy** — AI helped define the five candidate signal categories and corresponding prompt behaviors.
2. **Stateless API design** — AI helped reason through sessionId-keyed state management without a persistent DB.
3. **Feedback JSON reliability** — AI suggested stripping markdown fences from LLM output + a graceful fallback for JSON parse failures.
4. **MAX_QUESTIONS = 8** — Set to meet hackathon minimum requirement of 8 questions covering 4+ curriculum days.
5. **Token budget management** — AI designed the sliding window + per-message truncation strategy to stay within free-tier limits.
6. **Model fallback chain** — AI recommended `openrouter/auto` over hardcoded free slugs that rotate frequently.

---

*Last updated: 2026-08-08*
