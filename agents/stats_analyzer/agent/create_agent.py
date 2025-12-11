from langchain.agents import create_agent

from agents.stats_analyzer.tools.brief_summary import brief_summary_tool
from agents.stats_analyzer.tools.detailed_summary import detailed_summary_tool
from agents.stats_analyzer.llm.model import llm


def build_agent():
    tools = [
        brief_summary_tool,
        detailed_summary_tool
    ]

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
Ты — агент анализа знаний пользователя по C.
Используй инструменты строго по необходимости.
Если инструмент возвращает {"success": False}, сообщи об ошибке.
"""
    )

    return agent
