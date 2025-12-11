from langchain.agents.middleware import after_model
from logging_config import setup_logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

logger = setup_logging()


@after_model
def log_execution_and_save_memory_middleware(state: Dict[str, Any], runtime) -> Optional[Dict[str, Any]]:
    """
    Step 3: Log execution details and save interaction to memory.
    Logs:
    - User input preview
    - Recommended and called agent
    - Confidence score
    - Response preview
    Saves:
    - Interaction details to memory with metadata
    """

    messages = state.get("messages", [])
    memory_manager = state.get("_memory_manager")
    agent_selection = state.get("_agent_selection", {})

    if not messages or not memory_manager:
        return None

    # Получаем последний запрос и ответ
    user_message = messages[-2].content if len(messages) >= 2 else "Unknown"
    agent_response = messages[-1].content if messages[-1].content else "No response"

    recommended_agent = agent_selection.get("recommended_agent", "unknown")
    confidence = agent_selection.get("confidence", 0)

    # Определяем, какой агент был вызван в ответе (по контенту)
    called_agent = None
    for agent in ["task_generator", "code_checker", "tutor", "quiz_maker", "stats_advisor"]:
        if agent in agent_response.lower() or agent.replace("_", " ") in agent_response.lower():
            called_agent = agent
            break

    called_agent = called_agent or recommended_agent

    # Метаданные для сохранения
    metadata = {
        "recommended_agent": recommended_agent,
        "called_agent": called_agent,
        "confidence_score": confidence,
        "response_length": len(agent_response),
        "message_count": len(messages),
        "had_error": "ошибка" in agent_response.lower() or "error" in agent_response.lower()
    }

    # Сохраняем в памяти
    memory_manager.save_interaction(
        agent_name=called_agent,
        user_input=user_message[:200],  # Первые 200 символов
        agent_output=agent_response,
        metadata=metadata
    )

    # Логируем информацию
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_input": user_message[:100],
        "recommended_agent": recommended_agent,
        "called_agent": called_agent,
        "confidence": f"{confidence:.1%}",
        "response_preview": agent_response[:150],
        "had_error": metadata["had_error"],
        "message_count": len(messages)
    }

    logger.info(f"📋 Выполнение запроса:")
    logger.info(json.dumps(log_entry, indent=2, ensure_ascii=False))

    return None
