from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.models import ChatMessage, ChatSession, User
from app.database import get_db
from app.schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageBase,
    ChatSessionSchema,
)
from app.services.auth import get_current_user, get_current_user_from_token
from app.services.chat_service import ChatService

router = APIRouter()


# ✅ Define request schema
class ChatRequest(BaseModel):
    user_id: int
    message: str
    chat_id: Optional[str] = None
    model: str = "openai"
    temperature: float = 0.7


# ✅ POST /chat endpoint
@router.post("/", response_model=ChatMessageResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    chat_message = ChatMessageCreate(
        user_id=current_user.id,  # take from token
        message=request.message,
        chat_id=request.chat_id,
        model=request.model,
        temperature=request.temperature,
    )

    chat_service = ChatService(db)
    response = await chat_service.handle_chat(chat_message)

    return response


@router.get("/history/{chat_id}", response_model=List[ChatMessageBase])
def get_chat_history(
    chat_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    return messages


@router.get("/sessions/{user_id}", response_model=List[ChatSessionSchema])
def get_user_chat_sessions(user_id: int, db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions
