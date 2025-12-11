from langchain.agents.middleware import before_agent
from agents.coordinator.memory.manager import CoordinatorMemoryManager
from logging_config import setup_logging
from langchain_core.messages import AIMessage
from typing import Dict, Any, Optional

logger = setup_logging()


@before_agent
def validate_and_enrich_input_middleware(state: Dict[str, Any], runtime) -> Optional[Dict[str, Any]]:
    """
    Step 1: validate user input and enrich state with memory context
    Checks:
    - If the user message is present and non-empty
    - If the message length is sufficient
    Enriches state with:
    - Recent interactions from memory
    - Agent usage statistics
    """

    messages = state.get("messages", [])

    if not messages:
        error_msg = "❌ ОШИБКА: Запрос пуст. Пожалуйста, отправьте вопрос или команду."
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

    # Get the latest user message
    user_message = messages[-1].content.lower() if messages[-1].content else ""

    if len(user_message.strip()) < 3:
        error_msg = "❌ ОШИБКА: Запрос слишком короткий. Опишите подробнее, что вам нужно."
        return {
            "messages": messages + [AIMessage(content=error_msg)]
        }

    # Initialize memory manager
    session_id = state.get("session_id", "default_session")
    memory_manager = CoordinatorMemoryManager(session_id)

    # Get recent interactions and agent stats
    recent_interactions = memory_manager.get_recent_context(limit=3)
    agent_stats = memory_manager.get_agent_statistics()

    # Enrich state with memory context
    state["_memory_context"] = {
        "recent_interactions": recent_interactions,
        "agent_stats": agent_stats,
        "session_id": session_id
    }
    state["_memory_manager"] = memory_manager

    logger.info(f"✅ Входные данные валидированы. Контекст загружен из памяти")
    logger.info(f"📊 Статистика использования агентов: {agent_stats}")

    return None
