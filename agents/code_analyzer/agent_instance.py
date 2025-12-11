from functools import lru_cache
from agents.task_generator.agent.create_agent import build_agent
from agents.code_analyzer.tools.analyze_and_advise import analyze_and_advise_tool
from agents.code_analyzer.tools.compare_task_and_solution_tool import compare_task_and_solution_tool


# Singleton pattern to get the agent instance
@lru_cache(maxsize=1)
def get_agent():
    return build_agent()


agent = get_agent()


def analyze_code(task_text: str, user_code: str, error_text: str):
    """
    Function to analyze user code and provide advice.
    """
    result = analyze_and_advise_tool.invoke({
        "task_text": task_text,
        "user_code": user_code,
        "error_text": error_text
    })

    if not result.get("success"):
        return {"success": False, "error": result.get("error")}
    result = result["advice"]

    return result


def compare_task_and_solution(task_text: str, solution_code: str) -> bool:
    result = compare_task_and_solution_tool.invoke({
        "task_text": task_text,
        "solution_code": solution_code
    })

    return result
