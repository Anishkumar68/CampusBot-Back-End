import os
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import USER_UPLOAD_PDF_PATH
from app.models.models import ChatMessage, ChatSession, User
from app.schemas import ChatMessageCreate, ChatMessageResponse
from app.services.llm_handler import get_llm_handler
from app.utils.intent_matcher import match_intent
from app.utils.document_indexer import process_pdf_and_store


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_handler = get_llm_handler()

    async def handle_chat(self, chat_data: ChatMessageCreate) -> ChatMessageResponse:
        # 1️⃣ Validate input
        user = self._validate_user(chat_data.user_id)
        self._validate_message(chat_data.message)

        # 2️⃣ If user uploaded PDF in this request, process it
        if getattr(chat_data, "uploaded_pdf_bytes", None):
            process_pdf_and_store(
                chat_data.uploaded_pdf_bytes, user_id=chat_data.user_id
            )
            # After storing, you may want to re-index in RAG pipeline, etc.

        # 3️⃣ Decide session
        session_id = chat_data.session_id or self._start_new_chat(
            chat_data.user_id, chat_data.message
        )
        pdf_context_type = self._get_active_pdf_type()

        # 4️⃣ Optionally route by intent
        intent = match_intent(chat_data.message)
        # You can extend llm_handler to support different chains by intent
        # e.g. if intent == "quiz_generation": llm_handler.call_quiz_chain(...)

        # 5️⃣ Get LLM / RAG response (this method should encapsulate fallback logic)
        response_text, extra = self.llm_handler.get_response_with_metadata(
            user_id=str(chat_data.user_id),
            message=chat_data.message,
        )
        # `extra` might contain metadata like “used_web_search”, “source_urls”, etc.

        # 6️⃣ Generate follow-ups
        ai_followups = self.llm_handler.suggest_followups(
            chat_data.message, response_text
        )

        # 7️⃣ Persist messages
        self._store_messages(
            chat_data.user_id,
            session_id,
            chat_data.message,
            response_text,
            pdf_context_type,
        )

        # 8️⃣ Build response schema
        resp = ChatMessageResponse(
            session_id=session_id,
            response=response_text,
            followups={"ai_generated": ai_followups},
        )

        # 9️⃣ If extra metadata (like source links), include in schema
        if extra and "source_urls" in extra:
            resp.source_urls = extra["source_urls"]

        return resp

    def _validate_user(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        return user

    def _validate_message(self, message: str):
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

    def _start_new_chat(self, user_id: int, first_message: str) -> UUID:
        session_uuid = uuid4()
        title = self._generate_title_from_message(first_message)
        new_session = ChatSession(
            session_id=session_uuid,
            user_id=user_id,
            title=title,
            active_pdf_type=self._get_active_pdf_type(),
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session.session_id

    def _generate_title_from_message(self, message: str) -> str:
        return message[:47] + "..." if len(message) > 47 else message

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
        msgs = [
            ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="user",
                content=user_message,
            ),
            ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="bot",
                content=bot_response,
            ),
        ]
        self.db.add_all(msgs)
        self.db.commit()

    def get_chat_history(self, session_id: UUID, user_id: int):
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

    def get_user_sessions(self, user_id: int):
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def update_session_title(self, session_id: UUID, user_id: int, new_title: str):
        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
            .first()
        )
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        session.title = new_title[:50]
        self.db.commit()
        return session
