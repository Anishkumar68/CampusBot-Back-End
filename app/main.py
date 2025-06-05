from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from routers.buttons import

app = FastAPI()

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://campus-bot-front-end.vercel.app/", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Now import and add routers
from app.routers import chat, upload, auth
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/files", tags=["file"])
app.include_router(auth.router, prefix="/auth")
# app.include_router(buttons.router, prefix="/buttons")
