from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.sql import func
import uuid


# ------- User Table -------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, default="basic")
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    is_premium = Column(Boolean, default=False)
    has_free_pdf_access = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    hashed_password = Column(String)
    chat_sessions = relationship("ChatSession", back_populates="user")
    messages = relationship("ChatMessage", back_populates="user")


# ------- Chat Session Table -------
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    title = Column(String, nullable=False)
    active_pdf_type = Column(String, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")


# ------- Chat Message Table -------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, nullable=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active_pdf_type = Column(String, default="default")

    user = relationship("User", back_populates="messages")
    chat_session = relationship("ChatSession", back_populates="messages")
