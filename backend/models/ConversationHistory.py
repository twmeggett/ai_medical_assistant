from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ConversationHistory:
    session_id: str
    user_id: str
    turns: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)