from langchain.agents import create_agent
from agents.code_analyzer.llm.model import llm
from agents.code_analyzer.tools.analyze_and_advise import analyze_and_advise_tool


def build_agent():
    return create_agent(
        model=llm,
        tools=[analyze_and_advise_tool],
        system_prompt="Ты — агент анализа ошибок кода на C и выдачи советов."
    )
