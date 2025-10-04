from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.utils.model_loader import load_embedding_model, load_chat_model
from app.utils.document_indexer import _load_source


class RAGPipeline:
    def __init__(
        self,
        urls: list[str],
        embedding_provider: str = "openai",
        chat_provider: str = "openai",
        embed_model_name: str = None,
        chat_model_name: str = None,
    ):
        # Load embedding & chat models
        self.embedder = load_embedding_model(
            provider=embedding_provider, model_name=embed_model_name
        )
        self.chat_model = load_chat_model(
            provider=chat_provider, model_name=chat_model_name
        )

        # Load documents from URLs (your website pages)
        docs = []
        for url in urls:
            docs.extend(_load_source(url))

        # Optionally chunk / split docs for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=100
        )
        splits = text_splitter.split_documents(docs)

        # Create vector store + retriever
        self.vectorstore = FAISS.from_documents(splits, embedding=self.embedder)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        # Create the retrieval‑aware QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.chat_model,
            retriever=self.retriever,
            chain_type="stuff",  # or "map_reduce", etc.
        )

    def answer(self, query: str) -> str:
        result = self.qa_chain.invoke({"query": query})
        # sometimes invoke returns dict, sometimes direct str
        if isinstance(result, dict):
            return result.get("result") or result.get("text") or ""
        return str(result)
