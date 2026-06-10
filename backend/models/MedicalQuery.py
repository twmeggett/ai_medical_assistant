from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MedicalQuery:
    user_id: str
    query_text: str
    session_id: str
    timestamp: datetime = field(default_factory=datetime.now)
