from typing import Any, Dict


def format_memory_context_for_llm(memory_context: Dict[str, Any]) -> str:
    """
    Formats the memory context into a markdown string for LLM input.
    """

    if not memory_context:
        return ""

    recent_interactions = memory_context.get("recent_interactions", [])
    agent_stats = memory_context.get("agent_stats", {})

    formatted = "\n## 📚 КОНТЕКСТ ИЗ ПАМЯТИ\n\n"

    if agent_stats:
        formatted += "### Использованные агенты в этой сессии:\n"
        for agent, count in agent_stats.items():
            formatted += f"- {agent}: {count} раз(а)\n"
        formatted += "\n"

    if recent_interactions:
        formatted += "### Недавние взаимодействия:\n"
        for i, interaction in enumerate(recent_interactions[-3:], 1):
            agent = interaction.get("agent_name", "unknown")
            user_input = interaction.get("user_input", "")[:50]
            formatted += f"{i}. **{agent}**: {user_input}...\n"

    return formatted if len(formatted) > 50 else ""
