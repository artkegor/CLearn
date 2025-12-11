from typing import Dict, Any

from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek

from agents.coordinator.tools.task_generator_tool import task_generator_tool
from agents.coordinator.tools.code_checker_tool import code_checker_tool
from agents.coordinator.tools.tutor_tool import tutor_tool
from agents.coordinator.tools.quiz_maker_tool import quiz_maker_tool
from agents.coordinator.tools.stats_advisor_tool import stats_advisor_tool

from agents.coordinator.middleware.validation import validate_and_enrich_input_middleware
from agents.coordinator.middleware.classification import classify_agent_selection_middleware
from agents.coordinator.middleware.context_manager import trim_and_summarize_context_middleware
from agents.coordinator.middleware.logging_middleware import log_execution_and_save_memory_middleware

from agents.coordinator.memory.manager import CoordinatorMemoryManager

from agents.coordinator.coordinator.system_prompt import SYSTEM_PROMPT
from logging_config import setup_logging
from config import Config

logger = setup_logging()

coordinator = create_agent(
    model=ChatDeepSeek(
        model="deepseek-chat",
        api_key=Config.DEEPSEEK_API_KEY,
        temperature=0.7,
        max_tokens=4096,
        timeout=120,
    ),
    tools=[
        task_generator_tool,
        code_checker_tool,
        tutor_tool,
        quiz_maker_tool,
        stats_advisor_tool,
    ],
    system_prompt=SYSTEM_PROMPT,
    middleware=[
        validate_and_enrich_input_middleware,
        classify_agent_selection_middleware,
        trim_and_summarize_context_middleware,
        log_execution_and_save_memory_middleware,
    ],
)

logger.info("✅ Координатор успешно инициализирован")


def get_session_statistics(session_id: str) -> Dict[str, Any]:
    """
    Get statistics for a given session.
    """
    try:
        memory_manager = CoordinatorMemoryManager(session_id)
        return {
            "session_id": session_id,
            "agent_statistics": memory_manager.get_agent_statistics(),
            "recent_interactions": memory_manager.get_recent_context(limit=5),
        }
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return {"error": str(e), "session_id": session_id}
