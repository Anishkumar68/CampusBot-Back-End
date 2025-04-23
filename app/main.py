from fastapi import FastAPI
from app.routers import chat, upload
from app.database import Base, engine
from app import models
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, upload, auth

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or restrict in prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables from models (Dev only; use Alembic in production)
Base.metadata.create_all(bind=engine)

# Register chat route
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/files", tags=["file"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
