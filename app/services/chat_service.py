from datetime import datetime
import os
import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import USER_UPLOAD_PDF_PATH
from app.models import ChatMessage, ChatSession, User
from app.schemas import ChatMessageCreate, ChatMessageResponse
from app.services.llm_handler import get_llm_handler
from app.utils.intent_matcher import match_intent
from app.utils.pdf_loader import process_pdf_and_store
from app.utils.button_loader import get_button_questions


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_handler = get_llm_handler()

    async def handle_chat(self, chat_data: ChatMessageCreate) -> ChatMessageResponse:
        # === Step 1: Validate input ===
        user = self._validate_user(chat_data.user_id)
        self._validate_message(chat_data.message)

        # === Step 2: Setup chat session ===
        session_id = chat_data.session_id or self._start_new_chat(
            chat_data.user_id, chat_data.message
        )
        active_pdf_type = self._get_active_pdf_type()

        # === Step 3: Generate LLM response
        response_text = self.llm_handler.get_response(
            str(chat_data.user_id), chat_data.message
        )

        # === Step 4: AI-generated follow-up questions
        ai_followups = self.llm_handler.suggest_followups(
            chat_data.message, response_text
        )

        # === Step 5: Store conversation
        self._store_messages(
            chat_data.user_id,
            session_id,
            chat_data.message,
            response_text,
            active_pdf_type,
        )

        # === Step 6: Return response
        return ChatMessageResponse(
            session_id=session_id,
            response=response_text,
            followups={"ai_generated": ai_followups},
        )

    # === Internal Helpers ===

    def _validate_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        return user

    def _validate_message(self, message: str):
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

    def _start_new_chat(self, user_id: int, first_message: str) -> UUID:
        """Create new chat session and auto-generate title from first message"""
        # ✅ Generate UUID object, not string
        session_uuid = uuid.uuid4()

        # ✅ Auto-generate title from first message (max 50 chars as per model)
        auto_title = self._generate_title_from_message(first_message)

        new_session = ChatSession(
            session_id=session_uuid,  # ✅ Pass UUID object
            user_id=user_id,
            title=auto_title,  # ✅ Use auto-generated title
            active_pdf_type=self._get_active_pdf_type(),
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)  # ✅ Get the saved session

        return new_session.session_id  # ✅ Return UUID object

    def _generate_title_from_message(self, message: str) -> str:
        """Generate session title from first message (max 50 chars)"""
        if len(message) > 47:
            return message[:47] + "..."
        return message

    def _get_active_pdf_type(self) -> str:
        return "uploaded" if os.path.exists(USER_UPLOAD_PDF_PATH) else "default"

    def _store_messages(
        self,
        user_id: int,
        session_id: UUID,  # ✅ Accept UUID type
        user_message: str,
        bot_response: str,
        pdf_type: str,
    ):
        """Store both user and bot messages"""
        messages = [
            ChatMessage(
                user_id=user_id,
                session_id=session_id,  # ✅ Pass UUID object
                role="user",
                content=user_message,
            ),
            ChatMessage(
                user_id=user_id,
                session_id=session_id,  # ✅ Pass UUID object
                role="bot",
                content=bot_response,
            ),
        ]

        self.db.add_all(messages)
        self.db.commit()

    # === Additional Helper Methods ===

    def get_chat_history(self, session_id: UUID, user_id: int) -> list:
        """Get chat history for a specific session"""
        # Validate session belongs to user
        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id, ChatSession.user_id == user_id
            )
            .first()
        )

        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
            .all()
        )

        return messages

    def get_user_sessions(self, user_id: int) -> list:
        """Get all chat sessions for a user"""
        sessions = (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

        return sessions

    def update_session_title(self, session_id: UUID, user_id: int, new_title: str):
        """Update session title"""
        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id, ChatSession.user_id == user_id
            )
            .first()
        )

        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        session.title = new_title[:50]  # Ensure max length
        self.db.commit()

        return session
