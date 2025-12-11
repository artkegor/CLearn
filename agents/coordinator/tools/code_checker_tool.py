from langchain.tools import tool
from logging_config import setup_logging
from agents.code_analyzer.agent.create_agent import build_agent

logger = setup_logging()


@tool
def code_checker_tool(user_request: str) -> str:
    """Проверка и исправление кода на C.

    Используйте этот инструмент КОГДА:
    - Пользователь отправил код для проверки
    - Нужно найти ошибки (синтаксис, логика)
    - Требуется оптимизация или рефакторинг кода
    - Нужен анализ корректности решения
    - НЕ используйте для объяснения концепций

    Входные данные: код для проверки и описание проблемы
    Выходные данные: найденные ошибки, рекомендации, исправленный код"""
    code_checker_agent = build_agent()
    logger.info(f"🔍 code_checker_tool вызван: {user_request[:50]}...")
    try:
        result = code_checker_agent.invoke({
            "messages": [{"role": "user", "content": user_request}]
        })
        response = result["messages"][-1].content
        logger.info("✅ code_checker_tool успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в code_checker_tool: {str(e)}")
        raise
