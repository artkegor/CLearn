from langchain.agents import AgentExecutor
from agents.quiz_generator.agent.factory import build_agent
from agents.quiz_generator.tools.registry import TOOLS


def create_executor():
    agent = build_agent()
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True
    )
    return executor