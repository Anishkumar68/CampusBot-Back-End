import os
import redis
from dotenv import load_dotenv

from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.schema import AIMessage, HumanMessage

load_dotenv()


class MemoryHandler:
    def __init__(self, user_id: str, max_turns: int = 5, ttl_seconds: int = 3600):
        self.user_id = user_id
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds
        self.redis_url = os.getenv("REDIS_URL")

        # Initialize Redis chat history
        self.chat_history = RedisChatMessageHistory(
            session_id=f"chat:{self.user_id}",
            url=self.redis_url,
        )

        # Memory with chat history
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=self.chat_history,
        )

        self.is_redis = isinstance(self.chat_history, RedisChatMessageHistory)
        self._expire_redis_key()  # 🔁 Set TTL once at init

    def add_user_message(self, content: str):
        self.memory.chat_memory.add_user_message(content)
        self._trim_memory()
        self._expire_redis_key()

    def add_ai_message(self, content: str):
        self.memory.chat_memory.add_ai_message(content)
        self._trim_memory()
        self._expire_redis_key()

    def _trim_memory(self):
        # Trimming is not supported on RedisChatMessageHistory
        if self.is_redis:
            return

        messages = self.memory.chat_memory.messages

        if len(messages) % 2 != 0:
            messages = messages[:-1]  # Drop incomplete pair

        if len(messages) > self.max_turns * 2:
            self.memory.chat_memory.messages = messages[-self.max_turns * 2 :]

    def _expire_redis_key(self):
        if self.is_redis:
            try:
                redis_client = redis.from_url(self.redis_url)
                redis_client.expire(f"chat:{self.user_id}", self.ttl_seconds)
            except Exception as e:
                print(f"[Redis TTL Error] User {self.user_id} — {e}")

    def get_messages(self):
        return self.memory.chat_memory.messages

    def get_memory(self):
        return self.memory

    def get_chat_history(self):
        return self.memory.chat_memory.get_messages()

    def clear(self):
        self.memory.chat_memory.clear()
        self._expire_redis_key()

    def get_memory_json(self):
        return [
            {
                "type": "human" if isinstance(msg, HumanMessage) else "ai",
                "content": msg.content,
            }
            for msg in self.get_messages()
        ]

    def get_memory_text(self):
        return "\n".join(
            [
                f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
                for msg in self.get_messages()
            ]
        )

    def get_user_id(self):
        return self.user_id

    def get_backend_type(self):
        return "redis" if self.is_redis else "local"
