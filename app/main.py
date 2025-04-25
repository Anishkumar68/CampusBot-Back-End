from fastapi import FastAPI
from routers import chat, upload, auth
from fastapi import Depends
from services.auth import get_current_user

from database import Base, engine
from models import User, ChatMessage, ChatSession
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status


app = FastAPI()

# Allow requests from your React frontend
origins = [
    "http://localhost:5173",
    # add your production frontend URL here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Only allow your dev frontend for now
    allow_credentials=True,
    allow_methods=["*"],  # or specify ["GET", "POST"] if you want to be strict
    allow_headers=["*"],  # or specify ["Authorization", "Content-Type"]
)

# Dependency to get the current user from the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Create tables from models (Dev only; use Alembic in production)
Base.metadata.create_all(bind=engine)

# Register chat route
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/files", tags=["file"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
