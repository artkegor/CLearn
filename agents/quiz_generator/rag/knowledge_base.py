import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter


class KnowledgeBase:
    """Knowledge base using FAISS vector store and HuggingFace embeddings"""

    def __init__(self, knowledge_dir: str = None, index_dir: str = "agents/quiz_generator/faiss_index"):
        """
        knowledge_dir: Directory containing .txt files for the knowledge base
        index_dir: Directory to store/load the FAISS index
        """
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
        self.retriever = None
        self.index_dir = index_dir

        # If no knowledge_dir provided, use default path
        if knowledge_dir:
            self.knowledge_dir = knowledge_dir
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.knowledge_dir = os.path.join(script_dir, "..", "knowledge")
            self.knowledge_dir = os.path.abspath(self.knowledge_dir)

        self.load_or_create_base()

    def load_or_create_base(self):
        """Load existing FAISS index or create a new one"""
        try:
            self.vectorstore = FAISS.load_local(
                self.index_dir,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            print(f"✅ FAISS загружен из {self.index_dir}")
        except Exception as e:
            print(f"⚠️ FAISS не найден ({e}), создаём новый индекс...")
            self.create_knowledge_base()

    def create_knowledge_base(self):
        """Initialize knowledge base from .txt files"""
        if not os.path.exists(self.knowledge_dir):
            raise FileNotFoundError(f"Папка knowledge не найдена: {self.knowledge_dir}")

        loader = DirectoryLoader(
            self.knowledge_dir,
            glob="*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        docs = loader.load()
        if not docs:
            raise ValueError(f"В папке {self.knowledge_dir} нет .txt файлов!")

        splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        self.vectorstore.save_local(self.index_dir)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        print(f"✅ База знаний создана: {len(docs)} файлов, {len(chunks)} чанков")

    def get_retriever(self):
        return self.retriever

    def search(self, query: str, k: int = 3) -> str:
        """Get top k documents for the query"""
        if not self.retriever:
            raise ValueError("Retriever не инициализирован")
        docs = self.retriever.invoke(query)
        return "\n---\n".join(d.page_content for d in docs)
