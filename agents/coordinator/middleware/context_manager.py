from typing import Any, Dict, Optional
from langchain.agents.middleware import before_model
from logging_config import setup_logging

logger = setup_logging()

@before_model
def trim_and_summarize_context_middleware(state: Dict[str, Any], runtime) -> Optional[Dict[str, Any]]:
    """
    Step 4: Trim and summarize context if it exceeds limits.
    Ensures the message history does not exceed a maximum number of messages.
    Returns:
    - Trimmed messages if trimming was performed
    """

    messages = state.get("messages", [])
    MAX_MESSAGES = 15

    if len(messages) <= MAX_MESSAGES:
        return None

    # Find all system messages to always retain
    system_messages = [
        msg for msg in messages
        if hasattr(msg, "type") and msg.type == "system"
    ]

    # If we exceed max messages, trim the oldest non-system messages
    if len(messages) > MAX_MESSAGES:
        # Select the most recent messages, ensuring system messages are retained
        trimmed_messages = system_messages + messages[-(MAX_MESSAGES - len(system_messages)):]

        logger.info(
            f"✂️ Контекст обрезан: {len(messages)} → {len(trimmed_messages)} сообщений "
            f"(сохранено {len(system_messages)} системных)"
        )

        state["messages"] = trimmed_messages
        return {"messages": trimmed_messages}

    return None