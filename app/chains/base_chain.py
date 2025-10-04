from langchain_core.output_parsers.base import BaseOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

def build_chain(
    prompt: PromptTemplate,
    llm: BaseChatModel,
    parser: BaseOutputParser = None
) -> Runnable:
    """
    Build a LangChain Runnable sequence:
    PromptTemplate -> LLM -> (optional) OutputParser

    :param prompt: The prompt template to format input
    :param llm: The LLM to invoke
    :param parser: Optional output parser to structure the response
    :return: A Runnable chain
    """
    chain = prompt | llm
    if parser:
        chain = chain | parser
    return chain
