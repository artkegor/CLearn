from langchain.agents import create_agent
from agents.quiz_generator.config.llm import init_llm
from agents.quiz_generator.tools.registry import TOOLS


def build_agent():
    llm = init_llm()
    agent = create_agent(
        tools=TOOLS,
        model=llm
    )
    return agent
