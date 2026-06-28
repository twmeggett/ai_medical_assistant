from fastapi import APIRouter

router = APIRouter()

@router.get("/{session_id}")
async def get_history(session_id: int):
    history = [] # TODO - Perform database query for session's chat history  
    return history