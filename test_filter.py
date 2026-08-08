
from interview_engine import _build_feedback_prompt

def test_hard_filter_ui_errors():
    s = {"name": "Test User", "role": "Dev", "years": 5, "education": "BS", "strong": [], "struggled": [], "failed": [], "skipped": [], "firstTryRate": 1.0, "commitDays": 31}
    
    # Simulate a history with genuine technical discussion AND injected UI errors
    history = [
        {"role": "assistant", "content": "Tell me about scaling."},
        {"role": "user", "content": "I use backpressure and handle 502 rate limit errors carefully."},
        {"role": "user", "content": "Network error. Check the server connection."},
        {"role": "user", "content": "I use backpressure. LLM service error: Google API Error 429: quota exceeded. Also I use RAGAS for evaluation."},
        {"role": "assistant", "content": "Great answer."},
    ]
    
    prompt = _build_feedback_prompt(s, history)
    
    assert "handle 502 rate limit errors carefully" in prompt, "Valid technical answer 1 was dropped!"
    assert "I use backpressure." in prompt, "Valid technical answer 2 (prefix) was dropped!"
    assert "Also I use RAGAS for evaluation." in prompt, "Valid technical answer 3 (suffix) was dropped!"
    assert "Network error. Check the server connection." not in prompt, "UI error 1 leaked!"
    assert "LLM service error: Google API Error 429" not in prompt, "UI error 2 leaked!"

test_hard_filter_ui_errors()
print("Tests passed")
