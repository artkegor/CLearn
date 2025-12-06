from langchain_core.tools import tool
from agents.quiz_generator.rag.knowledge_base import KnowledgeBase

kb = KnowledgeBase()


@tool
def get_c_knowledge(query: str) -> str:
    """Retrieve knowledge about the C programming language from the knowledge base."""
    return kb.search(query, k=3)