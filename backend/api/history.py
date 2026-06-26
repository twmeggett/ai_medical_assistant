from fastapi import APIRouter

router = APIRouter()

@router.get("/{user_id}")
async def get_history(user_id: int):
    history = [] # TODO - Perform database query for user's chat history  
    return history