from langchain_core.tools import tool
from agents.task_generator.llm.model import llm


@tool
def generate_solution_tool(task_text: str) -> dict:
    """
    Generate solution code for the given task in C.
    """
    try:
        prompt = f"""
Напиши рабочее решение задачи на C.

Задача:
{task_text}

Требования:
- Полный компилируемый код C
- С комментариями
- Верни только код
"""

        code = llm.invoke(prompt).content
        code = code.replace("```c", "").replace("```", "").strip()

        return {"success": True, "solution_code": code}

    except Exception as ex:
        return {"success": False, "error": str(ex)}
