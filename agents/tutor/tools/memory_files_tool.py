from langchain.tools import tool
from agents.tutor.rag_retrievers.retrievers import get_retrievers

memory_files_retriever = get_retrievers()["memory_files"]

@tool
def memory_files_search(query: str) -> str:
    """Поиск информации по памяти и файлам в C.

    Используй этот инструмент для вопросов о:
    • Динамическое выделение памяти (malloc, calloc, realloc)
    • Освобождение памяти (free)
    • Работа с файлами (fopen, fclose, fread, fwrite)
    • Препроцессор (#include, #define)
    • Потоковая передача данных (stdin, stdout, stderr)
    • Обработка ошибок при работе с памятью и файлами
    """
    results = memory_files_retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in results])