from typing import Dict, Any
from langchain.schema import SystemMessage, HumanMessage

from agents.task_generator.agent.deepseek_llm import DeepSeekLLM
from agents.task_generator.agent.rag_store import RAGStore
from config import Config


class TaskGenerator:
    def __init__(self, deepseek_api_key: str = Config.DEEPSEEK_API_KEY,
                 vector_db_dir: str = "./vector_db",
                 knowledge_base_dir: str = "./c_knowledge_data"):
        self.llm = DeepSeekLLM(api_key=deepseek_api_key)
        self.rag = RAGStore(vector_db_dir=vector_db_dir,
                            knowledge_base_dir=knowledge_base_dir)
        self.vectorstore = self.rag.load_or_create()

        self.c_topics = Config.C_TOPICS

        # Detailed system prompt for task generation
        self.system_prompt = Config.GENERATOR_SYSTEM_PROMPT

    def _rag_examples_context(self, topic_id: str, difficulty: int) -> str:
        """Find relevant examples from RAG store"""
        if not self.vectorstore:
            return ""

        topic_name = self.c_topics.get(topic_id, "Неизвестная тема")
        query = f"ТЕМА: {topic_name} СЛОЖНОСТЬ: {difficulty}"
        found = self.vectorstore.similarity_search(query, k=2)

        context = ""
        for d in found:
            context += f"\n---ПРИМЕР---\n{d.page_content}\n"

        return context

    def generate_task(self, topic_id: str, difficulty: int) -> Dict[str, Any]:
        """Generation of a programming task"""
        try:
            topic_name = self.c_topics.get(topic_id, "Неизвестная тема")
            examples_context = self._rag_examples_context(topic_id, difficulty)

            prompt = (
                f"{self.system_prompt}\n"
                f"Создай новое оригинальное задание по теме '{topic_name}' со сложностью {difficulty}.\n"
                f"Примеры:\n{examples_context}\n"
                "Требования:\n"
                "- Структура похожа на примеры, НО не нужно писать ТЕМА, СЛОЖНОСТЬ и ЗАДАНИЕ.\n"
                "- Укажи числовые ограничения.\n"
                "- Будь оригинален, не копируй примеры.\n"
            )

            messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=prompt)]
            task_text = self.llm._generate(messages)

            return {
                "success": True,
                "task_text": task_text,
                "topic_id": topic_id,
                "topic_name": topic_name,
                "difficulty": difficulty
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_test_cases(self, task_text: str) -> Dict[str, Any]:
        """Generation of test cases for the task"""
        import re
        import json

        try:
            prompt = (
                f"Создай ровно 5 тестовых примеров для следующего задания.\nЗадание:\n{task_text}\n"
                "Верни ТОЛЬКО JSON-массив в формате:\n"
                "[{\"input\": ..., \"expected_output\": ..., \"description\": ..., \"type\": ...}]"
            )

            messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=prompt)]
            response = self.llm._generate(messages)

            json_text = response.strip()
            json_text = re.sub(r"```(?:json)?", "", json_text, flags=re.IGNORECASE)

            match = re.search(r"(\[.*\])", json_text, re.DOTALL)
            if match:
                json_text = match.group(1)

            if not json_text.startswith("["):
                return {"success": False, "error": "LLM не вернул JSON массив"}

            test_cases = json.loads(json_text)

            if len(test_cases) != 5:
                return {"success": False, "error": f"Ожидалось 5 тестов, получено {len(test_cases)}"}

            return {"success": True, "test_cases": test_cases}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_solution(self, task_text: str) -> Dict[str, Any]:
        """Generation of a complete solution code for the task"""
        try:
            prompt = (
                f"Напиши полное и корректное решение на C для следующего задания:\n\n{task_text}\n\n"
                "Требования:\n"
                "- Приведи полный компилируемый код (с includes и main)\n"
                "- Добавь комментарии\n"
                "- Обработай крайние случаи\n"
                "Верни только исходный код, без пояснений."
            )

            messages = [SystemMessage(content=self.system_prompt), HumanMessage(content=prompt)]
            response = self.llm._generate(messages)

            import re
            code = re.sub(r"```(?:c|c\+\+)?", "", response, flags=re.IGNORECASE).strip()

            return {"success": True, "solution_code": code}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_complete_task(self, topic_id: str, difficulty: int) -> Dict[str, Any]:
        """Create a complete task with test cases and solution"""
        task_res = self.generate_task(topic_id, difficulty)

        if not task_res.get("success"):
            return task_res

        task_text = task_res["task_text"]

        tests_res = self.generate_test_cases(task_text)

        if not tests_res.get("success"):
            return tests_res

        sol_res = self.generate_solution(task_text)

        if not sol_res.get("success"):
            return sol_res

        return {
            "success": True,
            "task_text": task_text,
            "test_cases": tests_res["test_cases"],
            "solution_code": sol_res["solution_code"],
            "topic_id": task_res["topic_id"],
            "topic_name": task_res["topic_name"],
            "difficulty": difficulty
        }
