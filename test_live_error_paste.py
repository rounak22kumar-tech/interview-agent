import httpx
import json
import sys
import time

BASE = "http://127.0.0.1:8000"
SESSION_ID = f"paste-test-{int(time.time())}"

with open("data/candidates.json") as f:
    candidate = json.load(f)["candidates"][0]

client = httpx.Client(base_url=BASE, timeout=120.0)

print("Starting interview...")
r = client.post("/api/interview", json={"sessionId": SESSION_ID, "candidate": candidate})
if r.status_code != 200:
    print("FAIL: Server not running or start failed.")
    sys.exit(1)

# Scenario 1: User pastes ONLY the error string
print("Pasting ONLY an error string...")
r = client.post("/api/interview", json={"sessionId": SESSION_ID, "message": "LLM service error: Google API Error 429: quota exceeded"})
data = r.json()
assert "system error occurred" in data["reply"].lower(), "Did not receive empty-message fallback!"

# Scenario 2: User pastes valid technical answer + error string
print("Pasting technical answer + error string...")
r = client.post("/api/interview", json={"sessionId": SESSION_ID, "message": "I scaled it using KEDA. LLM service error: Google API Error 502"})
data = r.json()
assert "system error occurred" not in data["reply"].lower(), "Fallback was triggered when valid text was present!"
assert data["reply"], "Reply was empty!"

print("Tests passed!")
