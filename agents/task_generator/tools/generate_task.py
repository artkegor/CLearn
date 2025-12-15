from langchain_core.tools import tool
from agents.task_generator.llm.model import llm
from agents.task_generator.llm.system_prompt import SYSTEM_PROMPT
from agents.task_generator.rag.vectorstore import vectorstore
from config import Config


@tool
def generate_task_tool(topic_id: str, difficulty: int) -> dict:
    """Генерирует полное работающее решение задания на языке C.

        КОГДА ИСПОЛЬЗОВАТЬ: Используй этот инструмент когда пользователь просит:
        - Решение или ответ к задаче
        - Пример кода на C
        - Подсказку как решать
        - Готовый код для скомпилирования

        ФОРМАТ: Вернёт обычный код на C (не JSON), с #include, main(), и всеми необходимыми функциями.
        Готов к копированию и запуску в компиляторе.
        Args:
            task_text: Полный текст задания из generate_task_tool.
                       Должно содержать: описание задачи, формат входа/выхода.
                       ВАЖНО: Передавай 'task_text' точно как он был в результате generate_task_tool.
        Returns:
            Словарь с полями:
            - 'solution_code': Полный исходный код на C:
              * Содержит все необходимые #include (stdio.h, stdlib.h и т.д.)
              * Содержит функцию main() с обработкой входных данных
              * Содержит вспомогательные функции если нужны
              * Содержит комментарии к важным алгоритмам
            - 'error': Сообщение об ошибке (если success=False)
    """
    try:
        topic_name = Config.C_TOPICS.get(topic_id, "Неизвестная тема")

        query = f"ТЕМА: {topic_name} СЛОЖНОСТЬ: {difficulty}"
        examples = vectorstore.similarity_search(query, k=7)

        examples_text = "\n".join(
            f"--- ПРИМЕР ---\n{doc.page_content}\n"
            for doc in examples
        )

        prompt = f"""
{SYSTEM_PROMPT}

Создай новое задание по теме "{topic_name}" сложности {difficulty}.

Примеры:
{examples_text}

Сгенерируй новое задание:
"""

        result = llm.invoke(prompt)
        return {"success": True, "task_text": result.content}

    except Exception as ex:
        return {"success": False, "error": str(ex)}
