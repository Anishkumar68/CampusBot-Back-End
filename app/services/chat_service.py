from datetime import datetime
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import USER_UPLOAD_PDF_PATH

from models import ChatMessage, ChatSession, User
from schemas import ChatMessageCreate, ChatMessageResponse
from services.llm_handler import LLMHandler
from utils.pdf_loader import process_pdf_and_store


class ChatService:
    def __init__(self, db: Session):
        self.db = db

    async def handle_chat(self, chat_data: ChatMessageCreate) -> ChatMessageResponse:
        # Validate user
        user = self.db.query(User).filter(User.id == chat_data.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate message
        if not chat_data.message or not chat_data.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Get or create chat session
        chat_id = chat_data.chat_id or self._start_new_chat(chat_data.user_id)

        # Detect active PDF
        active_pdf_type = self._get_active_pdf_type()

        # Call LLM
        handler = LLMHandler(model=chat_data.model, temperature=chat_data.temperature)
        response_text = handler.get_response(chat_data.message)

        # Store user + bot messages
        self.db.add_all(
            [
                ChatMessage(
                    user_id=chat_data.user_id,
                    chat_id=chat_id,
                    role="user",
                    content=chat_data.message,
                    active_pdf_type=active_pdf_type,
                ),
                ChatMessage(
                    user_id=chat_data.user_id,
                    chat_id=chat_id,
                    role="bot",
                    content=response_text,
                    active_pdf_type=active_pdf_type,
                ),
            ]
        )
        self.db.commit()

        return ChatMessageResponse(chat_id=chat_id, response=response_text)

    def _start_new_chat(self, user_id: int) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"chat_{user_id}_{timestamp}"

        self.db.add(
            ChatSession(
                session_id=session_id,
                user_id=user_id,
                active_pdf_type=self._get_active_pdf_type(),
            )
        )
        self.db.commit()

        return session_id

    def _get_active_pdf_type(self) -> str:
        return "uploaded" if os.path.exists(USER_UPLOAD_PDF_PATH) else "default"
