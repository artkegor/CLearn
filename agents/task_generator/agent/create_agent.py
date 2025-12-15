from langchain.agents import create_agent
from agents.task_generator.tools.generate_task import generate_task_tool
from agents.task_generator.tools.generate_test_cases import generate_test_cases_tool
from agents.task_generator.tools.generate_solution import generate_solution_tool
from agents.task_generator.llm.model import llm
from agents.task_generator.middleware.middleware import (validate_input_middleware, enrich_context_middleware,
                                                         log_model_response_middleware)


def build_agent():
    tools = [
        generate_task_tool,
        generate_test_cases_tool,
        generate_solution_tool
    ]

    agent = create_agent(
        tools=tools,
        model=llm,
        system_prompt="""
Ты — агент генерации заданий по C.
Используй инструменты по запросу пользователя.
Если инструмент возвращает {"success": False}, сообщи об ошибке.
""",
        middleware=[
            validate_input_middleware,
            enrich_context_middleware,
            log_model_response_middleware,
        ]
    )
    return agent
