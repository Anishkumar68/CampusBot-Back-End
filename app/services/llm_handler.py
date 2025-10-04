# app/services/llm_handler.py

import os
import json
from functools import lru_cache
from dotenv import load_dotenv

# Import chains & tools/modules you created
from app.chains.qa_chain import get_qa_chain
from app.chains.followup_chain import get_followup_chain
from app.chains.rag_pipeline import RAGPipeline  # if you created this
from app.utils.model_loader import load_web_search_tool
from app.services.memory_handler import MemoryHandler

load_dotenv()

class LLMHandler:
    def __init__(
        self,
        model_provider: str = "openai",
        temperature: float = 0.2,
        urls_for_rag: list[str] | None = None,
        enable_web_search: bool = False,
    ):
        """
        :param model_provider: e.g. "openai", "anthropic", "huggingface", "gemini"
        :param temperature: temperature for the LLM
        :param urls_for_rag: list of website URLs to index for RAG
        :param enable_web_search: whether to enable web search fallback
        """
        self.model_provider = model_provider
        self.temperature = temperature

        # Instantiate chains
        self.qa_chain = get_qa_chain(provider=model_provider, temperature=temperature)
        self.followup_chain = get_followup_chain(provider=model_provider, temperature=temperature)

        # Optional: RAG setup
        if urls_for_rag:
            self.rag_pipeline = RAGPipeline(
                urls=urls_for_rag,
                embedding_provider=model_provider,
                chat_provider=model_provider,
                embed_model_name=None,
                chat_model_name=None,
            )
        else:
            self.rag_pipeline = None

        # Optional: web search fallback
        if enable_web_search:
            # returns a callable, e.g. web_search(query) -> result
            self.web_search = load_web_search_tool(provider="brave", search_kwargs={"count": 3})
        else:
            self.web_search = None

        self.user_memories: dict[str, MemoryHandler] = {}

    def _get_user_memory(self, user_id: str) -> MemoryHandler:
        if user_id not in self.user_memories:
            self.user_memories[user_id] = MemoryHandler(user_id=user_id, max_turns=5)
        return self.user_memories[user_id]

    def get_response(self, user_id: str, user_input: str) -> str:
        """
        Main entry point for getting a response from the chatbot,
        with memory, RAG, fallback, and follow-up chain.
        """
        memory = self._get_user_memory(user_id)
        memory.add_user_message(user_input)

        # Build chat history text
        history = [
            f"{'User' if msg.type == 'human' else 'Bot'}: {msg.content}"
            for msg in memory.get_messages()
        ]
        history_text = "\n".join(history)

        # 1. Try RAG (if available)
        if self.rag_pipeline:
            try:
                answer = self.rag_pipeline.answer(user_input)
            except Exception as rag_err:
                # fallback to QA chain if RAG fails
                answer = None
        else:
            answer = None

        # 2. If RAG gave no good answer, fallback to plain QA chain
        if not answer or self._is_low_confidence(answer):
            # Use QA chain
            result = self.qa_chain.invoke({"chat_history": history_text, "question": user_input})
            answer = result.get("text") if isinstance(result, dict) else str(result)

        # 3. If still no answer and web search is enabled, try web search
        if (not answer or answer.strip() == "") and self.web_search:
            try:
                search_res = self.web_search(user_input)
                # Optionally feed this into the model to produce a better answer
                # e.g., re-prompt model: “Based on these search results, answer this: …”
                answer = f"I found the following from web search:\n{search_res}"
            except Exception as ws_err:
                # ignore web search errors
                pass

        memory.add_ai_message(answer)
        return answer.strip()

    def suggest_followups(self, user_input: str, bot_answer: str) -> list[str]:
        """
        Use follow‑up chain to generate 3 short follow-up questions.
        """
        result = self.followup_chain.invoke({
            "user_question": user_input,
            "bot_response": bot_answer
        })
        raw = result.get("text", "") if isinstance(result, dict) else str(result)
        lines = raw.strip().split("\n")

        followups = []
        for line in lines:
            line = line.strip()
            if line and any(c.isalpha() for c in line):
                question = line.lstrip("1234567890.:- ").strip()
                followups.append(question)
        return followups[:3]

    def reset_memory(self, user_id: str):
        memory = self._get_user_memory(user_id)
        memory.clear()

    def get_chat_history(self, user_id: str) -> str:
        memory = self._get_user_memory(user_id)
        return "\n".join(
            f"{'User' if msg.type == 'human' else 'Bot'}: {msg.content}"
            for msg in memory.get_messages()
        )

    def get_memory_json(self, user_id: str) -> str:
        memory = self._get_user_memory(user_id)
        return json.dumps(
            [{"type": msg.type, "content": msg.content} for msg in memory.get_messages()],
            indent=2
        )

    def _is_low_confidence(self, answer: str) -> bool:
        """
        Heuristic: decide if an answer is not confident / not good enough,
        so fallback to another strategy. You can customize.
        """
        if not answer:
            return True
        # Simple heuristic (you can build better logic):
        # e.g., “I’m sorry”, “I don’t know”, or very short answer
        low_phrases = ["i'm not sure", "i don't know", "i am not sure"]
        lower = answer.lower()
        if any(phrase in lower for phrase in low_phrases):
            return True
        if len(answer) < 20:
            return True
        return False


@lru_cache(maxsize=1)
def get_llm_handler(**kwargs) -> LLMHandler:
    """
    Cached singleton factory. Pass same arguments to get consistent instance.
    """
    return LLMHandler(**kwargs)
