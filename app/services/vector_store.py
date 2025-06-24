import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from app.config import DEFAULT_PDF_PATH, USER_UPLOAD_PDF_PATH, VECTOR_INDEX_PATH


class VectorStoreManager:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.index_path = VECTOR_INDEX_PATH
        self.vectorstore = None

    def load_or_create(self):
        """Load FAISS index or create from default.pdf"""
        index_file = os.path.join(self.index_path, "index.faiss")
        if os.path.exists(index_file):
            print("✅ Loading existing FAISS index...")
            self.vectorstore = FAISS.load_local(
                folder_path=self.index_path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True,  # ✅ Added this flag
            )
        else:
            print("⚠️ FAISS index not found. Creating new from default.pdf...")
            self.reset_to_default()

    def reset_to_default(self):
        """Rebuild vectorstore from default.pdf"""
        print(f"📄 Processing {DEFAULT_PDF_PATH}...")
        loader = PyPDFLoader(DEFAULT_PDF_PATH)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(documents)

        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        self.vectorstore.save_local(self.index_path)
        print("✅ Default vectorstore created and saved.")

    def process_uploaded_pdf(self):
        """Rebuild vectorstore from uploaded user PDF"""
        if not os.path.exists(USER_UPLOAD_PDF_PATH):
            raise FileNotFoundError("❌ Uploaded PDF not found.")

        print(f"📄 Processing uploaded file: {USER_UPLOAD_PDF_PATH}...")
        loader = PyPDFLoader(USER_UPLOAD_PDF_PATH)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.split_documents(documents)

        self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        self.vectorstore.save_local(self.index_path)
        print("✅ User PDF vectorstore created and saved.")

    def get_vectorstore(self):
        """Return loaded FAISS vectorstore"""
        if self.vectorstore is None:
            self.load_or_create()
        return self.vectorstore
