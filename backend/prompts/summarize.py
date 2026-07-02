from backend.models.prompts import PromptVersion

SUMMARIZE_QUERY_V1 = PromptVersion(
    content="Summarize the user's message into a short title of 4-6 words. Reply with only the title, no punctuation.",
    version="1.0",
    sprint=3,
    optimized_for="concise conversation title generation",
    notes="Used to auto-title new conversations after the first user message",
)

ACTIVE_SUMMARIZE_PROMPT = SUMMARIZE_QUERY_V1
