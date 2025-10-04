# app/utils/model_loader.py

import os
from typing import Literal, Optional, Callable

from langchain.chat_models import (
    ChatOpenAI,
    ChatAnthropic,
    ChatHuggingFace,
)
from langchain.embeddings import (
    OpenAIEmbeddings,
    HuggingFaceEmbeddings,
)

# Web search tool / Brave Search
from langchain_community.tools import BraveSearch


def load_chat_model(
    provider: Literal["openai", "anthropic", "huggingface"] = "openai",
    model_name: Optional[str] = None,
    temperature: float = 0.2,
):
    """
    Load a chat model from the supported providers.
    """
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(
            model_name=model_name or "gpt-3.5-turbo",
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=model_name or "claude-v1",
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif provider == "huggingface":
        return ChatHuggingFace(
            repo_id=model_name or "mistralai/Mistral-7B-Instruct-v0.2",
            temperature=temperature,
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
        )
    else:
        raise ValueError(f"Unsupported chat provider: {provider}")


def load_embedding_model(
    provider: Literal["openai", "huggingface"] = "openai",
    model_name: Optional[str] = None,
):
    """
    Load embedding model (for texts, web content, etc.)
    """
    provider = provider.lower()
    if provider == "openai":
        return OpenAIEmbeddings(
            model=model_name or "text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
    elif provider == "huggingface":
        return HuggingFaceEmbeddings(
            model_name=model_name or "sentence-transformers/all-MiniLM-L6-v2"
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")


def load_web_search_tool(
    provider: Literal["brave"] = "brave",
    api_key: Optional[str] = None,
    **search_kwargs,
) -> Callable[[str], str]:
    """
    Load a web search tool (e.g. Brave Search) as a callable function to be exposed as a tool.

    provider: supports "brave" currently; you can add more later
    api_key: API key for the provider
    search_kwargs: additional parameters (e.g. count, etc.)

    Returns a function that accepts a query string and returns search results.
    """
    provider = provider.lower()
    if provider == "brave":
        key = api_key or os.getenv("BRAVE_SEARCH_API_KEY")
        # BraveSearch is part of langchain_community tools integration.
        tool = BraveSearch.from_api_key(api_key=key, search_kwargs=search_kwargs)
        # `tool.run` is the callable that accepts a query
        return tool.run
    else:
        raise ValueError(f"Unsupported web search provider: {provider}")
