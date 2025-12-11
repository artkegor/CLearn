from langchain.tools import tool
from agents.tutor.rag_retrievers.retrievers import get_retrievers

syntax_retriever = get_retrievers()["syntax"]

@tool
def syntax_search(query: str) -> str:
    """Поиск информации по синтаксису языка C."""
    results = syntax_retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in results])