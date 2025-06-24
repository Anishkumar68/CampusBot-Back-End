from datetime import datetime
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import USER_UPLOAD_PDF_PATH
from app.models import ChatMessage, ChatSession, User
from app.schemas import ChatMessageCreate, ChatMessageResponse
from app.services.llm_handler import get_llm_handler, LLMHandler
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
        chat_id = chat_data.chat_id or self._start_new_chat(chat_data.user_id)
        active_pdf_type = self._get_active_pdf_type()

        # === Step 3: Generate LLM response (pass user_id as string)
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
            chat_id,
            chat_data.message,
            response_text,
            active_pdf_type,
        )

        # === Step 6: Return response
        return ChatMessageResponse(
            chat_id=chat_id,
            response=response_text,
            followups={
                "ai_generated": ai_followups,
            },
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

    def _start_new_chat(self, user_id: int) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"chat_{user_id}_{timestamp}"
        chat_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            active_pdf_type=self._get_active_pdf_type(),
        )
        self.db.add(chat_session)
        self.db.commit()
        return session_id

    def _get_active_pdf_type(self) -> str:
        return "uploaded" if os.path.exists(USER_UPLOAD_PDF_PATH) else "default"

    def _store_messages(
        self,
        user_id: int,
        chat_id: str,
        user_message: str,
        bot_response: str,
        pdf_type: str,
    ):
        self.db.add_all(
            [
                ChatMessage(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="user",
                    content=user_message,
                    active_pdf_type=pdf_type,
                ),
                ChatMessage(
                    user_id=user_id,
                    chat_id=chat_id,
                    role="bot",
                    content=bot_response,
                    active_pdf_type=pdf_type,
                ),
            ]
        )
        self.db.commit()
