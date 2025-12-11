from langchain.agents.middleware import before_model
from logging_config import setup_logging
from typing import Dict, Any, Optional

logger = setup_logging()


@before_model
def classify_agent_selection_middleware(state: Dict[str, Any], runtime) -> Optional[Dict[str, Any]]:
    """
    Step 2: Classify user request to recommend the most suitable agent.
    Analyzes the latest user message to determine which agent is best suited
    to handle the request based on keyword matching.
    ️Returns:
    - recommended_agent: str - the agent best suited for the request
    - confidence: float - confidence score of the recommendation
    - alternatives: List[str] - other potential agents
    """

    messages = state.get("messages", [])
    if not messages:
        return None

    user_message = messages[-1].content.lower()

    # Dictionary of agents and their associated keywords
    agent_keywords = {
        "task_generator": ["задание", "создать", "новое задание", "упражнение", "задачу"],
        "code_checker": ["проверить", "ошибка", "исправить", "код", "баг", "debug", "тест"],
        "tutor": ["объясни", "что это", "как это", "концепция", "синтаксис", "пример", "понять"],
        "quiz_maker": ["тест", "контрольная", "квиз", "проверь знания", "вопросы"],
        "stats_advisor": ["статистика", "прогресс", "результаты", "рекомендации", "улучшить", "анализ"]
    }

    # Get keyword scores for each agent
    agent_scores = {}

    for agent, keywords in agent_keywords.items():
        score = sum(1 for keyword in keywords if keyword in user_message)
        agent_scores[agent] = score

    # Determine the best agent based on scores
    best_agent = max(agent_scores, key=agent_scores.get) if agent_scores else "task_generator"
    confidence = agent_scores.get(best_agent, 0) / len(user_message.split()) if user_message else 0

    # Select up to two alternative agents
    alternatives = [agent for agent, score in agent_scores.items()
                    if score > 0 and agent != best_agent][:2]

    agent_selection = {
        "recommended_agent": best_agent,
        "confidence": min(confidence, 1.0),
        "alternatives": alternatives,
        "keyword_scores": agent_scores
    }

    state["_agent_selection"] = agent_selection

    logger.info(f"🤖 Рекомендуемый агент: {best_agent} (уверенность: {confidence:.1%})")
    logger.info(f"🔄 Альтернативы: {alternatives}")

    return None
