from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import ChatMessage, ChatSession, User
from app.database import get_db
from app.schemas import (
    ChatRequest,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageBase,
    ChatSessionSchema,
)

from app.services.chat_service import ChatService
from app.services.auth import get_current_user, require_role
from app.config import USER_UPLOAD_PDF_PATH, DEFAULT_PDF_PATH
from app.utils.pdf_loader import process_pdf_and_store
from typing import List


# rate limit imports slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.extension import Limiter
from fastapi import Request

router = APIRouter()


#  POST /chat endpoint
@router.post("/", response_model=ChatMessageResponse)
@Limiter.limit("5/minutes")
async def chat(
    request: Request,
    request_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat_message = ChatMessageCreate(
        user_id=current_user.id,  #  Automatically set from token
        message=request_data.message,
        chat_id=request_data.chat_id,
        model=request_data.model,
        temperature=request_data.temperature,
        active_pdf_type=request_data.active_pdf_type or "default",
    )

    chat_service = ChatService(db)
    response = await chat_service.handle_chat(chat_message)

    return response


#  GET /chat/history/{chat_id}
@router.get("/history/{chat_id}", response_model=List[ChatMessageBase])
def get_chat_history(
    chat_id: str,
    current_user: User = Depends(get_current_user),
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


#  GET /chat/sessions/{user_id}
@router.get("/sessions/{user_id}", response_model=List[ChatSessionSchema])
def get_user_chat_sessions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this user's sessions"
        )

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions


#  POST /chat/sessions
@router.post("/sessions", response_model=ChatSessionSchema)
def create_chat_session(
    session: ChatSessionSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_session = ChatSession(
        user_id=current_user.id,
        title=session.title,
        active_pdf_type=session.active_pdf_type,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


#  DELETE /chat/sessions/{session_id}
@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this session"
        )

    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}


#  DELETE /chat/history/{chat_id}
@router.delete("/history/{chat_id}")
def delete_chat_history(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = db.query(ChatMessage).filter(ChatMessage.chat_id == chat_id).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    for message in messages:
        db.delete(message)
    db.commit()
    return {"message": "Chat history deleted successfully"}


#  GET /chat/active_pdf_types
@router.get("/active_pdf_types")
def get_active_pdf_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Get the active PDF types for the current user
    active_pdf_types = (
        db.query(ChatSession.active_pdf_type)
        .filter(ChatSession.user_id == current_user.id)
        .distinct()
        .all()
    )

    if not active_pdf_types:
        raise HTTPException(status_code=404, detail="No active PDF types found")

    return [pdf_type[0] for pdf_type in active_pdf_types]


#  POST /chat/sessions/{session_id}/set_active_pdf
@router.post("/sessions/{session_id}/set_active_pdf")
def set_active_pdf_type(
    session_id: str,
    active_pdf_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to set active PDF type"
        )

    session.active_pdf_type = active_pdf_type
    db.commit()
    return {"message": "Active PDF type updated successfully"}


#  GET /chat/sessions/{session_id}/messages
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageBase])
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")
    return messages
