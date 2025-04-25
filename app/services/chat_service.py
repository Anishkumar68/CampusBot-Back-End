from datetime import datetime
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import USER_UPLOAD_PDF_PATH
from models import ChatMessage, ChatSession, User
from schemas import ChatMessageCreate, ChatMessageResponse
from services.auth import get_current_user
from services.llm_handler import LLMHandler


class ChatService:
    def __init__(self, db):
        self.db = db

    async def handle_chat(self, chat_data: ChatMessageCreate) -> ChatMessageResponse:
        # ✅ Validate user ID
        if not chat_data.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # ✅ Validate user
        user = get_current_user(self.db, chat_data.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # ✅ Validate message
        if not chat_data.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # ✅ Get or create chat session ID
        chat_id = chat_data.chat_id or self._start_new_chat(chat_data.user_id)

        # ✅ Determine which PDF is active
        active_pdf_type = (
            "uploaded" if os.path.exists(USER_UPLOAD_PDF_PATH) else "default"
        )

        # ✅ Call LLM
        handler = LLMHandler(model=chat_data.model, temperature=chat_data.temperature)
        response_text = handler.get_response(chat_data.message)

        # ✅ Store both user and bot messages in DB, with PDF type
        user_msg = ChatMessage(
            user_id=chat_data.user_id,
            chat_id=chat_id,
            role="user",
            content=chat_data.message,
            active_pdf_type=active_pdf_type,
        )
        bot_msg = ChatMessage(
            user_id=chat_data.user_id,
            chat_id=chat_id,
            role="bot",
            content=response_text,
            active_pdf_type=active_pdf_type,
        )

        self.db.add_all([user_msg, bot_msg])
        self.db.commit()

        return ChatMessageResponse(chat_id=chat_id, response=response_text)

    from models import ChatSession

    def _start_new_chat(self, user_id: int) -> str:
        latest_chat_session = (
            self.db.query(ChatMessage.chat_id)
            .order_by(ChatMessage.chat_id.desc())
            .first()
        )
        new_chat_number = (
            int(latest_chat_session[0].split("_")[0]) + 1 if latest_chat_session else 1
        )
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"{new_chat_number}_{user_id}_{timestamp}"

        active_pdf_type = (
            "uploaded" if os.path.exists(USER_UPLOAD_PDF_PATH) else "default"
        )

        new_session = ChatSession(
            session_id=session_id, user_id=user_id, active_pdf_type=active_pdf_type
        )
        self.db.add(new_session)
        self.db.commit()

        return session_id
