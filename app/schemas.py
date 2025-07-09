from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ------------------ Incoming Chat Request from Frontend ------------------ #
class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    active_pdf_type: Optional[str] = "default"

    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I apply?",
                "chat_id": None,
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "active_pdf_type": "default",
            }
        }


# ------------------ Chat Session Creation ------------------ #
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "Untitled Session"
    active_pdf_type: Optional[str] = "default"

    class Config:
        json_schema_extra = {
            "example": {"title": "Application Questions", "active_pdf_type": "default"}
        }


class UpdateSessionTitle(BaseModel):
    title: Optional[str] = None
    active_pdf_type: Optional[str] = None


# ------------------ Chat Message Creation ------------------ #
class ChatMessageCreate(BaseModel):
    user_id: int
    message: str
    chat_id: Optional[str] = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    active_pdf_type: str = "default"


# ------------------ Chat Session Schema ------------------ #
class ChatSessionSchema(BaseModel):
    session_id: str
    user_id: int
    created_at: datetime
    title: str
    active_pdf_type: str

    class Config:
        from_attributes = True


# ------------------ Chat Message Schema ------------------ #
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


# ------------------ Auth & Token Schemas ------------------ #
class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ------------------ Final Chat Response ------------------ #
class ChatMessageResponse(BaseModel):
    chat_id: str
    response: str
    followups: Optional[Dict[str, List[str]]] = None

    class Config:
        from_attributes = True
