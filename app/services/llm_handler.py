import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI  # ✅ Correct for OpenAI models
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader  # if you need it later

from config import DEFAULT_PDF_PATH, VECTOR_INDEX_PATH
from utils.pdf_loader import process_pdf_and_store

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

    def _load_vectorstore(self):
        if not os.path.exists(VECTOR_INDEX_PATH):
            process_pdf_and_store(DEFAULT_PDF_PATH)

        if os.path.exists(VECTOR_INDEX_PATH):
            return FAISS.load_local(
                VECTOR_INDEX_PATH, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            )
        else:
            return None

    def _build_prompt_template(self):
        return PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are CampusBot, a helpful rio grande university ohio assistant.\n"
                "Answer the user's question based only on the context provided below.\n"
                "If the context does not contain the answer, politely say 'I don't know.'\n\n"
                "Context:\n{context}\n\n"
                "Question:\n{question}\n\n"
                "Helpful Answer:"
            ),
        )

    def get_response(self, message: str) -> str:
        try:
            if self.vectorstore:
                chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=self.vectorstore.as_retriever(),
                    memory=self.memory,
                )
                result = chain.run(message)
                return result.strip() if isinstance(result, str) else str(result)
            else:
                # 🔥 fallback to simple prompt
                prompt = PromptTemplate(
                    input_variables=["question"],
                    template="Answer the question clearly and accurately:\n\n{question}",
                )
                chain = LLMChain(prompt=prompt, llm=self.llm)
                result = chain.run({"question": message})

                # 🔥 Here is the correct safe way
                if isinstance(result, dict):
                    text = result.get("text", "Sorry, no answer.")
                    return text.strip()
                elif isinstance(result, str):
                    return result.strip()
                else:
                    return str(result)
        except Exception as e:
            print("LLMHandler Error:", e)
            return "Sorry, I couldn't process your question at the moment."
