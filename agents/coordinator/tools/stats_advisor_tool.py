from langchain.tools import tool
from logging_config import setup_logging
from agents.stats_analyzer.agent.create_agent import build_agent

logger = setup_logging()


@tool
def stats_advisor_tool(user_request: str) -> str:
    """Аналитик прогресса и советник по обучению.

    Используйте этот инструмент КОГДА:
    - Пользователь запрашивает свою статистику
    - Нужны рекомендации по улучшению
    - Требуется анализ слабых сторон
    - Пользователь спрашивает "на чём мне сосредоточиться?"
    - НЕ используйте для других задач

    """
    stats_advisor_agent = build_agent()
    logger.info(f"📊 stats_advisor_tool вызван: {user_request[:50]}...")
    try:
        result = stats_advisor_agent.invoke({
            "messages": [{"role": "user", "content": user_request}]
        })
        response = result["messages"][-1].content
        logger.info("✅ stats_advisor_tool успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в stats_advisor_tool: {str(e)}")
        raise
