from langchain.tools import tool
from agents.tutor.rag_retrievers.retrievers import get_retrievers

data_structures_retriever = get_retrievers()["data_structures"]

@tool
def data_structures_search(query: str) -> str:
    """Поиск информации по структурам данных в C.

    Используй этот инструмент для вопросов о:
    • Массивы и многомерные массивы
    • Указатели и арифметика указателей
    • Структуры (struct) и typedef
    • Строки как массивы символов
    • Память и адреса
    """
    results = data_structures_retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in results])