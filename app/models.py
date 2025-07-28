from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid

from app.database import Base


# ---------------------- User Table ---------------------- #
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(50), default="basic", nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), unique=True, index=True, nullable=False)
    is_premium = Column(Boolean, default=False)
    has_free_pdf_access = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    hashed_password = Column(String(255), nullable=False, unique=True, index=True)

    # Relationships
    chat_sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete"
    )
    messages = relationship("ChatMessage", back_populates="user", cascade="all, delete")


# ---------------------- Chat Session Table ---------------------- #
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    title = Column(String(50), nullable=False, default="Untitled Session")
    active_pdf_type = Column(String(50), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="chat_session", cascade="all, delete"
    )


# ---------------------- Chat Message Table ---------------------- #
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    role = Column(String(50), nullable=True)  # e.g. "user" or "bot"
    content = Column(Text, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="messages")
    chat_session = relationship("ChatSession", back_populates="messages")
