from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ------- Chat Input -------
class ChatMessageCreate(BaseModel):
    user_id: int
    message: str
    chat_id: Optional[int]
    model: str
    temperature: float


class ChatMessageResponse(BaseModel):
    chat_id: int
    response: str


class ChatSessionSchema(BaseModel):
    session_id: str
    user_id: int
    created_at: datetime
    title: str
    active_pdf_type: str

    class Config:
        orm_mode = True


# ------- Full Chat Message Model -------
class ChatMessageBase(BaseModel):
    id: int
    chat_id: str
    user_id: int
    role: str
    content: str
    timestamp: datetime
    active_pdf_type: str

    class Config:
        orm_mode = True
