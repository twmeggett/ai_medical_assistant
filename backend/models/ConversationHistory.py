from dataclasses import dataclass, field
from datetime import datetime
from .Turn import Turn

@dataclass
class ConversationHistory:
    session_id: str
    user_id: str
    turns: list[Turn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)