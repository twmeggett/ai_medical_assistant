import re
import logging
from backend.prompts import INJECTION_PATTERNS

logger = logging.getLogger(__name__)


def strip_injection_patterns(text: str) -> str:
    lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if pattern in lower:
            logger.warning("Potential prompt injection detected in tool output: %s", pattern)
            text = re.sub(re.escape(pattern), "[FILTERED]", text, flags=re.IGNORECASE)

    return text
