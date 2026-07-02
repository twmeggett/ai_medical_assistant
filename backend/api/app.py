import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

from backend.db.connector import connect, disconnect
from .chat import router as chat_router
from .conversation import router as conversation_router
from .message import router as message_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",      # Common React development port
    "http://localhost:5173",      # Common Vite/Vue development port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allow specified origins
    allow_credentials=True,         # Allow cookies and authentication headers
    allow_methods=["*"],            # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # Allow all request headers
)

@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}

app.include_router(chat_router, prefix="/chat")
app.include_router(conversation_router, prefix="/conversation")
app.include_router(message_router, prefix="/message")
