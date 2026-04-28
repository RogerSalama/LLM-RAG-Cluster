import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

class RAGRetriever:
    def __init__(self, data_folder="data/"):
        # Use absolute path to avoid directory-not-found issues
        self.data_folder = os.path.abspath(data_folder)
        
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"[RAG] Created missing directory: {self.data_folder}")

        all_documents = []

        # 1. Load PDFs (Recursive search)
        print("[RAG] Scanning for PDFs...")
        pdf_loader = DirectoryLoader(
            self.data_folder, 
            glob="**/*.pdf", 
            loader_cls=PyPDFLoader
        )
        all_documents.extend(pdf_loader.load())

        # 2. Load Markdown (Recursive search for your SKILLS folder)
        print("[RAG] Scanning for Markdown files...")
        md_loader = DirectoryLoader(
            self.data_folder, 
            glob="**/*.md", 
            loader_cls=UnstructuredMarkdownLoader
        )
        all_documents.extend(md_loader.load())

        if not all_documents:
            print("[ERROR] No PDF or MD files found in the data directory!")
            # Adding a placeholder to prevent FAISS from crashing on an empty list
            from langchain_core.documents import Document
            all_documents = [Document(page_content="The knowledge base is currently empty.")]

        # 3. Split text into chunks
        # Increased overlap slightly so technical terms don't get cut off
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
        self.chunks = text_splitter.split_documents(all_documents)

        # 4. Create Embeddings and Vector Store
        print(f"[RAG] Embedding {len(self.chunks)} chunks into FAISS...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'} # Explicitly force CPU for embeddings
)        
        self.vector_store = FAISS.from_documents(self.chunks, self.embeddings)
        print("[RAG] Index Ready!")

    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        # Similarity search automatically handles the vector math
        docs = self.vector_store.similarity_search(query, k=top_k)
        
        # Clean up the output by joining chunks with spaces
        return " ".join([d.page_content for d in docs])

# Create the global instance
retriever_instance = RAGRetriever()

def retrieve_context(query: str) -> str:
    return retriever_instance.retrieve_context(query)