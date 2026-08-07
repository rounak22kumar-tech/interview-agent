import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import interview_engine
import session_store
from models import FeedbackModel, InterviewRequest, InterviewResponse

# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Interview Agent",
    version="1.0.0",
    description="LLM-driven adaptive interviewer for AI Cohort graduates.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "AI Interview Agent",
        "active_sessions": session_store.active_count(),
    }


@app.get("/api/candidates")
async def list_candidates():
    """Return a summary list of all available candidates."""
    with open(DATA_DIR / "candidates.json") as f:
        data = json.load(f)
    return {
        "candidates": [
            {
                "id": c["member"]["id"],
                "name": c["member"]["name"],
                "jobRole": c["member"]["jobRole"],
                "yearsExperience": c["member"]["yearsExperience"],
                "education": c["member"]["education"],
                "status": c["member"]["status"],
                "signals": c["signals"],
                "missionCount": len(c["missions"]),
            }
            for c in data["candidates"]
        ]
    }


@app.get("/api/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Return the full candidate object for use in /api/interview."""
    with open(DATA_DIR / "candidates.json") as f:
        data = json.load(f)
    for c in data["candidates"]:
        if c["member"]["id"] == candidate_id:
            return c
    raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found.")


@app.post("/api/interview", response_model=InterviewResponse)
async def interview(req: InterviewRequest):
    """
    Main interview endpoint — stateless per call, sessionId-keyed state.

    First call:  { sessionId, candidate: {...} }        → welcome message
    Subsequent:  { sessionId, message: "..." }          → next question
    Final:       { ..., done: true, feedback: {...} }   → structured feedback
    """
    session = session_store.get_session(req.sessionId)

    # ── New session ──────────────────────────────────────────────────────────
    if session is None:
        if not req.candidate:
            raise HTTPException(
                status_code=400,
                detail="The first request must include the 'candidate' object.",
            )
        reply, session = await interview_engine.start_interview(req.candidate)
        session_store.set_session(req.sessionId, session)
        return InterviewResponse(reply=reply, done=False)

    # ── Already finished ─────────────────────────────────────────────────────
    if session.get("done"):
        raise HTTPException(
            status_code=400,
            detail="This interview session has already been completed.",
        )

    # ── Ongoing session ──────────────────────────────────────────────────────
    if not req.message:
        raise HTTPException(
            status_code=400,
            detail="Ongoing sessions require a 'message' field.",
        )

    reply, done, feedback = await interview_engine.continue_interview(session, req.message)
    session_store.set_session(req.sessionId, session)

    if done:
        return InterviewResponse(
            reply=reply,
            done=True,
            feedback=FeedbackModel(**feedback),
        )
    return InterviewResponse(reply=reply, done=False)
