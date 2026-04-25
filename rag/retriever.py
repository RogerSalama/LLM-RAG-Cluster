# rag/retriever.py
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os

class RAGRetriever:
    def __init__(self, data_folder="data/"):
        self.data_folder = data_folder
        
        # 1. Load all PDFs from the directory automatically
        print("[RAG] Loading Documents...")
        loader = DirectoryLoader(self.data_folder, glob="./*.pdf", loader_cls=PyPDFLoader)
        raw_documents = loader.load()

        # 2. Split text into 500-character chunks
        # RecursiveCharacterTextSplitter is "smarter" than manual slicing 
        # because it tries to split at paragraphs and sentences first.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        self.chunks = text_splitter.split_documents(raw_documents)

        # 3. Create Embeddings and Vector Store (The Map)
        print(f"[RAG] Embedding {len(self.chunks)} chunks into FAISS...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # This one line creates the index and adds the vectors
        self.vector_store = FAISS.from_documents(self.chunks, self.embeddings)
        print("[RAG] Index Ready!")

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        # Search the vector store
        docs = self.vector_store.similarity_search(query, k=top_k)
        
        # Join the text from the retrieved document objects
        return " ".join([d.page_content for d in docs])

# Global instance
retriever_instance = RAGRetriever()

def retrieve_context(query: str) -> str:
    return retriever_instance.retrieve_context(query)