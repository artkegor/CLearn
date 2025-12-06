import json
from langchain_core.tools import tool
from agents.quiz_generator.rag.knowledge_base import KnowledgeBase
from agents.quiz_generator.config.llm import init_llm

kb = KnowledgeBase()
llm = init_llm()


@tool
def create_blitz_quiz(topic: str) -> str:
    """Crеate a blitz quiz on the given topic using knowledge from the RAG system."""
    try:
        docs = kb.get_retriever().invoke(f"{topic} в C")
        context = "\n".join(d.page_content for d in docs)

        prompt = f"""Ты генератор блиц-вопросов по C.

Контекст:
{context}

Сгенерируй JSON блиц-опрос по теме "{topic}". Требования:
- 5 вопросов
- 4 варианта
- correct_answer = цифра от 0 до 3, обозначающая правильный ответ
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
        text = response.content

        json_str = text[text.find("{"): text.rfind("}") + 1]
        data = json.loads(json_str)

        return json.dumps(data, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
