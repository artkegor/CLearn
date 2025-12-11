from langchain.tools import tool
from logging_config import setup_logging
from agents.task_generator.agent.create_agent import build_agent

logger = setup_logging()


@tool
def task_generator_tool(user_request: str) -> str:
    """Генератор задач по C программированию.

    Используйте этот инструмент КОГДА:
    - Пользователь просит создать новое задание
    - Пользователь хочет обучающую задачу на конкретную тему
    - Требуется практическое задание с проверкой
    - НЕ используйте если пользователь просто спрашивает о концепции

    """
    task_generator_agent = build_agent()
    logger.info(f"📝 task_generator_tool вызван: {user_request[:50]}...")
    try:
        result = task_generator_agent.invoke({
            "messages": [{"role": "user", "content": user_request}]
        })
        response = result["messages"][-1].content
        logger.info("✅ task_generator_tool успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в task_generator_tool: {str(e)}")
        raise
