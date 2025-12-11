from langchain_core.tools import tool
from agents.code_analyzer.llm.model import llm


@tool
def compare_task_and_solution_tool(task_text: str, solution_code: str) -> bool:
    """
    Tool to compare the generated solution code with the task description.
    """
    try:
        prompt = f"""
        Условие задачи:
{task_text}
        Решение задачи:
{solution_code}

        Проверь, соответствует ли решение условию задачи. Ответь "Да" или "Нет" и ничего более.
        """

        response = llm.invoke(prompt)
        answer = response.content.strip().lower()

        return answer == "да" or answer == "yes"
    except Exception:
        return False
