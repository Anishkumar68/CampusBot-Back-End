import os
import logging
from typing import List, Union

from langchain.document_loaders import PyPDFLoader, JSONLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

from app.config import (
    DEFAULT_PDF_PATH,
    USER_UPLOAD_PDF_PATH,
    VECTOR_INDEX_PATH,
    HELPING_DATA_JSON,
    URLS_LIST_FILE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _load_source(source: Union[str, dict]) -> List[Document]:
    """
    Load documents from one source (PDF path, JSON path, URL, or JSON dict).
    Returns list of Document objects.
    Attaches metadata field `"source": source_identifier` to each Document.
    """
    docs: List[Document] = []
    src = source

    try:
        # PDF file path
        if isinstance(src, str) and src.lower().endswith(".pdf"):
            loader = PyPDFLoader(src)
            loaded = loader.load()
            for d in loaded:
                d.metadata = d.metadata or {}
                d.metadata["source"] = src
            docs.extend(loaded)

        # JSON file path
        elif isinstance(src, str) and src.lower().endswith(".json"):
            loader = JSONLoader(src)
            loaded = loader.load()
            for d in loaded:
                d.metadata = d.metadata or {}
                d.metadata["source"] = src
            docs.extend(loaded)

        # In‑memory JSON dict
        elif isinstance(src, dict):
            loader = JSONLoader(json_string=src)
            loaded = loader.load()
            for d in loaded:
                d.metadata = d.metadata or {}
                d.metadata["source"] = "in_memory_json"
            docs.extend(loaded)

        # URL (http / https)
        elif isinstance(src, str) and src.lower().startswith(("http://www.sfcc.edu", "https://www.rio.edu/")):
            loader = WebBaseLoader(src)
            loaded = loader.load()
            for d in loaded:
                d.metadata = d.metadata or {}
                d.metadata["source"] = src
            docs.extend(loaded)

        else:
            logger.warning(f"Skipping unsupported source type: {src}")
    except Exception as e:
        logger.error(f"Error loading source {src}: {e}")

    return docs

def process_and_index(
    sources: List[Union[str, dict]],
    persist_path: str = None,
) -> str:
    """
    Process and index multiple sources into a FAISS vector store.
    :param sources: list of sources (PDF paths, JSON paths, URLs, or JSON dicts)
    :param persist_path: where to save the vector store (directory). Default = VECTOR_INDEX_PATH
    :return: status message
    """
    if persist_path:
        index_dir = persist_path
    else:
        index_dir = str(VECTOR_INDEX_PATH)

    os.makedirs(index_dir, exist_ok=True)

    all_docs = []
    for src in sources:
        docs = _load_source(src)
        if docs:
            logger.info(f"Loaded {len(docs)} documents from source: {src}")
            all_docs.extend(docs)

    if not all_docs:
        return "No documents loaded; index not created."

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(all_docs)
    logger.info(f"Split documents into {len(chunks)} chunks.")

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    try:
        vectorstore.save_local(index_dir)
        logger.info(f"Vector store saved to {index_dir}.")
    except Exception as e:
        logger.error(f"Failed to save vector store: {e}")
        return f"Index built but failed to save: {e}"

    return f"Indexed {len(chunks)} chunks from {len(sources)} sources into {index_dir}."

def index_default_sources():
    """
    Convenience function to index your standard sources:
    default PDF, user‑uploaded PDF (if exists), helping_data JSON, and URLs list.
    """
    sources: List[Union[str, dict]] = []

    if DEFAULT_PDF_PATH and os.path.exists(DEFAULT_PDF_PATH):
        sources.append(str(DEFAULT_PDF_PATH))

    if USER_UPLOAD_PDF_PATH and os.path.exists(USER_UPLOAD_PDF_PATH):
        sources.append(str(USER_UPLOAD_PDF_PATH))

    if HELPING_DATA_JSON and os.path.exists(HELPING_DATA_JSON):
        sources.append(str(HELPING_DATA_JSON))

    if URLS_LIST_FILE and os.path.exists(URLS_LIST_FILE):
        try:
            with open(URLS_LIST_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        sources.append(line)
        except Exception as e:
            logger.error(f"Error reading URL list file: {e}")

    return process_and_index(sources=sources, persist_path=str(VECTOR_INDEX_PATH))
