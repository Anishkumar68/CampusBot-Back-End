from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Union, Literal
from datetime import datetime
from uuid import UUID, uuid4


# ------------------ Structured Output for LLM ------------------ #
class ResponseFormatter(BaseModel):
    """Structured output format for LLM responses."""

    answer: str = Field(description="The main answer to the user's question")
    followup_question: str = Field(description="A relevant follow-up question")


# ------------------ Incoming Chat Request ------------------ #
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[UUID] = None
    model: str = Field(default="gpt-4o-mini-2024-07-18")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    active_pdf_type: Optional[str] = Field(default="default", max_length=50)


# ------------------ Chat Session Creation ------------------ #
class ChatSessionCreate(BaseModel):
    title: str = Field(default="New Conversation", max_length=100)
    active_pdf_type: str = Field(default="default", max_length=50)


class UpdateSessionTitle(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    active_pdf_type: Optional[str] = Field(None, max_length=50)


# ------------------ Chat Message Creation ------------------ #
class ChatMessageCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[UUID] = None
    model: str = Field(default="gpt-4o-mini-2024-07-18")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    active_pdf_type: str = Field(default="default", max_length=50)


# ------------------ Chat Session Schema ------------------ #
class ChatSessionSchema(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    user_id: int = Field(..., gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    title: str = Field(..., max_length=100)
    active_pdf_type: str = Field(..., max_length=50)

    class Config:
        from_attributes = True


# ------------------ Chat Message Schema ------------------ #
class ChatMessageBase(BaseModel):
    id: int = Field(..., gt=0)
    session_id: UUID
    user_id: int = Field(..., gt=0)
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageBase]
    total_count: int = Field(default=0, ge=0)


# ------------------ Auth Schemas ------------------ #
class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


# ------------------ Enhanced Chat Response ------------------ #
class ChatMessageResponse(BaseModel):
    session_id: UUID
    answer: str = Field(description="The main response content")
    followup_question: Optional[str] = Field(
        default=None, description="Suggested follow-up"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(default=True)

    class Config:
        from_attributes = True


# ------------------ Error Response ------------------ #
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = Field(default=False)


# ------------------ Auto Title Update ------------------ #
class AutoTitleUpdate(BaseModel):
    """Schema for auto-updating session title with first question"""

    session_id: UUID
    first_message: str = Field(..., min_length=1, max_length=1000)

    def generate_title(self) -> str:
        """Generate title from first message (max 50 chars)"""
        if len(self.first_message) > 47:
            return self.first_message[:47] + "..."
        return self.first_message
