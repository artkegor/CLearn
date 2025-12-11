from langchain_core.tools import tool
from agents.code_analyzer.llm.model import llm
from agents.code_analyzer.llm.system_prompt import SYSTEM_PROMPT


@tool
def analyze_and_advise_tool(task_text: str, user_code: str, error_text: str):
    """
    Tool to analyze user code and provide advice based on the task description and error message.
    """
    try:
        prompt = f"""
Условие задачи:
{task_text}

Код пользователя:
{user_code}

Ошибка:
{error_text}

Теперь проанализируй код по правилам:
{SYSTEM_PROMPT}

Сформируй грамотные рекомендации:
"""

        response = llm.invoke(prompt)

        return {
            "success": True,
            "advice": response.content.strip()
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


