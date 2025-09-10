import os
import json
from functools import lru_cache
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas import ResponseFormatter

load_dotenv()
set_llm_cache(InMemoryCache())


class LLMHandler:
    def __init__(self, model: str = "openai", temperature: float = 0.2):
        self.model_name = model
        self.temperature = temperature
        self.llm = self._load_model()
        self.llm_with_tools = self._load_model_with_tools()
        self._followup_cache = {}

    def _load_model(self):
        """Load structured output model for regular responses"""
        if self.model_name == "openai":
            base = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=512,
                request_timeout=30,
            )
            return base.with_structured_output(ResponseFormatter)
        raise ValueError(f"Unsupported model: {self.model_name}")

    def _load_model_with_tools(self):
        """Load model with web search tools"""
        if self.model_name == "openai":
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=256,
                request_timeout=20,
            )
            tool = {"type": "web_search_preview"}
            return llm.bind_tools([tool])
        return None

    def get_response(
        self, memory_handler, message: str, use_web_search: bool = False
    ) -> dict:
        """Returns structured response with answer and followup."""
        try:
            # Add user message to memory
            memory_handler.add_message(HumanMessage(content=message))
            history = memory_handler.get_recent_messages(limit=10)

            if self.model_name == "openai":
                if use_web_search and self.llm_with_tools:
                    # Web search response
                    search_response = self.llm_with_tools.invoke(history)
                    answer_text = search_response.content or "Web search completed"
                    followup_text = (
                        "Would you like me to search for more specific information?"
                    )
                else:
                    # Structured output response
                    structured_response = self.llm.invoke(history)
                    answer_text = structured_response.answer
                    followup_text = structured_response.followup_question

                # Store AI response in memory
                memory_handler.add_message(AIMessage(content=answer_text))

                # Generate follow-up questions (moved to separate method)
                ai_followups = self._get_cached_followups(message, answer_text)

                return {
                    "answer": answer_text,
                    "followup_question": followup_text,
                    "ai_followups": ai_followups,
                    "success": True,
                    "used_web_search": use_web_search,
                }

        except Exception as e:
            return {
                "answer": f"Error generating response: {str(e)}",
                "followup_question": None,
                "ai_followups": [],
                "success": False,
                "used_web_search": False,
            }

    def generate_followups(self, user_input: str, bot_answer: str) -> list[str]:
        """Generate follow-up questions using external prompt"""
        try:
            # Import here to avoid circular imports
            from app.services.prompt_template import PromptTemplateService

            base_model = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                max_tokens=150,
                request_timeout=15,
            )

            # Use prompt from PromptTemplateService
            followup_prompt = PromptTemplateService.get_followup_prompt()
            chain = LLMChain(prompt=followup_prompt, llm=base_model)

            result = chain.invoke(
                {"question": user_input[:200], "answer": bot_answer[:300]}
            )

            raw = result.get("text", "") if isinstance(result, dict) else str(result)
            lines = raw.strip().split("\n")

            followups = []
            for line in lines:
                line = line.strip()
                if line and any(c.isalpha() for c in line):
                    question = line.lstrip("1234567890.:- ").strip()
                    if question and len(question) > 5:
                        followups.append(question)

            return followups[:3]

        except Exception:
            return [
                "Can you tell me more about this?",
                "What are the main benefits?",
                "Are there any alternatives?",
            ]

    def _get_cached_followups(self, user_input: str, bot_answer: str) -> list[str]:
        """Get cached follow-up questions or generate new ones"""
        cache_key = f"{hash(user_input)}_{hash(bot_answer[:100])}"

        if cache_key in self._followup_cache:
            return self._followup_cache[cache_key]

        followups = self.generate_followups(user_input, bot_answer)
        self._followup_cache[cache_key] = followups

        # Keep cache manageable
        if len(self._followup_cache) > 100:
            self._followup_cache.clear()

        return followups


@lru_cache(maxsize=1)
def get_llm_handler() -> LLMHandler:
    return LLMHandler(model="openai", temperature=0.3)
