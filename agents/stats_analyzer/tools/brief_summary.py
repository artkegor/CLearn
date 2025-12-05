from langchain_core.tools import tool
from agents.stats_analyzer.llm.model import llm


@tool
def brief_summary_tool(user_data: str) -> dict:
    """
    Tool to generate a brief summary of user skills in C programming.
    """
    system_prompt = """
Ты опытный репетитор по C.
Сделай краткую сводку в 2–3 предложениях.
Дай оценку общего уровня знаний пользователя и выдели сильные и слабые стороны.
Обращайся к пользователю на "ты".
Не форматируй текст (жирный, курсив и т.д.).
"""

    prompt = (
        f"Результаты пользователя в решении задач на соответствующие темы (x из 100):\n{user_data}\n\n"
        "Вот словарь индекс-тема заданий:\n"
        "1: Переменные и типы данных\n"
        "2: Условные операторы\n"
        "3: Циклы\n"
        "4: Массивы\n"
        "5: Функции\n"
        "6: Указатели\n"
        "7: Структуры данных\n"
        "8: Работа с файлами\n"
        "9: Динамическая память\n"
        "10: Препроцессор\n"
    )
    try:
        response = llm.invoke(system_prompt + prompt)
        return {"success": True, "summary": response.content.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}
