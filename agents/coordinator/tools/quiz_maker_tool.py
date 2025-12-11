from langchain.tools import tool
from logging_config import setup_logging
from agents.quiz_generator.agent.factory import build_agent

logger = setup_logging()


@tool
def quiz_maker_tool(user_request: str) -> str:
    """Создатель тестов и контрольных работ по C.

    Используйте этот инструмент КОГДА:
    - Пользователь просит пройти тест
    - Нужна контрольная работа для оценки знаний
    - Требуется квиз с вариантами ответов
    - Пользователь хочет проверить свои знания
    - НЕ используйте для объяснения теории

    """
    quiz_maker_agent = build_agent()
    logger.info(f"❓ quiz_maker_tool вызван: {user_request[:50]}...")
    try:
        result = quiz_maker_agent.invoke({
            "messages": [{"role": "user", "content": user_request}]
        })
        response = result["messages"][-1].content
        logger.info("✅ quiz_maker_tool успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в quiz_maker_tool: {str(e)}")
        raise
