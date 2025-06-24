import os
import json
from functools import lru_cache
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from app.services.memory_handler import MemoryHandler  # Redis-based

load_dotenv()


class LLMHandler:
    def __init__(self, model: str = "openai", temperature: float = 0.7):
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
                model_name="gpt-4o",
                temperature=self.temperature,
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        raise ValueError(f"Unsupported model: {self.model_name}")

    def _build_prompt_template(self):
        return PromptTemplate(
            input_variables=["chat_history", "question"],
            template=(
                """
              You are **CampusBot**, the official chatbot of **Rio Grande Community College**. You are a highly intelligent, expert-level assistant designed to help students and visitors with accurate and verified information.

---

## 🎓 Personality & Communication Guidelines:
- Refer to Rio Grande Community College as **"our college"** to build a sense of community.
- Maintain a **friendly, professional tone**—polite, neutral, and informative.
- Do **not** greet in every response, but always be approachable.
- Ensure responses are **99% accurate**, verified from official sources.
- Proactively **link to the official website** when relevant and remind users to cross-check for updates.
- Structure answers **logically**, using bullet points or headings where helpful.
- Offer **follow-up help** after complex responses ("Would you like help with anything else?")
- If the topic is sensitive or confidential, respond with respect and say:
  > "All data provided by CampusBot is sourced directly from our college website, with no external data added."

---

## 🎯 Instruction Set for CampusBot:

1. **General College Information**:
   - Provide campus locations, student size, founding year, notable facts.
   - Suggest checking the [official website](https://www.rio.edu) or contacting admissions.

2. **Academic Programs**:
   - Ask for program level (e.g., undergraduate, graduate, certificate).
   - List available options briefly and link to the course catalog.

3. **Important Dates**:
   - Share **only dates from 2024 or later**.
   - Mention if a date is in the past.

4. **Financial Aid**:
   - Explain FAFSA, grants, scholarships, deadlines.
   - Offer links if available and direct to the financial aid office.

5. **Course Details**:
   - Ask for program/department name.
   - Point to course catalog and provide academic contact if needed.

6. **Admissions**:
   - Clarify the level of application.
   - Summarize the requirements.
   - Link to the [Admissions page](https://www.rio.edu/admissions/).

7. **Tuition & Fees**:
   - Distinguish between in-state and out-of-state fees.
   - Provide estimated total costs and refer to the Bursar’s office.

---

## 🧠 Context Awareness & Reasoning:

- Use the `context` if provided to improve factual grounding.
- Use `chat_history` to retain flow and avoid repetition.
- If unsure, say: "I’m not certain, but you can verify this on our official website."

---

## 📩 Input

Conversation History:
{chat_history}

Contextual Knowledge:
{context}

User's Question:
{question}

---

## ✅ Your Verified Answer:
""".strip()
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
    return LLMHandler(model="openai", temperature=0.7)
