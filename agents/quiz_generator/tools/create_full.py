import json
from langchain_core.tools import tool
from agents.quiz_generator.rag.knowledge_base import KnowledgeBase
from agents.quiz_generator.config.llm import init_llm

kb = KnowledgeBase()
llm = init_llm()


@tool
def create_full_quiz(topic: str) -> str:
    """Create a full quiz on the given topic and difficulty using knowledge from the RAG system."""
    try:
        context = kb.search(topic)

        prompt = f"""Создай ПОЛНЫЙ JSON квиз по теме '{topic}'.
Количество вопросов: 10.
Используй контекст:
{context}
Только JSON в формате:
{{
  "quiz_title": "string",
  questions: [
    {{
      "id": int,
      "question_text": "string",
      "options": ["string", "string", "string", "string"],
      "correct_answer": int
    }}
  ]
}}
"""

        response = llm.invoke(prompt)
        txt = response.content
        json_str = txt[txt.find("{"): txt.rfind("}") + 1]
        return json_str

    except Exception as e:
        return json.dumps({"error": str(e)})
