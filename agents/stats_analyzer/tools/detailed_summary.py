from langchain_core.tools import tool
from agents.stats_analyzer.llm.model import llm


@tool
def detailed_summary_tool(user_data: str) -> dict:
    """
    Tool to generate a detailed summary of user skills in C programming.
    """
    system_prompt = """
Ты опытный преподаватель C.
Дай оценку общего уровня знаний пользователя и выдели сильные и слабые стороны.
Обращайся к пользователю на "ты".
Не форматируй текст (жирный, курсив и т.д.).

Оформи ответ в формате (по темам, по которым есть данные):

Тема:
• Комментарий по теме 

Общий уровень:  

Рекомендация: 
"""

    prompt = (
        f"Ниже результаты пользователя в решении задач на соответствующие темы (x из 100):\n{user_data}\n\n"
        f"Их не нужно вкладывать в ответ, они только для понимания твоей задачи.\n\n"
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
