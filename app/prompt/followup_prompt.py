# app/prompts/followup_prompt.py

from langchain.prompts import PromptTemplate

followup_prompt = PromptTemplate(
    input_variables=["user_question", "bot_response"],
    template=(
        "You are an educational chatbot assisting students with follow-up questions.\n"
        "Based on the following exchange:\n\n"
        "User Question: {user_question}\n"
        "Bot Answer: {bot_response}\n\n"
        "Suggest 3 short, helpful follow-up questions they might ask next.\n"
        "1."
    ),
)
