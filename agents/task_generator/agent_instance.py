from functools import lru_cache
from agents.task_generator.agent.create_agent import build_agent
from agents.task_generator.tools.generate_test_cases import generate_test_cases_tool
from agents.task_generator.tools.generate_solution import generate_solution_tool
from agents.task_generator.tools.generate_task import generate_task_tool


# Instantiate the agent with caching to avoid rebuilding
@lru_cache(maxsize=1)
def get_agent():
    return build_agent()


agent = get_agent()


def generate_task_full(topic_id: str, difficulty: int):
    # Generate full task package: task, test cases, solution
    task_res = generate_task_tool.invoke({"topic_id": topic_id, "difficulty": difficulty})
    if not task_res.get("success"):
        return {"success": False, "error": task_res.get("error")}
    task_text = task_res["task_text"]

    test_result = generate_test_cases_tool.invoke({"task_text": task_text})
    if not test_result.get("success"):
        return {"success": False, "error": f"Ошибка генерации тестов: {test_result.get('error')}"}
    test_cases = test_result["test_cases"]

    solution_result = generate_solution_tool.invoke({"task_text": task_text})
    if not solution_result.get("success"):
        return {"success": False, "error": f"Ошибка генерации решения: {solution_result.get('error')}"}
    solution_code = solution_result["solution_code"]

    return {
        "success": True,
        "task_text": task_text,
        "test_cases": test_cases,
        "solution_code": solution_code
    }


def regenerate_task_solution(task_text: str):
    # Regenerate solution for an existing task
    solution_result = generate_solution_tool.invoke({"task_text": task_text})
    if not solution_result.get("success"):
        return {"success": False, "error": f"Ошибка генерации решения: {solution_result.get('error')}"}
    solution_code = solution_result["solution_code"]

    return {
        "success": True,
        "solution_code": solution_code
    }
