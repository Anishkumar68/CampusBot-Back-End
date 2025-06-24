import os
from dotenv import load_dotenv
from urllib.parse import urlparse

from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()


class MemoryHandler:
    def __init__(self, user_id: str, max_turns: int = 5, ttl_seconds: int = 3600):
        self.user_id = user_id
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("❌ REDIS_URL not set in environment.")

        parsed_url = urlparse(redis_url)
        if parsed_url.scheme not in ["redis", "rediss"]:
            raise ValueError("❌ Invalid REDIS_URL scheme.")

        self.chat_history = RedisChatMessageHistory(
            session_id=f"chat:{self.user_id}", url=redis_url, ttl=self.ttl_seconds
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=self.chat_history,
        )

    def add_user_message(self, message: str):
        self.memory.chat_memory.add_user_message(message)

    def add_ai_message(self, message: str):
        self.memory.chat_memory.add_ai_message(message)

    def get_messages(self) -> list:
        return self.memory.load_memory_variables({}).get("chat_history", [])

    def clear(self):
        if hasattr(self.memory.chat_memory, "clear"):
            self.memory.chat_memory.clear()
