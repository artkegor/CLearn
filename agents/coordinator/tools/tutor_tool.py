from langchain.tools import tool
from logging_config import setup_logging
from agents.tutor.agent_setup import create_c_agent

logger = setup_logging()


@tool
def tutor_tool(user_request: str) -> str:
    """Преподаватель по языку C.

    Используйте этот инструмент КОГДА:
    - Пользователь задает вопрос о синтаксисе C
    - Нужно объяснить концепцию (указатели, массивы, функции и т.д.)
    - Требуется помощь с пониманием алгоритма
    - Пользователь спрашивает "как это работает?" или "что это?
    - НЕ используйте для проверки готового кода
    """
    tutor_agent = create_c_agent()
    logger.info(f"🎓 tutor_tool вызван: {user_request[:50]}...")
    try:
        result = tutor_agent.invoke({
            "messages": [{"role": "user", "content": user_request}]
        })
        response = result["messages"][-1].content
        logger.info("✅ tutor_tool успешно выполнен")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка в tutor_tool: {str(e)}")
        raise
