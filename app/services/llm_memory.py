import os
from dotenv import load_dotenv
from urllib.parse import urlparse

from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()


class RedisMemoryHandler:
    def __init__(self, user_id: str, max_turns: int = 5, ttl_seconds: int = 3600):
        self.user_id = user_id
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds

        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            raise ValueError("❌ REDIS_URL not set in environment.")

        parsed_url = urlparse(self.redis_url)
        self.is_redis = parsed_url.scheme in ["redis", "rediss"]

        if self.is_redis:
            self.chat_history = RedisChatMessageHistory(
                session_id=f"chat:{self.user_id}",
                url=self.redis_url,
                ttl=self.ttl_seconds,
            )
        else:
            raise EnvironmentError(
                "Only Redis-based memory is supported in this handler."
            )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=self.chat_history,
        )

    def add_message(self, content: str, role: str):
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "ai":
            self.memory.chat_memory.add_ai_message(content)
        else:
            raise ValueError("Role must be 'user' or 'ai'.")

    def get_messages(self):
        return self.memory.load_memory_variables({}).get("chat_history", [])

    def get_messages_as_str(self):
        messages = self.get_messages()
        return "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Bot'}: {m.content}"
            for m in messages
        )

    def get_messages_as_json(self):
        messages = self.get_messages()
        return [
            {
                "role": "user" if isinstance(m, HumanMessage) else "ai",
                "content": m.content,
            }
            for m in messages
        ]

    def clear(self):
        self.memory.chat_memory.clear()
