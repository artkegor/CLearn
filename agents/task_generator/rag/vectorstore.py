from langchain_community.vectorstores import FAISS
from .embeddings import embeddings

vectorstore = FAISS.load_local(
    "agents/task_generator/vector_db/task_generation_faiss",
    embeddings,
    allow_dangerous_deserialization=True
)