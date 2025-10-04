# app/chains/followup_chain.py

from langchain.prompts import PromptTemplate
from app.utils.model_loader import load_chat_model
from app.chains.base_chain import build_chain

# Prompt to suggest follow-up questions
followup_prompt = PromptTemplate(
    input_variables=["user_question", "bot_response"],
    template=(
        "Given this Q&A:\n"
        "Q: {user_question}\n"
        "A: {bot_response}\n\n"
        "Suggest 3 short follow-up questions:\n1."
    )
)

def get_followup_chain():
    llm = load_chat_model(model_name="gpt-3.5-turbo", temperature=0.5)
    return build_chain(prompt=followup_prompt, llm=llm)
