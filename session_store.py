"""
Session store — Breeth-first (free hackathon access), in-memory fallback.

Priority:
  1. Breeth  (if BREETH_API_KEY is set)  → persistent, intent-aware memory
  2. In-memory dict                       → local dev / demo

Breeth API used:
  Write: POST https://api.thebreeth.com/v1/episodes
  Read:  POST https://api.thebreeth.com/v1/search

Get your key: thebreeth.com/app → API Keys
"""

import json
import os
from typing import Optional

import httpx

# ── Config ──────────────────────────────────────────────────────────────────
BREETH_BASE    = "https://api.thebreeth.com/v1"
BREETH_KEY     = os.environ.get("BREETH_API_KEY", "").strip()
BREETH_PROJECT = os.environ.get("BREETH_PROJECT_ID", "interview-agent").strip()

_breeth_ok: Optional[bool] = None   # None = not yet tested


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {BREETH_KEY}",
        "Content-Type": "application/json",
    }


def _is_breeth_configured() -> bool:
    global _breeth_ok
    if _breeth_ok is not None:
        return _breeth_ok
    configured = bool(BREETH_KEY) and len(BREETH_KEY) > 10
    if configured:
        print(f"[session_store] [OK] Breeth connected (project: {BREETH_PROJECT})")
    else:
        print("[session_store] [INFO] BREETH_API_KEY not set — using in-memory store.")
    _breeth_ok = configured
    return _breeth_ok


# ── In-memory fallback ──────────────────────────────────────────────────────
_sessions: dict[str, dict] = {}

# ── Breeth helpers ──────────────────────────────────────────────────────────

def _write_to_breeth(session_id: str, data: dict) -> None:
    """Write / overwrite a session as a Breeth episode."""
    payload = {
        "project_id":      BREETH_PROJECT,
        "content":         json.dumps(data),
        "extract_intent":  True,            # let Breeth extract interview patterns
        "metadata": {
            "session_id": session_id,
            "type":       "interview_session",
            "candidate":  data.get("strategy", {}).get("name", "unknown"),
        },
    }
    with httpx.Client(timeout=8) as client:
        resp = client.post(f"{BREETH_BASE}/episodes", headers=_headers(), json=payload)
        resp.raise_for_status()


def _read_from_breeth(session_id: str) -> Optional[dict]:
    """Search Breeth for an exact session_id match and return parsed JSON."""
    payload = {
        "query":      f"session_id:{session_id}",
        "project_id": BREETH_PROJECT,
        "limit":      1,
    }
    with httpx.Client(timeout=8) as client:
        resp = client.post(f"{BREETH_BASE}/search", headers=_headers(), json=payload)
        resp.raise_for_status()

    results = resp.json().get("results") or resp.json().get("data") or []
    for r in results:
        content = r.get("content") or r.get("text") or ""
        try:
            data = json.loads(content)
            if isinstance(data, dict) and data.get("strategy"):
                return data
        except json.JSONDecodeError:
            continue
    return None


# ── Public interface ────────────────────────────────────────────────────────

def get_session(session_id: str) -> Optional[dict]:
    if _is_breeth_configured():
        try:
            result = _read_from_breeth(session_id)
            if result:
                return result
        except Exception as e:
            print(f"[session_store] Breeth read error: {e} — falling back to memory")
    return _sessions.get(session_id)


def set_session(session_id: str, data: dict) -> None:
    # Always write to in-memory (fast reads during the session)
    _sessions[session_id] = data
    # Also persist to Breeth if available
    if _is_breeth_configured():
        try:
            _write_to_breeth(session_id, data)
        except Exception as e:
            print(f"[session_store] Breeth write error: {e} — saved in memory only")


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
    # Breeth doesn't have a delete endpoint — data ages out naturally


def active_count() -> int:
    return len(_sessions)
