from langchain_core.tools import tool
from agents.task_generator.llm.model import llm
from agents.task_generator.llm.system_prompt import SYSTEM_PROMPT
from agents.task_generator.rag.vectorstore import vectorstore
from config import Config


@tool
def generate_task_tool(topic_id: str, difficulty: int) -> dict:
    """
    Generate a new task based on topic and difficulty.
    """
    try:
        topic_name = Config.C_TOPICS.get(topic_id, "Неизвестная тема")

        query = f"ТЕМА: {topic_name} СЛОЖНОСТЬ: {difficulty}"
        examples = vectorstore.similarity_search(query, k=7)

        examples_text = "\n".join(
            f"--- ПРИМЕР ---\n{doc.page_content}\n"
            for doc in examples
        )

        prompt = f"""
{SYSTEM_PROMPT}

Создай новое задание по теме "{topic_name}" сложности {difficulty}.

Примеры:
{examples_text}

Сгенерируй новое задание:
"""

        result = llm.invoke(prompt)
        return {"success": True, "task_text": result.content}

    except Exception as ex:
        return {"success": False, "error": str(ex)}
