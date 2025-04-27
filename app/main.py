from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


origins = ["*"]  # Allow all (temporary fix)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Now import and add routers
from routers import chat, upload, auth
from database import Base, engine

Base.metadata.create_all(bind=engine)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(upload.router, prefix="/files", tags=["file"])
app.include_router(auth.router, prefix="/auth")
