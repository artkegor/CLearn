from langchain_core.tools import tool
from agents.task_generator.llm.model import llm
import json
import re


@tool
def generate_test_cases_tool(task_text: str) -> dict:
    """Создаёт новое учебное задание по программированию на C на основе темы и уровня сложности.

     КОГДА ИСПОЛЬЗОВАТЬ: Используй этот инструмент когда пользователь просит:
     - Создать новое задание
     - Сгенерировать упражнение
     - Придумать задачу для практики
     - Загрузить задание на определённую тему

     Args:
         topic_id: ID темы программирования на C (от "1" до "10"):
                   1 = Переменные и типы данных
                   2 = Условные операторы (if/else)
                   3 = Циклы (for/while)
                   4 = Массивы
                   5 = Функции
                   6 = Указатели
                   7 = Структуры данных
                   8 = Работа с файлами
                   9 = Динамическая память
                   10 = Препроцессор

         difficulty: Уровень сложности задания (целое число от 1 до 3):
                    1 = Лёгкое (базовые концепции, 1 цикл или 1 условие)
                    2 = Среднее (комбинация 2-3 концепций, логика с условиями)
                    3 = Сложное (хитрые решения, граничные случаи, оптимизация)

     Returns:
         Словарь с полями:
         - 'task_text': Полный текст задания (передавай в generate_test_cases_tool)
         - 'topic_id': Исходный ID темы
         - 'topic_name': Название темы на русском
         - 'difficulty': Исходный уровень сложности
         - 'error': Сообщение об ошибке (если success=False)
     """
    try:
        prompt = f"""
Создай 5 тест-кейсов для задания:

{task_text}

Формат:
[
  {{"input":"...", "expected_output":"...", "description":"...", "type":"normal"}},
  ...
]

Верни только JSON.
"""

        r = llm.invoke(prompt).content.strip()

        cleaned = r.replace("```json", "").replace("```", "").strip()
        match = re.search(r"(\[.*\])", cleaned, re.DOTALL)

        if not match:
            return {"success": False, "error": "LLM не вернул JSON"}

        cases = json.loads(match.group(1))
        return {"success": True, "test_cases": cases}

    except Exception as ex:
        return {"success": False, "error": str(ex)}
