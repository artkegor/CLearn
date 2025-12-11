from langchain.tools import tool
from agents.tutor.rag_retrievers.retrievers import get_retrievers

functions_retriever = get_retrievers()["functions"]

@tool
def functions_search(query: str) -> str:
    """Поиск информации по функциям в C.

    Используй этот инструмент для вопросов о:
    • Определение и объявление функций
    • Параметры функций, возвращаемые значения
    • Рекурсия и стек вызовов
    • Указатели на функции
    • Встроенные функции (strlen, printf, malloc и т.д.)
    """
    results = functions_retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in results])