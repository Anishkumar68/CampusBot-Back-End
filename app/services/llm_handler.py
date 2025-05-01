import os
from functools import lru_cache
from dotenv import load_dotenv

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
                "You are CampusBot, a helpful Rio Grande University Ohio assistant.\n"
                "Use the following chat history to inform your response.\n\n"
                "{chat_history}\n\n"
                "User Question: {question}\n\n"
                "Answer:"
            ),
        )

    def get_response(self, message: str) -> str:
        """Pure-LLM response using memory to track chat history."""
        try:
            # 1. Add user message to memory
            self.memory.chat_memory.add_user_message(message)

            # 2. Format chat history into a single string7

            history = []
            for msg in self.memory.chat_memory.messages:
                role = "User" if msg.type == "human" else "Bot"
                history.append(f"{role}: {msg.content}")
            history_text = "\n".join(history)

            # 3. Invoke the LLMChain with history and current question
            chain = LLMChain(prompt=self.qa_prompt, llm=self.llm)
            result = chain.invoke(
                {
                    "chat_history": history_text,
                    "question": message,
                }
            )
            answer = result["text"] if isinstance(result, dict) else result

            # 4. Add bot response to memory
            self.memory.chat_memory.add_ai_message(answer)

            return answer.strip()

        except Exception as e:
            print("LLMHandler Error:", e)
            return "Sorry, I couldn't process your question at the moment."

    def suggest_followups(self, user_input: str, bot_answer: str) -> list[str]:
        prompt = f"""
        Suggest 2 useful follow-up questions for the user based on this conversation.

        User: {user_input}
        Bot: {bot_answer}

        Respond ONLY with a list in JSON format like:
        ["Follow-up 1?", "Follow-up 2?"]
        """
        try:
            result = self.llm.invoke(prompt)
            return eval(result) if result.strip().startswith("[") else []
        except:
            return []


@lru_cache(maxsize=1)
def get_llm_handler() -> LLMHandler:
    """
    Returns a singleton LLMHandler (with retained memory), so that chat history persists across calls.
    """
    return LLMHandler(model="openai", temperature=0.7)
