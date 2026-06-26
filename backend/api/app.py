from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .chat import router as chat_router
from .history import router as history_router

app = FastAPI()

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
app.include_router(history_router, prefix="/history")
