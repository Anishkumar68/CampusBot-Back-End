from datetime import datetime
import os

from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import USER_UPLOAD_PDF_PATH
from models import ChatMessage, ChatSession, User
from schemas import ChatMessageCreate, ChatMessageResponse
from utils.button_loader import (
    get_button_questions,
)
from utils.intent_matcher import match_intent
from utils.suggestion_engine import get_rule_based_suggestions


from services.llm_handler import (
    LLMHandler,
)  # Assuming this is a utility function to get the LLM handler
from utils.pdf_loader import (
    process_pdf_and_store,
)  # Assuming this is a utility function to process PDFs


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        # Use a single cached handler to retain memory/chat history
        self.llm_handler = LLMHandler()

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

        # Optionally track which PDF is active (if PDF QA comes later)
        active_pdf_type = self._get_active_pdf_type()

        # Call LLMHandler for a prompt-based reply
        response_text = self.llm_handler.get_response(chat_data.message)

        matched = match_intent(chat_data.message)

        rule_followups = []
        if matched:
            rule_followups = get_rule_based_suggestions(
                topic_tag=matched["topic_tag"], exclude_id=matched["id"]
            )

        # === Step 2: AI-generated followups ===
        ai_followups = self.llm_handler.suggest_followups(
            chat_data.message, response_text
        )

        # Store user + bot messages in DB
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
        return ChatMessageResponse(
            chat_id=chat_id,
            response=response_text,
            followups={
                "rule_based": [btn["question_text"] for btn in rule_followups],
                "ai_generated": ai_followups,
            },
        )

        # return ChatMessageResponse(chat_id=chat_id, response=response_text)

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
