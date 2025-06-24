from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import chat, upload, auth

from app.database import Base, engine
from fastapi import FastAPI, Request

from app.utils.rate_limiter import limiter
from slowapi.middleware import SlowAPIMiddleware

app = FastAPI()
# Initialize the rate limiter

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# for auth links
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://campus-bot-front-end.vercel.app",
        "https://campus-bot-front-ktusanzfz-nihal-softwares-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ Starting FastAPI app")

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema created")
except Exception as e:
    print("❌ Database error:", e)


Base.metadata.create_all(bind=engine)

# routing
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/files", tags=["file"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
# app.include_router(buttons.router, prefix="/buttons", tags=["buttons"])  # Enable if needed


# for api running status
@app.get("/")
def root():
    return {"message": "CampusBot API is running."}


# ports for deployment
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
