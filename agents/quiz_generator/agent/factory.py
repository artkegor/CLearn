from langchain.agents import initialize_agent, AgentType
from agents.quiz_generator.config.llm import init_llm
from agents.quiz_generator.tools.registry import TOOLS


def build_agent():
    llm = init_llm()
    agent = initialize_agent(
        tools=TOOLS,
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return agent
