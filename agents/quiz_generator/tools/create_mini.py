import json
from langchain_core.tools import tool
from agents.quiz_generator.rag.knowledge_base import KnowledgeBase
from agents.quiz_generator.config.llm import init_llm

kb = KnowledgeBase()
llm = init_llm()


@tool
def create_mini_quiz(topic: str) -> str:
    """Create a mini quiz on the given topic using knowledge from the RAG system."""
    try:
        docs = kb.search(topic)
        context = docs[:300]

        prompt = f"""Создай JSON мини-викторину по теме "{topic}".
Контекст:
{context}
Требования:
- 7 вопросов
- Только JSON в формате:
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
        text = response.content

        json_str = text[text.find("{"): text.rfind("}") + 1]
        return json_str

    except Exception as e:
        return json.dumps({"error": str(e)})