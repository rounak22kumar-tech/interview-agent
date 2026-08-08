"""
End-to-end test: full 8-question interview + feedback JSON verification.
Simulates the exact flow a hackathon judge's automated script would run.
"""
import httpx
import json
import sys
import time

BASE = "https://interview-agent-nmlc.onrender.com"
SESSION_ID = f"e2e-test-{int(time.time())}"

# Load first candidate
with open("data/candidates.json") as f:
    candidate = json.load(f)["candidates"][0]

print(f"=== E2E TEST: {candidate['member']['name']} ===")
print(f"Session: {SESSION_ID}\n")

# Simulated candidate answers (short, realistic)
ANSWERS = [
    "I used Python with ChromaDB for embeddings and vector search.",
    "RAG combines retrieval with generation - you fetch relevant docs then feed them to the LLM.",
    "I used cosine similarity for matching and experimented with different chunk sizes.",
    "Prompt engineering is about crafting instructions that guide LLM behavior consistently.",
    "I built a chatbot using FastAPI backend with streaming responses.",
    "For agents, I used tool-calling where the LLM decides which function to invoke.",
    "MCP standardizes how AI models interact with external tools and data sources.",
    "I deployed using Docker containers on a cloud platform with health checks.",
]

client = httpx.Client(base_url=BASE, timeout=30)

# Step 1: Start interview
print("[1/10] Starting interview...")
r = client.post("/api/interview", json={"sessionId": SESSION_ID, "candidate": candidate})
if r.status_code != 200:
    print(f"FAIL: Start returned {r.status_code}: {r.text}")
    sys.exit(1)
data = r.json()
print(f"  Status: {r.status_code}")
print(f"  done: {data['done']}")
print(f"  reply: {data['reply'][:100]}...")
assert data["done"] == False, "First response should not be done"
print("  PASS\n")

# Steps 2-9: Answer 8 questions
for i, answer in enumerate(ANSWERS, start=1):
    print(f"[{i+1}/10] Sending answer {i}/8: '{answer[:50]}...'")
    r = client.post("/api/interview", json={"sessionId": SESSION_ID, "message": answer})
    if r.status_code != 200:
        print(f"  FAIL: Turn {i} returned {r.status_code}: {r.text}")
        sys.exit(1)
    data = r.json()
    print(f"  Status: {r.status_code}")
    print(f"  done: {data['done']}")
    try:
        print(f"  reply: {data['reply'][:100]}...")
    except UnicodeEncodeError:
        print(f"  reply: {data['reply'][:100].encode('ascii', 'ignore').decode('ascii')}...")

    if i < 8:
        assert data["done"] == False, f"Turn {i} should not be done yet"
        assert data.get("feedback") is None, f"Turn {i} should not have feedback"
        print("  PASS\n")
    else:
        # Final turn — must have done=true and feedback
        assert data["done"] == True, "Final turn must have done=true"
        assert data.get("feedback") is not None, "Final turn must include feedback"
        fb = data["feedback"]
        print(f"\n=== FEEDBACK JSON ===")
        print(json.dumps(fb, indent=2))
        assert "summary" in fb, "Feedback missing 'summary'"
        assert "strengths" in fb, "Feedback missing 'strengths'"
        assert "gaps" in fb, "Feedback missing 'gaps'"
        assert "next" in fb, "Feedback missing 'next'"
        assert isinstance(fb["strengths"], list), "'strengths' must be a list"
        assert isinstance(fb["gaps"], list), "'gaps' must be a list"
        assert isinstance(fb["next"], list), "'next' must be a list"
        print("\n  ALL FEEDBACK FIELDS VALID")
        print("  PASS\n")

# Step 10: Verify completed session rejects new messages
print("[10/10] Verifying completed session rejects new messages...")
r = client.post("/api/interview", json={"sessionId": SESSION_ID, "message": "hello?"})
print(f"  Status: {r.status_code}")
assert r.status_code == 400, "Completed session should return 400"
print("  PASS\n")

print("=" * 60)
print("ALL 10 CHECKS PASSED — FULL E2E TEST SUCCESSFUL")
print("=" * 60)
