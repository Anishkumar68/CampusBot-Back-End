from langchain.llms import OpenAI, HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv

from app.config import DEFAULT_PDF_PATH, VECTOR_INDEX_PATH
from app.utils.pdf_loader import process_pdf_and_store

load_dotenv()


class LLMHandler:
    def __init__(self, model: str = "openai", temperature: float = 0.7):
        self.model_name = model
        self.temperature = temperature
        self.llm = self._load_model()
        self.vectorstore = self._load_vectorstore()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

    def _load_model(self):
        if self.model_name == "openai":
            return OpenAI(
                temperature=self.temperature, openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        elif self.model_name == "huggingface":
            return HuggingFaceHub(
                repo_id="google/flan-t5-xl",
                model_kwargs={"temperature": self.temperature},
                huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            )
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

    def _load_vectorstore(self):
        index_path = "vector_index"

        # If no vector index exists, create it from default.pdf
        if not os.path.exists(VECTOR_INDEX_PATH):
            process_pdf_and_store(DEFAULT_PDF_PATH)
            return FAISS.load_local(
                VECTOR_INDEX_PATH, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            )
        # If user-specific or uploaded file, load the vectorstore from the specified path
        else:
            # If user-specific or uploaded file, load the vectorstore from the specified path
            if os.path.exists(index_path):
                return FAISS.load_local(
                    index_path, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
                )
            else:
                return None

    #        # If no vectorstore is found, return None
    #        else:
    #            return None

    # If user-specific or uploaded file, load the vectorstore from the specified path
    # else:
    #     return None
    def get_response(self, message: str) -> str:
        if self.vectorstore:
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(),
                memory=self.memory,
            )
            result = chain.run(message)
            return result
        else:
            prompt = PromptTemplate(
                input_variables=["question"],
                template="Answer the question clearly:\n\n{question}",
            )
            chain = LLMChain(prompt=prompt, llm=self.llm)
            return chain.run(message)
