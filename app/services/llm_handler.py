import os
from functools import lru_cache
from dotenv import load_dotenv
import json

from langchain_openai import ChatOpenAI  # ✅ Correct for OpenAI models
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

load_dotenv()


class LLMHandler:
    def __init__(self, model: str = "openai", temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.llm = self._load_model()
        # Initialize memory to store chat history across turns
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        # Build a prompt template that uses chat history
        self.qa_prompt = self._build_prompt_template()

    def _load_model(self):
        if self.model_name == "openai":
            return ChatOpenAI(
                model_name="gpt-4o",
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

    def _build_prompt_template(self):
        return PromptTemplate(
            input_variables=["chat_history", "question"],
            template=(
                "You are CampusBot, a helpful assistant for Rio Grande University, Ohio.\n"
                "You always provide concise, accurate, and helpful answers for students and visitors.\n"
                "Always include official and relevant links when available.\n"
                "Never guess or provide false information — if unsure, say so and guide where to look.\n"
                "You do not provide offensive, political, religious, or fabricated content.\n"
                "Use the full conversation context from {chat_history} to understand and reply clearly.\n"
                "Interpret follow-up questions using previous questions and answers.\n"
                "Current Question: {question}\n\n"
                "Answer:"
            ),
        )

    def get_response(self, message: str) -> str:
        """Pure-LLM response using memory to track last 10 messages only."""
        try:
            # 1. Add user message to memory
            self.memory.chat_memory.add_user_message(message)

            # 2. Trim memory to last 10 messages
            max_messages = 10  # 5 exchanges (user + bot)
            if len(self.memory.chat_memory.messages) > max_messages:
                self.memory.chat_memory.messages = self.memory.chat_memory.messages[
                    -max_messages:
                ]

            # 3. Format chat history
            history = []
            for msg in self.memory.chat_memory.messages:
                role = "User" if msg.type == "human" else "Bot"
                history.append(f"{role}: {msg.content}")
            history_text = "\n".join(history)

            # 4. Get response
            chain = LLMChain(prompt=self.qa_prompt, llm=self.llm)
            result = chain.invoke(
                {
                    "chat_history": history_text,
                    "question": message,
                }
            )
            answer = result["text"] if isinstance(result, dict) else result

            # 5. Add bot response to memory
            self.memory.chat_memory.add_ai_message(answer)

            return answer.strip()
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def reset_memory(self):
        """Reset the conversation memory."""
        self.memory.chat_memory.clear()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        self.qa_prompt = self._build_prompt_template()
        """        Reset the conversation memory and prompt template.
        This is useful for starting a new conversation without previous context."""

    def get_chat_history(self) -> str:
        """Get the current chat history as a formatted string."""
        history = []
        for msg in self.memory.chat_memory.messages:
            role = "User" if msg.type == "human" else "Bot"
            history.append(f"{role}: {msg.content}")
        return "\n".join(history)

    def get_memory(self) -> str:
        """Get the current memory as a JSON string."""
        memory_data = {
            "chat_history": self.memory.chat_memory.messages,
            "prompt_template": self.qa_prompt.template,
        }
        return json.dumps(memory_data, indent=2)

    def load_memory(self, memory_json: str):
        """Load memory from a JSON string."""
        try:
            memory_data = json.loads(memory_json)
            self.memory.chat_memory.messages = memory_data.get("chat_history", [])
            self.qa_prompt.template = memory_data.get(
                "prompt_template", self.qa_prompt.template
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid memory JSON format: {str(e)}")

    # suggested questions
    def suggest_followups(self, user_input: str, bot_answer: str) -> list[str]:
        """
        Suggest 3 follow-up questions based on the user's input and the bot's answer.
        Output is clean strings to be shown as clickable buttons in the frontend.
        """
        prompt_template = PromptTemplate(
            input_variables=["user_question", "bot_response"],
            template=(
                "You are a helpful assistant.\n"
                "Given the user's question and the bot's answer, suggest 3 short follow-up questions a user might ask next.\n\n"
                "User Question: {user_question}\n"
                "Bot Answer: {bot_response}\n\n"
                "Related Questions:\n"
                "1."
            ),
        )

        question_chain = LLMChain(
            prompt=prompt_template,
            llm=self.llm,
        )

        result = question_chain.invoke(
            {"user_question": user_input, "bot_response": bot_answer}
        )

        raw_text = result.get("text", "") if isinstance(result, dict) else str(result)
        lines = raw_text.strip().split("\n")

        # Normalize and clean each question
        followup_questions = []
        for line in lines:
            line = line.strip()
            if line and any(char.isalpha() for char in line):
                question = line.lstrip("1234567890.:- ").strip()
                followup_questions.append(question)

        return followup_questions[:3]


@lru_cache(maxsize=1)
def get_llm_handler() -> LLMHandler:
    """
    Returns a singleton LLMHandler (with retained memory), so that chat history persists across calls.
    """
    return LLMHandler(model="openai", temperature=0.7)
