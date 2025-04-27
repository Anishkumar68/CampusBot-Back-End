from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


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
        String, primary_key=True, unique=True, index=True
    )  # ✅ primary key
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String, default="Untitled Chat")
    active_pdf_type = Column(String, default="default")

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")
    # fixed here
    # messages = relationship("ChatMessage", back_populates="chat_session")  # fixed here


# ------- Chat Message Table -------
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chat_sessions.session_id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    active_pdf_type = Column(String, default="default")

    user = relationship("User", back_populates="messages")
    chat_session = relationship("ChatSession", back_populates="messages")
