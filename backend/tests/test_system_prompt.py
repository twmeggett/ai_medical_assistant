# tests/test_system_prompt.py
import json
import anthropic
from dotenv import load_dotenv
from anthropic.types import TextBlock
from backend.prompts import ACTIVE_MED_ASSISTANT_SYSTEM

load_dotenv()

client = anthropic.Anthropic()

def ask(user_message: str) -> str:
    """Helper — makes a real API call with your system prompt."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=ACTIVE_MED_ASSISTANT_SYSTEM.content,
        messages=[{"role": "user", "content": user_message}]
    )
    first_block = response.content[0]
    return first_block.text if isinstance(first_block, TextBlock) else ''


# ── Test 1: Response includes required keys ──────────────────────────────────
def test_response_has_required_keys():
    result = ask("What are the symptoms of Type 2 diabetes?")
    parsed = json.loads(result)
    assert "answer" in parsed
    assert "sources" in parsed
    assert "confidence" in parsed


# ── Test 2: Sources is a non-empty list ──────────────────────────────────────
def test_sources_is_populated():
    result = ask("What is metformin used for?")
    parsed = json.loads(result)
    assert isinstance(parsed["sources"], list)
    assert len(parsed["sources"]) > 0


# ── Test 3: Refuses off-topic questions ──────────────────────────────────────
def test_refuses_non_medical_query():
    result = ask("What is the capital of France?")
    # Don't assert exact wording — assert intent
    assert any(word in result.lower() for word in ["medical", "outside", "only", "cannot"])


# ── Test 4: Confidence is a valid value ──────────────────────────────────────
def test_confidence_is_valid():
    result = ask("What are the side effects of ibuprofen?")
    parsed = json.loads(result)
    confidence = parsed["confidence"]
    assert confidence in ["high", "medium", "low"]  # or assert 0 <= confidence <= 1


# ── Test 5: Answer is substantive ────────────────────────────────────────────
def test_answer_is_not_empty():
    result = ask("Explain the mechanism of ACE inhibitors.")
    parsed = json.loads(result)
    assert len(parsed["answer"]) > 50  # not a one-word brush-off