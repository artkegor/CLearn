from langchain.tools import tool
from agents.tutor.rag_retrievers.retrievers import get_retrievers

control_flow_retriever = get_retrievers()["control_flow"]

@tool
def control_flow_search(query: str) -> str:
    """Поиск информации по управлению потоком в C.

    Используй этот инструмент для вопросов о:
    • Условные операторы (if, else if, else — логика ветвления)
    • Оператор выбора (switch/case/default — множественный выбор)
    • Циклы for, while, do-while
    • Управление циклами (break, continue)
    • Вложенные условия и циклы
    • Операторы сравнения и логические операторы (&&, ||, !)
    """
    results = control_flow_retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in results])