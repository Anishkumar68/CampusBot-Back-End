from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# from routers.buttons import

app = FastAPI()

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://campus-bot-front-end.vercel.app"],
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",  # Adjust path if needed
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),  # Render uses dynamic $PORT
    )
