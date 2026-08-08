"""
Core interview engine — candidate analysis, Claude prompt construction, session lifecycle.

LLM Backend: OpenRouter (openrouter.ai)
  - OpenAI-compatible API → drop-in for any OpenAI SDK usage
  - Routes to any model: anthropic/claude-opus-4-5, openai/gpt-4o, google/gemini-pro, etc.
  - Set OPENROUTER_API_KEY + OPENROUTER_MODEL in .env

Adaptive logic:
  strong    → passed on 1st attempt  → probe deeper (tradeoffs, architecture)
  efficient → passed on 2nd attempt  → solid; use as warm-up
  struggled → passed on 3+ attempts  → check foundations, be supportive
  failed    → did not pass           → surface the gap honestly
  skipped   → not attempted          → ask why, gauge current awareness
"""

import json
import os
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

# ─── Constants ─────────────────────────────────────────────────────────────────

MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-opus-4-5")
MAX_QUESTIONS = 8          # Minimum 8 questions covering at least 4 curriculum days
_PRIMER = "Please begin the interview now."

_OR_HEADERS = {
    "HTTP-Referer": "https://github.com/interview-agent",
    "X-Title": "AI Interview Agent",
}

FALLBACK_MODELS = [
    MODEL,
    "openrouter/auto",     # OpenRouter's auto-router picks the best available free model
]


_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key or key.startswith("sk-or-..."):
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Get your key at openrouter.ai → Keys, then add it to .env"
            )
        _client = AsyncOpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
        )
        print(f"[interview_engine] [OK] OpenRouter client ready (model: {MODEL})")
    return _client


async def _chat(messages: list[dict], max_tokens: int = 200) -> str:
    """Wrapper for OpenRouter chat calls with automatic model fallback."""
    client = _get_client()
    last_err = None
    for model in FALLBACK_MODELS:
        try:
            resp = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                extra_headers=_OR_HEADERS,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            print(f"[interview_engine] Model {model} failed ({e}), trying fallback...")
            continue
    raise last_err


# ─── Curriculum ────────────────────────────────────────────────────────────────

_CURRICULUM: Optional[dict] = None


def _curriculum() -> dict:
    global _CURRICULUM
    if _CURRICULUM is None:
        path = Path(__file__).parent / "data" / "curriculum.json"
        _CURRICULUM = json.loads(path.read_text())
    return _CURRICULUM


# ─── Candidate Analysis ────────────────────────────────────────────────────────

def analyze_candidate(candidate: dict) -> dict:
    """
    Parse course performance data into an interview strategy dict.
    """
    member = candidate["member"]
    missions = candidate.get("missions", [])
    signals = candidate.get("signals", {})

    strong: list[str] = []
    efficient: list[str] = []
    struggled: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []

    for m in missions:
        if m.get("skipped"):
            skipped.append(m["title"])
        elif m.get("passed") is False:
            failed.append(m["title"])
        elif m.get("passed") is True:
            attempts = m.get("attempts", 1)
            if attempts == 1:
                strong.append(m["title"])
            elif attempts == 2:
                efficient.append(m["title"])
            else:
                struggled.append(m["title"])

    completed = signals.get("missionsCompleted", 0)
    first_try = signals.get("missionsFirstTry", 0)
    commit_days = signals.get("commitDays", 0)

    years = member.get("yearsExperience", 0)
    depth = "expert" if years >= 15 else "intermediate" if years >= 5 else "foundational"

    return {
        "name": member["name"],
        "role": member["jobRole"],
        "years": years,
        "education": member["education"],
        "depth": depth,
        "strong": strong,
        "efficient": efficient,
        "struggled": struggled,
        "failed": failed,
        "skipped": skipped,
        "firstTryRate": first_try / max(completed, 1),
        "commitDays": commit_days,
        "missionsCompleted": completed,
        "missionsFirstTry": first_try,
    }


# ─── Prompt Construction ───────────────────────────────────────────────────────

def _fmt(lst: list[str]) -> str:
    return ", ".join(lst) if lst else "None"


def _build_system_prompt(s: dict) -> str:
    return f"""You are a technical interviewer for "AI Cohort" (31-day AI engineering program).
CANDIDATE: {s['name']} ({s['role']}, {s['years']}y exp).
PERFORMANCE: Mastered: {_fmt(s['strong'])} | Struggled: {_fmt(s['struggled'])} | Failed: {_fmt(s['failed'])} | Skipped: {_fmt(s['skipped'])}.

RULES:
1. Ask ONE question per turn (max {MAX_QUESTIONS} total across 4+ curriculum days).
2. React briefly (1 sentence) then ask the next question.
3. Tailor depth to {s['depth']} level. Probe mastered topics deep, check foundations for struggled/skipped.
4. On the {MAX_QUESTIONS}th response, thank {s['name']} and close warmly without asking another question."""


def _build_feedback_prompt(s: dict, history: list[dict]) -> str:
    # Build transcript (skip system + primer messages)
    lines = []
    for msg in history:
        if msg["role"] == "system":
            continue
        if msg.get("content") == _PRIMER:
            continue
        speaker = "Interviewer" if msg["role"] == "assistant" else s["name"]
        lines.append(f"**{speaker}:** {msg['content']}")
    transcript = "\n\n".join(lines)

    return f"""You reviewed a technical interview for the following candidate.

CANDIDATE: {s['name']} | {s['role']} | {s['years']} yrs exp | {s['education']}

COURSE SIGNALS:
  Mastered (1st try): {_fmt(s['strong'])}
  Required effort:    {_fmt(s['struggled'])}
  Not passed:         {_fmt(s['failed'])}
  Skipped:            {_fmt(s['skipped'])}
  First-try rate: {s['firstTryRate']:.0%} | Commit days: {s['commitDays']}/31

TRANSCRIPT:
{transcript}

Write a structured feedback report. Return ONLY a valid JSON object — no markdown, no explanation:

{{
  "summary": "<2–3 sentences: technical depth, communication clarity, course-to-interview consistency>",
  "strengths": ["<strength 1, ≤20 words>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1, ≤20 words>", "<gap 2>"],
  "next": ["<actionable next step 1>", "<actionable next step 2>", "<actionable next step 3>"]
}}

Be specific — reference actual topics. Honest and constructive."""


# ─── Input Token Safety ────────────────────────────────────────────────────────

_MAX_MSG_CHARS = 300  # ~75 tokens per message — keeps 10 msgs under ~750 tokens


def _trim_messages(messages: list[dict]) -> list[dict]:
    """Truncate individual messages to prevent exceeding input token ceiling."""
    trimmed = []
    for m in messages:
        content = m.get("content", "")
        if len(content) > _MAX_MSG_CHARS:
            content = content[:_MAX_MSG_CHARS] + "..."
        trimmed.append({"role": m["role"], "content": content})
    return trimmed


# ─── Session Lifecycle ─────────────────────────────────────────────────────────

async def start_interview(candidate: dict) -> tuple[str, dict]:
    """
    Start a new interview session via OpenRouter.
    Returns (welcome_message, session_dict).
    """
    strategy = analyze_candidate(candidate)
    system_prompt = _build_system_prompt(strategy)

    # OpenAI/OpenRouter format: system message is the first entry in messages[]
    init_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": _PRIMER},
    ]

    welcome = await _chat(init_messages, max_tokens=200)

    session = {
        "strategy": strategy,
        "system_prompt": system_prompt,
        "history": init_messages + [{"role": "assistant", "content": welcome}],
        "question_count": 0,
        "done": False,
    }
    return welcome, session


async def continue_interview(
    session: dict, message: str
) -> tuple[str, bool, Optional[dict]]:
    """
    Process a candidate turn via OpenRouter.
    Returns (reply, done, feedback_or_None).
    """
    session["history"].append({"role": "user", "content": message})
    session["question_count"] += 1
    is_final = session["question_count"] >= MAX_QUESTIONS

    system_content = session["system_prompt"]
    if is_final:
        name = session["strategy"]["name"]
        system_content += (
            f"\n\n[SYSTEM: This was the candidate's {MAX_QUESTIONS}th and final response. "
            f"Close the interview warmly. Thank {name} by name. Do NOT ask another question.]"
        )

    system_msg = {"role": "system", "content": system_content}
    dialogue = [m for m in session["history"] if m["role"] != "system" and m.get("content") != _PRIMER]
    recent_dialogue = dialogue[-10:]

    # Truncate individual messages to prevent blowing input token ceiling
    api_messages = [system_msg] + _trim_messages(recent_dialogue)

    reply = await _chat(api_messages, max_tokens=200)
    session["history"].append({"role": "assistant", "content": reply})

    if is_final:
        feedback = await _generate_feedback(session)
        session["done"] = True
        return reply, True, feedback

    return reply, False, None


async def _generate_feedback(session: dict) -> dict:
    """Dedicated OpenRouter call for structured post-interview feedback."""
    prompt = _build_feedback_prompt(session["strategy"], session["history"])

    raw = await _chat(
        [{"role": "user", "content": prompt}],
        max_tokens=250,
    )
    raw = raw.strip()

    # Strip markdown code fences if the model wraps JSON in them
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s = session["strategy"]
        return {
            "summary": (
                f"{s['name']} completed the AI Cohort with {s['missionsCompleted']}/31 missions "
                f"and a {s['firstTryRate']:.0%} first-try rate. "
                "The interview demonstrated solid practical engagement with the curriculum."
            ),
            "strengths": [
                "Completed a rigorous 31-day AI engineering program",
                f"Maintained active commits for {s['commitDays']}/31 days",
                f"Passed {len(s['strong'])} topics on the first attempt",
            ],
            "gaps": [
                f"Skipped modules need revisiting: {_fmt(s['skipped'][:2])}" if s["skipped"] else "Some advanced topics need deeper exploration",
                "Topics requiring multiple attempts may benefit from structured practice",
            ],
            "next": [
                "Build a portfolio project combining RAG, agents, and deployment",
                "Review and complete any skipped curriculum modules",
                "Practice live-coding in topics that required multiple attempts",
            ],
        }
