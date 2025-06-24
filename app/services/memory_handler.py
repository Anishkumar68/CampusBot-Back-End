import os
import redis
from dotenv import load_dotenv
from urllib.parse import urlparse

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
        if not self.redis_url:
            raise ValueError("REDIS_URL not set")

        parsed_url = urlparse(self.redis_url)
        self.is_redis = parsed_url.scheme in ["redis", "rediss"]

        if self.is_redis:
            self.chat_history = RedisChatMessageHistory(
                session_id=f"chat:{self.user_id}",
                url=self.redis_url,
            )
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                chat_memory=self.chat_history,
            )
        else:
            self.chat_history = None
            self.memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )

    def add_user_message(self, content: str):
        self.memory.chat_memory.add_user_message(content)
        self._trim_memory()

    def add_ai_message(self, content: str):
        self.memory.chat_memory.add_ai_message(content)
        self._trim_memory()

    def _trim_memory(self):
        # Only trim local memory, RedisChatMessageHistory is already turn-based
        if not self.is_redis:
            messages = self.memory.chat_memory.messages
            if len(messages) % 2 != 0:
                messages = messages[:-1]
            if len(messages) > self.max_turns * 2:
                self.memory.chat_memory.messages = messages[-self.max_turns * 2 :]

    def get_messages(self):
        return self.memory.chat_memory.get_messages()

    def get_memory_text(self):
        return "\n".join(
            f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
            for msg in self.get_messages()
        )

    def clear(self):
        self.memory.chat_memory.clear()

    def get_messages(self):
        return self.memory.chat_memory.get_messages()

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
            f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
            for msg in self.get_messages()
        )

    def get_chat_history(self):
        return self.memory.chat_memory.get_messages()

    def get_backend_type(self):
        return "redis" if self.is_redis else "local"

    def get_user_id(self):
        return self.user_id

    def get_max_turns(self):
        return self.max_turns

    def get_ttl_seconds(self):
        return self.ttl_seconds

    def get_memory(self):
        return self.memory

    def get_chat_history_length(self):
        return len(self.memory.chat_memory.messages)

    def get_chat_history_as_str(self):
        return (
            "\n".join(
                f"{'User' if isinstance(msg, HumanMessage) else 'Bot'}: {msg.content}"
                for msg in self.memory.chat_memory.messages
            )
            if self.memory.chat_memory.messages
            else "No chat history available."
        )

    def get_chat_history_as_json(self):
        return (
            [
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                }
                for msg in self.memory.chat_memory.messages
            ]
            if self.memory.chat_memory.messages
            else []
        )

    def get_chat_history_as_dict(self):
        return {
            "user_id": self.user_id,
            "max_turns": self.max_turns,
            "ttl_seconds": self.ttl_seconds,
            "backend_type": self.get_backend_type(),
            "chat_history": self.get_chat_history_as_json(),
        }

    def __str__(self):
        return f"MemoryHandler(user_id={self.user_id}, max_turns={self.max_turns}, ttl_seconds={self.ttl_seconds}, backend_type={self.get_backend_type()})"

    def __repr__(self):
        return f"MemoryHandler(user_id={self.user_id}, max_turns={self.max_turns}, ttl_seconds={self.ttl_seconds}, backend_type={self.get_backend_type()})"

    def __len__(self):
        return len(self.memory.chat_memory.messages) if self.memory.chat_memory else 0

    def __getitem__(self, index):
        if (
            not self.memory.chat_memory
            or index < 0
            or index >= len(self.memory.chat_memory.messages)
        ):
            raise IndexError("Index out of range")
        return self.memory.chat_memory.messages[index]

    def __setitem__(self, index, value):
        if (
            not self.memory.chat_memory
            or index < 0
            or index >= len(self.memory.chat_memory.messages)
        ):
            raise IndexError("Index out of range")
        if not isinstance(value, (HumanMessage, AIMessage)):
            raise ValueError("Value must be HumanMessage or AIMessage")
        self.memory.chat_memory.messages[index] = value
        self._trim_memory()
        self._expire_redis_key()

    def __delitem__(self, index):
        if (
            not self.memory.chat_memory
            or index < 0
            or index >= len(self.memory.chat_memory.messages)
        ):
            raise IndexError("Index out of range")
        del self.memory.chat_memory.messages[index]
        self._trim_memory()
        self._expire_redis_key()

    def __contains__(self, item):
        if not self.memory.chat_memory:
            return False
        return any(
            (isinstance(msg, HumanMessage) and msg.content == item)
            or (isinstance(msg, AIMessage) and msg.content == item)
            for msg in self.memory.chat_memory.messages
        )

    def __iter__(self):
        if not self.memory.chat_memory:
            return iter([])
        return iter(self.memory.chat_memory.messages)

    def __next__(self):
        if not self.memory.chat_memory:
            raise StopIteration
        return next(iter(self.memory.chat_memory.messages))

    def __reversed__(self):
        if not self.memory.chat_memory:
            return iter([])
        return reversed(self.memory.chat_memory.messages)

    def __eq__(self, other):
        if not isinstance(other, MemoryHandler):
            return False
        return (
            self.user_id == other.user_id
            and self.max_turns == other.max_turns
            and self.ttl_seconds == other.ttl_seconds
            and self.get_backend_type() == other.get_backend_type()
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(
            (self.user_id, self.max_turns, self.ttl_seconds, self.get_backend_type())
        )

    def __bool__(self):
        return bool(self.memory.chat_memory and self.memory.chat_memory.messages)

    def __len__(self):
        return len(self.memory.chat_memory.messages) if self.memory.chat_memory else 0

    def __call__(self, *args, **kwargs):
        return self.get_memory_json()

    def __del__(self):
        if self.is_redis:
            try:
                r = redis.from_url(self.redis_url)
                r.delete(f"chat:{self.user_id}")
            except Exception as e:
                print(f"[Redis Delete Error] chat:{self.user_id} -> {e}")
        self.memory.chat_memory.clear()
        self.chat_history = None
        self.memory = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()
        return False

    def __getstate__(self):
        state = self.__dict__.copy()
        state["chat_history"] = None
        state["memory"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if self.is_redis:
            self.chat_history = RedisChatMessageHistory(
                session_id=f"chat:{self.user_id}", url=self.redis_url
            )
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                chat_memory=self.chat_history,
            )
        else:
            self.chat_history = None
            self.memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )

    def __copy__(self):
        new_handler = MemoryHandler(self.user_id, self.max_turns, self.ttl_seconds)
        new_handler.memory = self.memory.copy()
        return new_handler
