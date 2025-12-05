from langchain_core.tools import tool
from agents.task_generator.llm.model import llm
import json
import re


@tool
def generate_test_cases_tool(task_text: str) -> dict:
    """
    Generate test cases for the given task.
    """
    try:
        prompt = f"""
Создай 5 тест-кейсов для задания:

{task_text}

Формат:
[
  {{"input":"...", "expected_output":"...", "description":"...", "type":"normal"}},
  ...
]

Верни только JSON.
"""

        r = llm.invoke(prompt).content.strip()

        cleaned = r.replace("```json", "").replace("```", "").strip()
        match = re.search(r"(\[.*\])", cleaned, re.DOTALL)

        if not match:
            return {"success": False, "error": "LLM не вернул JSON"}

        cases = json.loads(match.group(1))
        return {"success": True, "test_cases": cases}

    except Exception as ex:
        return {"success": False, "error": str(ex)}
