import os
from dotenv import load_dotenv
from urllib.parse import urlparse

from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache

from app.services.prompt_template import PromptTemplateService

load_dotenv()

# Enable caching for better performance
set_llm_cache(InMemoryCache())


class MemoryHandler:
    def __init__(self, user_id: str, max_turns: int = 5, ttl_seconds: int = 3600):
        self.user_id = user_id
        self.max_turns = max_turns
        self.ttl_seconds = ttl_seconds

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError(" REDIS_URL not set in environment.")

        parsed_url = urlparse(redis_url)
        if parsed_url.scheme not in ["redis", "rediss"]:
            raise ValueError("Invalid REDIS_URL scheme.")

        self.qa_prompt = PromptTemplateService.get_qa_prompt()

        # Initialize Redis chat history
        self.chat_history = RedisChatMessageHistory(
            session_id=f"chat:{self.user_id}", url=redis_url, ttl=self.ttl_seconds
        )

        # Modern ConversationBufferWindowMemory with Redis backend
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=self.chat_history,
            k=self.max_turns,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content="You are CampusBot, a specialized AI assistant for New Mexico colleges and career guidance."
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{text}"),
            ]
        )

        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=512,
            request_timeout=30,
        )

        # Legacy chain uses your detailed prompt
        self.legacy_chain = LLMChain(
            llm=self.llm,
            prompt=self.qa_prompt,
            memory=self.memory,
        )

        # Modern LCEL chain uses simpler ChatPromptTemplate
        self.modern_chain = self._setup_modern_chain()

    def _setup_modern_chain(self):
        """Setup modern LCEL chain with message history"""
        # Create the basic chain
        chain = self.prompt | self.llm

        # Return chain with message history
        return RunnableWithMessageHistory(
            chain,
            self._get_session_history,
            input_messages_key="text",
            history_messages_key="chat_history",
        )

    def _get_session_history(self, session_id: str):
        """Get session history for RunnableWithMessageHistory"""
        return self.chat_history

    # Message management methods
    def add_message(self, message):
        """Add a LangChain message object (HumanMessage or AIMessage)"""
        if isinstance(message, HumanMessage):
            self.chat_history.add_user_message(message.content)
        elif isinstance(message, AIMessage):
            self.chat_history.add_ai_message(message.content)
        else:
            self.chat_history.add_message(message)

    def add_user_message(self, message: str):
        """Add user message as string"""
        self.chat_history.add_user_message(message)

    def add_ai_message(self, message: str):
        """Add AI message as string"""
        self.chat_history.add_ai_message(message)

    def get_messages(self) -> list:
        """Get messages from Redis"""
        return self.chat_history.messages

    def get_recent_messages(self, limit: int = None) -> list:
        """Get recent messages with optional limit"""
        messages = self.chat_history.messages
        if limit:
            return messages[-limit:]
        return (
            messages[-self.max_turns * 2 :]
            if len(messages) > self.max_turns * 2
            else messages
        )

    # Chain execution methods
    def run_legacy_conversation(self, user_input: str) -> str:
        """Run conversation using legacy LLMChain"""
        try:
            response = self.legacy_chain.invoke({"text": user_input})
            return response["text"]
        except Exception as e:
            return f"Error in legacy chain: {str(e)}"

    def run_modern_conversation(self, user_input: str) -> str:
        """Run conversation using modern LCEL chain"""
        try:
            response = self.modern_chain.invoke(
                {"text": user_input},
                config={"configurable": {"session_id": self.user_id}},
            )
            return response.content
        except Exception as e:
            return f"Error in modern chain: {str(e)}"

    # Memory management methods
    def get_memory_variables(self) -> dict:
        """Get memory variables for the conversation"""
        return self.memory.load_memory_variables({})

    def clear(self):
        """Clear all messages"""
        if hasattr(self.chat_history, "clear"):
            self.chat_history.clear()
        self.memory.clear()

    # Utility methods
    def get_conversation_summary(self) -> str:
        """Get a formatted summary of the conversation"""
        messages = self.get_messages()
        if not messages:
            return "No conversation history."

        summary = []
        for i, msg in enumerate(messages):
            if hasattr(msg, "type"):
                role = (
                    "User"
                    if msg.type == "human"
                    else "Assistant" if msg.type == "ai" else "System"
                )
            else:
                role = "Unknown"
            summary.append(f"{i+1}. {role}: {msg.content[:100]}...")

        return "\n".join(summary)

    def get_conversation_stats(self) -> dict:
        """Get conversation statistics"""
        messages = self.get_messages()
        user_count = sum(
            1 for msg in messages if hasattr(msg, "type") and msg.type == "human"
        )
        ai_count = sum(
            1 for msg in messages if hasattr(msg, "type") and msg.type == "ai"
        )

        return {
            "total_messages": len(messages),
            "user_messages": user_count,
            "ai_messages": ai_count,
            "conversation_pairs": min(user_count, ai_count),
        }
