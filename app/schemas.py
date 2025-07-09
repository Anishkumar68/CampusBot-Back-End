from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime


# ------- Incoming Chat Request from Frontend (NO user_id needed now)
class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    active_pdf_type: Optional[str] = "default"


class ChatSessionCreate(BaseModel):
    title: str
    active_pdf_type: str


class UpdateSessionTitle(BaseModel):
    title: str


# ------- Create Chat Message inside backend
class ChatMessageCreate(BaseModel):
    user_id: int
    message: str
    chat_id: Optional[str]  # Same as ChatRequest
    model: str
    temperature: float
    active_pdf_type: str


class ChatMessageCreate(BaseModel):
    user_id: int
    message: str
    chat_id: Optional[str] = None


# ------- Chat Session (History of chats)
class ChatSessionSchema(BaseModel):
    session_id: str
    user_id: int
    created_at: datetime
    title: str
    active_pdf_type: str

    class Config:
        from_attributes = True  # Pydantic v2 style


# ------- Chat Message (full history message model)
class ChatMessageBase(BaseModel):
    id: int
    chat_id: str
    user_id: int
    role: str
    content: str
    timestamp: datetime
    active_pdf_type: str

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageBase]


# schema
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChatMessageResponse(BaseModel):
    chat_id: str
    response: str
    followups: Optional[Dict[str, List[str]]] = None  # <== Add this

    class Config:
        from_attributes = True
