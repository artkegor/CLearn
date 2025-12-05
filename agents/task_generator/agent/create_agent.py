from langchain.agents import initialize_agent, Tool, AgentType
from agents.task_generator.tools.generate_task import generate_task_tool
from agents.task_generator.tools.generate_test_cases import generate_test_cases_tool
from agents.task_generator.tools.generate_solution import generate_solution_tool
from agents.task_generator.llm.model import llm

def build_agent():
    tools = [
        Tool(
            name="generate_task_tool",
            func=generate_task_tool,
            description="Генерация задания по теме C"
        ),
        Tool(
            name="generate_test_cases_tool",
            func=generate_test_cases_tool,
            description="Генерация тест-кейсов"
        ),
        Tool(
            name="generate_solution_tool",
            func=generate_solution_tool,
            description="Генерация решения"
        ),
    ]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=False,
        system_message="""
Ты — агент генерации заданий по C.
Используй инструменты по запросу пользователя.
Если инструмент возвращает {"success": False}, сообщи об ошибке.
"""
    )
    return agent