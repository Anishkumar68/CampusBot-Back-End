from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


# ------------------ Incoming Chat Request from Frontend ------------------ #
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    model: str = "gpt-4.1-mini-2025-04-14"
    temperature: float = 0.2
    active_pdf_type: Optional[str] = "default"


# ------------------ Chat Session Creation ------------------ #
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "student_Questions"
    active_pdf_type: Optional[str] = "default"


class UpdateSessionTitle(BaseModel):
    title: Optional[str] = None
    active_pdf_type: Optional[str] = None


# ------------------ Chat Message Creation ------------------ #
class ChatMessageCreate(BaseModel):
    user_id: int
    message: str
    session_id: Optional[UUID] = None
    model: str = "gpt-4.1-mini-2025-04-14"
    temperature: float = 0.2
    active_pdf_type: str = "default"


# ------------------ Chat Session Schema ------------------ #
class ChatSessionSchema(BaseModel):
    session_id: UUID
    user_id: int
    created_at: datetime
    title: str
    active_pdf_type: str

    class Config:
        from_attributes = True


# ------------------ Chat Message Schema ------------------ #
class ChatMessageBase(BaseModel):
    id: int
    session_id: UUID
    user_id: int
    role: str
    content: str
    timestamp: datetime

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
    session_id: UUID
    response: str
    followups: Optional[Dict[str, List[str]]] = None

    class Config:
        from_attributes = True


# ------------------ Auto Title Update Helper Schema ------------------ #
class AutoTitleUpdate(BaseModel):
    """Schema for auto-updating session title with first question"""

    session_id: UUID
    first_message: str

    def generate_title(self) -> str:
        """Generate title from first message (max 50 chars as per model)"""
        # Take first 47 chars and add "..." if longer
        if len(self.first_message) > 47:
            return self.first_message[:47] + "..."
        return self.first_message
