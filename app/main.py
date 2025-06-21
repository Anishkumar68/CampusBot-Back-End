from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers import chat, upload, auth

from app.database import Base, engine


from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI()

# Create app and limiter
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)

# Register the rate-limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# for auth links
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://campus-bot-front-end.vercel.app",
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
