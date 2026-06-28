from dataclasses import dataclass

@dataclass(frozen=True)
class PromptVersion:
    content: str
    version: str
    sprint: int
    optimized_for: str
    notes: str
    changed_from: str | None = None