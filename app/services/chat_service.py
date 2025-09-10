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
from app.services.memory_handler import MemoryHandler


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

        # === Step 3: Create memory handler for this user/session ===
        memory_handler = MemoryHandler(user_id=str(chat_data.user_id), max_turns=5)

        # === Step 4: Generate LLM response using memory handler ===
        llm_response = self.llm_handler.get_response(
            memory_handler=memory_handler,
            message=chat_data.message,
            use_web_search=False,
        )

        # Extract response data
        response_text = llm_response.get("answer", "No response generated")
        followup_question = llm_response.get("followup_question")
        ai_followups = llm_response.get("ai_followups", [])

        # === Step 5: Store conversation in database ===
        self._store_messages(
            chat_data.user_id,
            session_id,
            chat_data.message,
            response_text,
            active_pdf_type,
        )

        # === Step 6: Return response ===
        return ChatMessageResponse(
            session_id=session_id,
            answer=response_text,
            followup_question=followup_question,
            ai_followups=ai_followups[:3],  # Ensure max 3 followups
            timestamp=datetime.utcnow(),
            success=llm_response.get("success", True),
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
        session_uuid = uuid.uuid4()
        auto_title = self._generate_title_from_message(first_message)

        new_session = ChatSession(
            session_id=session_uuid,
            user_id=user_id,
            title=auto_title,
            active_pdf_type=self._get_active_pdf_type(),
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)

        return new_session.session_id

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
        session_id: UUID,
        user_message: str,
        bot_response: str,
        pdf_type: str,
    ):
        """Store both user and bot messages"""
        messages = [
            ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="user",
                content=user_message,
            ),
            ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="assistant",
                content=bot_response,
            ),
        ]

        self.db.add_all(messages)
        self.db.commit()

    # === Additional Helper Methods ===

    def get_chat_history(self, session_id: UUID, user_id: int) -> list:
        """Get chat history for a specific session"""
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
            .order_by(ChatMessage.timestamp.asc())
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

    def get_chat_with_web_search(
        self, chat_data: ChatMessageCreate
    ) -> ChatMessageResponse:
        """Handle chat with web search enabled"""
        user = self._validate_user(chat_data.user_id)
        self._validate_message(chat_data.message)

        session_id = chat_data.session_id or self._start_new_chat(
            chat_data.user_id, chat_data.message
        )

        # Create memory handler
        memory_handler = MemoryHandler(user_id=str(chat_data.user_id), max_turns=5)

        # Use web search
        llm_response = self.llm_handler.get_response(
            memory_handler=memory_handler,
            message=chat_data.message,
            use_web_search=True,
        )

        response_text = llm_response.get("answer", "Web search completed")
        followup_question = llm_response.get(
            "followup_question", "Would you like to search for more information?"
        )

        # Store in database
        self._store_messages(
            chat_data.user_id,
            session_id,
            chat_data.message,
            response_text,
            "web_search",
        )

        return ChatMessageResponse(
            session_id=session_id,
            answer=response_text,
            followup_question=followup_question,
            ai_followups=[],
            timestamp=datetime.utcnow(),
            success=True,
        )
