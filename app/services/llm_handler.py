import os
import json
from functools import lru_cache
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from app.services.memory_handler import MemoryHandler
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()


class LLMHandler:
    def __init__(self, model: str = "openai", temperature: float = 0.2):
        self.model_name = model
        self.temperature = temperature
        self.llm = self._load_model()
        self.qa_prompt = self._build_prompt_template()
        self.user_memories = {}

    def _get_user_memory(self, user_id: str) -> MemoryHandler:
        if user_id not in self.user_memories:
            self.user_memories[user_id] = MemoryHandler(user_id=user_id, max_turns=5)
        return self.user_memories[user_id]

    def _load_model(self):
        if self.model_name == "openai":
            return ChatOpenAI(
                model_name="gpt-4.1-mini-2025-04-14",
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        raise ValueError(f"Unsupported model: {self.model_name}")

    def _build_prompt_template(self):

        return PromptTemplate(
            input_variables=["chat_history", "question"],
            template=(
                """
    Role & Identity:
    You are CampusBot, the official virtual assistant for Rio Grande Community College. Your purpose is to provide accurate information and support about our college.

    Core Objectives:
    - Help current and prospective students with college-related questions
    - Provide verified information about programs, admissions, and campus life
    - Guide users through college processes and requirements

    Guidelines:
    - Keep responses friendly, clear and concise 
    - Only provide verified Rio Grande Community College information
    - Use bullet points and short paragraphs for readability
    - Refer to Rio Grande as "our college"
    - If information is unavailable, direct to rio.edu or suggest follow-up questions
    - Include helpful next steps or CTAs where relevant
    - don't provide information unrealated to Rio Grande Community College and else topics.

    Previous conversation:
    {chat_history}

    Current question:
    {question}

    Response:
    """
            ),
        )

    def get_response(self, user_id: str, message: str) -> str:
        try:
            memory = self._get_user_memory(user_id)
            memory.add_user_message(message)

            history = [
                f"{'User' if msg.type == 'human' else 'Bot'}: {msg.content}"
                for msg in memory.get_messages()
            ]
            history_text = "\n".join(history)

            chain = LLMChain(prompt=self.qa_prompt, llm=self.llm)
            result = chain.invoke({"chat_history": history_text, "question": message})
            answer = result["text"] if isinstance(result, dict) else result

            memory.add_ai_message(answer)
            return answer.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def reset_memory(self, user_id: str):
        memory = self._get_user_memory(user_id)
        memory.clear()
        self.qa_prompt = self._build_prompt_template()

    def get_chat_history(self, user_id: str) -> str:
        memory = self._get_user_memory(user_id)
        return "\n".join(
            [
                f"{'User' if msg.type == 'human' else 'Bot'}: {msg.content}"
                for msg in memory.get_messages()
            ]
        )

    def get_memory_json(self, user_id: str) -> str:
        memory = self._get_user_memory(user_id)
        return json.dumps(
            [
                {"type": msg.type, "content": msg.content}
                for msg in memory.get_messages()
            ],
            indent=2,
        )

    def suggest_followups(self, user_input: str, bot_answer: str) -> list[str]:
        prompt_template = PromptTemplate(
            input_variables=["user_question", "bot_response"],
            template=(
                "Given this Q&A:\n"
                "Q: {user_question}\n"
                "A: {bot_response}\n\n"
                "Suggest 3 short follow-up questions:\n1."
            ),
        )

        chain = LLMChain(prompt=prompt_template, llm=self.llm)
        result = chain.invoke({"user_question": user_input, "bot_response": bot_answer})

        raw = result.get("text", "") if isinstance(result, dict) else str(result)
        lines = raw.strip().split("\n")

        followups = []
        for line in lines:
            line = line.strip()
            if line and any(c.isalpha() for c in line):
                question = line.lstrip("1234567890.:- ").strip()
                followups.append(question)

        return followups[:3]


@lru_cache(maxsize=1)
def get_llm_handler() -> LLMHandler:
    return LLMHandler(model="openai", temperature=0.3)
