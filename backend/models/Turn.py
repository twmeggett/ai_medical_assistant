from typing import TypedDict, Literal

class Turn(TypedDict):
    role: Literal['user', 'assistant']
    content: str