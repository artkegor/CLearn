from langchain.agents import initialize_agent, Tool, AgentType

from agents.stats_analyzer.tools.brief_summary import brief_summary_tool
from agents.stats_analyzer.tools.detailed_summary import detailed_summary_tool
from agents.stats_analyzer.llm.model import llm


def build_agent():
    tools = [
        Tool(
            name="brief_summary_tool",
            func=brief_summary_tool,
            description="Краткое описание уровня знаний"
        ),
        Tool(
            name="detailed_summary_tool",
            func=detailed_summary_tool,
            description="Детальный анализ всех тем C"
        ),
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=False,
        system_message="""
Ты — агент анализа знаний пользователя по C.
Используй инструменты строго по необходимости.
Если инструмент возвращает {"success": False}, сообщи об ошибке.
"""
    )

    return agent
