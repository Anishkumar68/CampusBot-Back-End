from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import uuid
from uuid import UUID

from app.models import ChatMessage, ChatSession, User
from app.database import get_db
from app.schemas import (
    ChatRequest,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessageBase,
    ChatSessionSchema,
    ChatSessionCreate,
    UpdateSessionTitle,
)
from app.services.chat_service import ChatService
from app.services.auth import get_current_user
from app.utils.rate_limiter import limiter

router = APIRouter()


# ---------------- POST /chat ----------------
@router.post("/", response_model=ChatMessageResponse)
@limiter.limit("10/minute")
async def handle_chat(
    request: Request,
    chat_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat_service = ChatService(db)
    chat_data.user_id = current_user.id
    return await chat_service.handle_chat(chat_data)


# ---------------- GET /chat/history/{session_id} ----------------
@router.get("/history/{session_id}", response_model=List[ChatMessageBase])
def get_chat_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    return messages


# ---------------- GET /chat/sessions/{user_id} ----------------
@router.get("/sessions/{user_id}", response_model=List[ChatSessionSchema])
def get_chat_sessions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to view these sessions"
        )

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions


# ---------------- POST /chat/sessions ----------------
@router.post("/sessions", response_model=ChatSessionSchema)
def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or "Untitled Session",
        active_pdf_type=session_data.active_pdf_type or "default",
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


# ---------------- PUT /chat/sessions/{session_id} ----------------
@router.put("/sessions/{session_id}", response_model=ChatSessionSchema)
def update_chat_session(
    session_id: UUID,
    session_update: UpdateSessionTitle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this session"
        )

    if session_update.title:
        session.title = session_update.title[:50]
    if session_update.active_pdf_type:
        session.active_pdf_type = session_update.active_pdf_type

    db.commit()
    db.refresh(session)
    return session


# ---------------- DELETE /chat/sessions/{session_id} ----------------
@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: UUID,
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


# ---------------- DELETE /chat/history/{session_id} ----------------
@router.delete("/history/{session_id}")
def delete_chat_history(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    for message in messages:
        db.delete(message)
    db.commit()
    return {"message": "Chat history deleted successfully"}


# ---------------- GET /chat/active_pdf_types ----------------
@router.get("/active_pdf_types")
def get_active_pdf_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pdf_types = (
        db.query(ChatSession.active_pdf_type)
        .filter(ChatSession.user_id == current_user.id)
        .distinct()
        .all()
    )

    if not pdf_types:
        return []

    return [pt[0] for pt in pdf_types]


# ---------------- POST /chat/sessions/{session_id}/set_active_pdf ----------------
@router.post("/sessions/{session_id}/set_active_pdf")
def set_active_pdf_type(
    session_id: UUID,
    active_pdf_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.active_pdf_type = active_pdf_type
    db.commit()
    return {"message": "Active PDF type updated successfully"}


# ---------------- GET /chat/sessions/{session_id}/messages ----------------
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageBase])
def get_session_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    return messages


# endpoint to access and validate session
@router.get("/sessions/{session_id}/validate")
def validate_session_access(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Validate that a session exists and user has access to it"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "session_id": session.session_id,
        "title": session.title,
        "active_pdf_type": session.active_pdf_type,
        "created_at": session.created_at,
    }
