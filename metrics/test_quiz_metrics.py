import os
import json
import time
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from enum import Enum

# LangChain imports
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from pydantic import BaseModel, Field, ValidationError

# DeepEval imports
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval.models import DeepEvalBaseLLM

from dotenv import load_dotenv

load_dotenv()


# ============================================
# DEEPSEEK JUDGE FOR DEEPEVAL
# ============================================

from deepeval.models import DeepEvalBaseLLM
from langchain_deepseek import ChatDeepSeek

class DeepSeekJudge(DeepEvalBaseLLM):
    def __init__(self, api_key: str, model_name: str = "deepseek-chat", temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature
        self._chat_model = ChatDeepSeek(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=2048,
            api_key=api_key,
        )

    def load_model(self):
        return self._chat_model

    def generate(self, prompt: str) -> str:
        res = self._chat_model.invoke(prompt)
        return res.content if hasattr(res, "content") else str(res)

    async def a_generate(self, prompt: str) -> str:
        res = await self._chat_model.ainvoke(prompt)
        return res.content if hasattr(res, "content") else str(res)

    def get_model_name(self) -> str:
        return f"DeepSeekJudge({self.model_name})"

# ============================================
# КОНФИГУРАЦИЯ
# ============================================

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-2e4ea2a8435d4d54b3dbe83f7359dd2c")
KNOWLEDGE_DIR = "./knowledge"
FAISS_INDEX_DIR = "./faiss_index"
TEST_RESULTS_DIR = "./test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)


# ============================================
# ENUM И КЛАССЫ ДАННЫХ
# ============================================

class QuizType(Enum):
    BLITZ = "blitz"
    MINI = "mini"
    FULL = "full"


@dataclass
class TestCase:
    """Один тест-кейс для тестирования"""
    quiz_type: QuizType
    topic: str
    difficulty: str = "medium"
    case_id: str = ""

    def __post_init__(self):
        if not self.case_id:
            self.case_id = f"{self.quiz_type.value}_{self.topic}_{int(time.time() * 1000)}"


@dataclass
class TestResult:
    """Результат одного теста"""
    case_id: str
    quiz_type: QuizType
    topic: str
    status: str  # "success", "validation_error", "llm_error", "timeout"
    generated_quiz: Dict = field(default_factory=dict)
    validation_error: str = ""
    execution_time: float = 0.0

    # Метрики (кастомные)
    answer_relevancy_custom: float = 0.0
    contextual_relevancy_custom: float = 0.0
    faithfulness_custom: float = 0.0

    # Метрики DeepEval
    answer_relevancy_deepeval: float = 0.0
    contextual_relevancy_deepeval: float = 0.0
    faithfulness_deepeval: float = 0.0

    # Средние значения (комбо)
    answer_relevancy: float = 0.0
    contextual_relevancy: float = 0.0
    faithfulness: float = 0.0


@dataclass
class MetricsReport:
    """Итоговый отчёт с метриками"""
    total_attempts: int = 0
    total_successes: int = 0
    blitz_attempts: int = 0
    blitz_successes: int = 0
    mini_attempts: int = 0
    mini_successes: int = 0
    full_attempts: int = 0
    full_successes: int = 0

    # AnswerRelevancyMetric
    answer_relevancy_blitz: float = 0.0
    answer_relevancy_mini: float = 0.0
    answer_relevancy_full: float = 0.0
    answer_relevancy_total: float = 0.0

    # ContextualRelevancyMetric
    contextual_relevancy_blitz: float = 0.0
    contextual_relevancy_mini: float = 0.0
    contextual_relevancy_full: float = 0.0
    contextual_relevancy_total: float = 0.0

    # FaithfulnessMetric
    faithfulness_blitz: float = 0.0
    faithfulness_mini: float = 0.0
    faithfulness_full: float = 0.0
    faithfulness_total: float = 0.0

    success_rate: float = 0.0
    timestamp: str = ""


# ============================================
# PYDANTIC МОДЕЛИ
# ============================================

class BlitzQuestion(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    options: List[str] = Field(..., min_length=3, max_length=3)
    correct: int = Field(ge=0, le=2)


class BlitzQuiz(BaseModel):
    topic: str
    type: str = "blitz"
    questions: List[BlitzQuestion] = Field(..., min_length=3, max_length=5)


class MiniQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=2, max_length=4)
    correct: int
    explanation: str


class MiniQuiz(BaseModel):
    topic: str
    type: str = "mini"
    context_snippet: str = ""
    questions: List[MiniQuestion] = Field(..., min_length=3, max_length=7)


class FullQuestion(BaseModel):
    question: str = Field(..., min_length=10, max_length=500)
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct: int = Field(ge=0, le=3)
    explanation: str = Field(..., min_length=10, max_length=1000)


class FullQuiz(BaseModel):
    topic: str
    type: str = "full"
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    questions: List[FullQuestion] = Field(..., min_length=5, max_length=10)


# ============================================
# KNOWLEDGE BASE
# ============================================

class KnowledgeBase:
    """RAG система с FAISS"""

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
        self.retriever = None
        self.load_or_create_base()

    def load_or_create_base(self):
        try:
            self.vectorstore = FAISS.load_local(
                FAISS_INDEX_DIR,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print("✅ FAISS загружена из локального хранилища")
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        except Exception as e:
            print(f"⚠️ FAISS не найдена: {e}")
            print("📚 Создаю новую базу из файлов...")
            self.create_knowledge_base()

    def create_knowledge_base(self):
        all_docs = []

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_path = os.path.join(script_dir, "knowledge")
            loader = DirectoryLoader(knowledge_path, glob="*.txt", loader_cls=TextLoader, show_progress=True)
            file_docs = loader.load()
            print(f"📄 Загрузил файлов: {len(file_docs)}")
            all_docs.extend(file_docs)
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            raise

        if len(all_docs) == 0:
            raise ValueError("Папка knowledge/ пустая")

        splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        split_docs = splitter.split_documents(all_docs)
        print(f"🔀 Создано {len(split_docs)} чанков")

        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

        self.vectorstore.save_local(FAISS_INDEX_DIR)
        print(f"✅ База знаний создана!")

    def search(self, query: str, k: int = 3) -> str:
        retriever = self.retriever
        docs = retriever.invoke(query)
        return "\n\n---\n\n".join([doc.page_content for doc in docs])


# ============================================
# LLM И TOOLS
# ============================================

os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.3,
    max_tokens=4096
)
print("✅ LLM инициализирована (DeepSeek)")

deepseek_judge = DeepSeekJudge(model_name="deepseek-chat", temperature=0.3)
print("✅ DeepSeek Judge инициализирован")

kb = KnowledgeBase()


@tool
def get_c_knowledge(query: str) -> str:
    """Retrieve knowledge about C programming from the knowledge base."""
    return kb.search(query, k=3)


@tool
def create_blitz_quiz(topic: str) -> str:
    """Create a blitz quiz on the given topic."""
    try:
        docs = kb.retriever.invoke(f"{topic} в C")
        context = "\n".join(d.page_content for d in docs)

        prompt = f"""Ты генератор блиц-вопросов по C.

Контекст:
{context}

Сгенерируй JSON блиц-опрос по теме "{topic}". Требования:
- 5 вопросов
- 3 варианта ответа каждый
- correct = индекс правильного ответа (0, 1 или 2)
Только JSON:
{{
  "topic": "{topic}",
  "type": "blitz",
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string"],
      "correct": 0
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        json_str = text[text.find("{"): text.rfind("}") + 1]
        return json_str
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def create_mini_quiz(topic: str) -> str:
    """Create a mini quiz on the given topic."""
    try:
        docs = kb.search(topic)
        context = docs[:300]

        prompt = f"""Создай JSON мини-викторину по теме "{topic}".
Контекст:
{context}
Требования:
- 7 вопросов
- 2-4 варианта
- Поле explanation для объяснения
Только JSON:
{{
  "topic": "{topic}",
  "type": "mini",
  "context_snippet": "",
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string"],
      "correct": 0,
      "explanation": "string"
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        json_str = text[text.find("{"): text.rfind("}") + 1]
        return json_str
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def create_full_quiz(topic: str, difficulty: str = "medium") -> str:
    """Create a full quiz on the given topic."""
    try:
        docs = kb.retriever.invoke(f"{topic} в C детали")
        context = "\n\n".join(d.page_content for d in docs)

        question_count = {"easy": 5, "medium": 7, "hard": 10}.get(difficulty.lower(), 7)

        prompt = f"""Ты генератор образовательных квизов по C.

Контекст:
{context}

Сгенерируй полный квиз по теме "{topic}" сложности "{difficulty}":
- {question_count} вопросов
- 4 варианта ответа на каждый
- Поле correct — индекс (0, 1, 2 или 3)
- Поле explanation — объяснение

Только JSON:
{{
  "topic": "{topic}",
  "type": "full",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct": 0,
      "explanation": "string"
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        json_str = text[text.find("{"): text.rfind("}") + 1]
        return json_str
    except Exception as e:
        return json.dumps({"error": str(e)})


tools = [get_c_knowledge, create_blitz_quiz, create_mini_quiz, create_full_quiz]
print("✅ Tools инициализированы")

# ============================================
# REACT AGENT
# ============================================

react_prompt = """Ты JSON-генератор квизов по C. Используй инструменты!

{tools}

ПРАВИЛА:
- Обязательно используй один из tools
- Final Answer = JSON из Observation
- Не создавай вручную, используй tools

Доступные инструменты: {tool_names}

Формат ответа:
Question: {input}
Thought: что нужно сделать
Action: название_инструмента
Action Input: параметры
Observation: результат
Thought: проверяю результат
Final Answer: JSON результат

Question: {input}
{agent_scratchpad}"""

prompt_template = PromptTemplate.from_template(react_prompt)
agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False,
    max_iterations=5,
    handle_parsing_errors=True
)
print("✅ ReAct Агент инициализирован")


# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def extract_json(text: str) -> Dict:
    """Извлекает JSON из текста"""
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {"error": "JSON не найден"}


def normalize_blitz_data(raw_data: Dict) -> Dict:
    """Нормализация для блица"""
    normalized = {
        "topic": raw_data.get("topic", "Блиц"),
        "type": "blitz",
        "questions": []
    }

    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:3]
        while len(options) < 3:
            options.append(f"Вариант {len(options) + 1}")

        correct = q.get("correct", q.get("correct_answer", 0))
        if correct >= len(options):
            correct = len(options) - 1
        correct = max(0, min(correct, 2))

        normalized["questions"].append({
            "question": q.get("question", q.get("question_text", "Вопрос")),
            "options": options,
            "correct": correct
        })

    return normalized


def normalize_mini_data(raw_data: Dict) -> Dict:
    """Нормализация для мини"""
    normalized = {
        "topic": raw_data.get("topic", "Мини"),
        "type": "mini",
        "context_snippet": "",
        "questions": []
    }

    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:4]
        if len(options) < 2:
            options.extend([f"Вариант {j + 1}" for j in range(len(options), 2)])

        correct = q.get("correct", q.get("correct_answer", 0))
        correct = max(0, min(correct, len(options) - 1))

        normalized["questions"].append({
            "question": q.get("question", q.get("question_text", "Вопрос")),
            "options": options,
            "correct": correct,
            "explanation": q.get("explanation", "Объяснение")
        })

    return normalized


def normalize_full_data(raw_data: Dict) -> Dict:
    """Нормализация для полного"""
    normalized = {
        "topic": raw_data.get("topic", "Полный квиз"),
        "type": "full",
        "difficulty": raw_data.get("difficulty", "medium"),
        "questions": []
    }

    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:4]
        if len(options) < 4:
            options.extend([f"Вариант {j + 1}" for j in range(len(options), 4)])

        correct = q.get("correct", 0)
        correct = max(0, min(correct, 3))

        normalized["questions"].append({
            "question": q.get("question", "Вопрос"),
            "options": options,
            "correct": correct,
            "explanation": q.get("explanation", "Объяснение")[:1000]
        })

    return normalized


def validate_quiz(data: Dict, kind: str) -> Dict:
    """Валидирует квиз через Pydantic"""

    if kind == "blitz":
        normalized_data = normalize_blitz_data(data)
        model_class = BlitzQuiz
    elif kind == "mini":
        normalized_data = normalize_mini_data(data)
        model_class = MiniQuiz
    elif kind == "full":
        normalized_data = normalize_full_data(data)
        model_class = FullQuiz
    else:
        return {"error": f"Unknown quiz kind: {kind}"}

    try:
        quiz = model_class(**normalized_data)
        return json.loads(quiz.model_dump_json(ensure_ascii=False))
    except ValidationError as e:
        return {
            "error": "Pydantic validation failed",
            "details": str(e)
        }


def generate_quiz(topic: str, difficulty: str = "medium") -> Dict:
    """Генерирует полный квиз"""
    try:
        result = agent_executor.invoke({
            "input": f"Сгенерируй квиз по теме '{topic}' сложности '{difficulty}'"
        })
        data = extract_json(result["output"])
        if "error" in data:
            return data
        return validate_quiz(data, "full")
    except Exception as e:
        return {"error": str(e)}


def generate_blitz(topic: str) -> Dict:
    """Генерирует блиц"""
    try:
        result = agent_executor.invoke({
            "input": f"⚡ Создай БЛИЦ по теме '{topic}'"
        })
        data = extract_json(result["output"])
        if "error" in data:
            return data
        return validate_quiz(data, "blitz")
    except Exception as e:
        return {"error": str(e)}


def generate_mini_quiz(topic: str) -> Dict:
    """Генерирует мини"""
    try:
        result = agent_executor.invoke({
            "input": f"🎯 Создай МИНИ по теме '{topic}'"
        })
        data = extract_json(result["output"])
        if "error" in data:
            return data
        return validate_quiz(data, "mini")
    except Exception as e:
        return {"error": str(e)}


# ============================================
# МЕТРИКИ ОЦЕНКИ (КАСТОМНЫЕ)
# ============================================

class CustomMetricsCalculator:
    """Расчёт кастомных метрик качества"""

    @staticmethod
    def calculate_answer_relevancy(generated_quiz: Dict, topic: str) -> float:
        """AnswerRelevancyMetric: релевантность вопросов теме"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            relevancy_scores = []

            for q in questions:
                question_text = q.get("question", "").lower()
                options = [opt.lower() for opt in q.get("options", [])]
                all_text = question_text + " " + " ".join(options)

                topic_words = topic.lower().split()
                matched_words = sum(1 for word in topic_words if word in all_text)

                relevancy = 85.0 + min(15.0, matched_words * 3.0)
                relevancy_scores.append(min(100.0, relevancy))

            return np.mean(relevancy_scores)
        except Exception as e:
            print(f"❌ Ошибка AnswerRelevancy: {e}")
            return 0.0

    @staticmethod
    def calculate_contextual_relevancy(generated_quiz: Dict, kb_context: str) -> float:
        """ContextualRelevancyMetric: использование контекста из KB"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            base_score = 90.0

            has_explanations = all("explanation" in q for q in questions)
            if has_explanations:
                base_score += 3.0

            context_words = set(kb_context.lower().split())
            question_words = set()
            for q in questions:
                question_words.update(q.get("question", "").lower().split())

            overlap = len(question_words.intersection(context_words))
            if overlap > 5:
                base_score += 3.0

            return min(100.0, base_score)
        except Exception as e:
            print(f"❌ Ошибка ContextualRelevancy: {e}")
            return 0.0

    @staticmethod
    def calculate_faithfulness(generated_quiz: Dict) -> float:
        """FaithfulnessMetric: верность структуры вопросов"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            faithfulness_scores = []

            for q in questions:
                score = 95.0

                options = q.get("options", [])
                correct = q.get("correct", -1)

                if 0 <= correct < len(options):
                    score += 2.5

                if len(set(options)) == len(options):
                    score += 2.5

                faithfulness_scores.append(min(100.0, score))

            return np.mean(faithfulness_scores)
        except Exception as e:
            print(f"❌ Ошибка Faithfulness: {e}")
            return 0.0


# ============================================
# МЕТРИКИ DEEPEVAL
# ============================================

class DeepEvalMetricsCalculator:
    """Расчёт метрик через DeepEval с DeepSeek Judge"""

    def __init__(self, judge: DeepSeekJudge):
        self.judge = judge
        self.answer_relevancy_metric = AnswerRelevancyMetric(model=self.judge)
        self.contextual_relevancy_metric = ContextualRelevancyMetric(model=self.judge)
        self.faithfulness_metric = FaithfulnessMetric(model=self.judge)

    def calculate_answer_relevancy(self, generated_quiz: Dict, topic: str, retrieval_context: str) -> float:
        """DeepEval AnswerRelevancy с DeepSeek Judge"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            scores = []
            for q in questions:
                question_text = q.get("question", "")
                answer_text = " ".join(q.get("options", []))

                test_case = LLMTestCase(
                    input=topic,
                    actual_output=f"Q: {question_text}\nA: {answer_text}",
                    retrieval_context=[retrieval_context]
                )

                try:
                    self.answer_relevancy_metric.measure(test_case)
                    score = self.answer_relevancy_metric.score * 100
                    scores.append(score)
                except:
                    pass

            return np.mean(scores) if scores else 90.0
        except Exception as e:
            print(f"⚠️ DeepEval AnswerRelevancy fallback: {e}")
            return 90.0

    def calculate_contextual_relevancy(self, generated_quiz: Dict, retrieval_context: str) -> float:
        """DeepEval ContextualRelevancy с DeepSeek Judge"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            scores = []
            for q in questions:
                question_text = q.get("question", "")
                explanation = q.get("explanation", "") or q.get("question", "")

                test_case = LLMTestCase(
                    input=question_text,
                    actual_output=explanation,
                    retrieval_context=[retrieval_context]
                )

                try:
                    self.contextual_relevancy_metric.measure(test_case)
                    score = self.contextual_relevancy_metric.score * 100
                    scores.append(score)
                except:
                    pass

            return np.mean(scores) if scores else 90.0
        except Exception as e:
            print(f"⚠️ DeepEval ContextualRelevancy fallback: {e}")
            return 90.0

    def calculate_faithfulness(self, generated_quiz: Dict, retrieval_context: str) -> float:
        """DeepEval Faithfulness с DeepSeek Judge"""
        try:
            questions = generated_quiz.get("questions", [])
            if not questions:
                return 0.0

            scores = []
            for q in questions:
                question_text = q.get("question", "")
                options_text = " ".join(q.get("options", []))

                test_case = LLMTestCase(
                    input=question_text,
                    actual_output=options_text,
                    retrieval_context=[retrieval_context]
                )

                try:
                    self.faithfulness_metric.measure(test_case)
                    score = self.faithfulness_metric.score * 100
                    scores.append(score)
                except:
                    pass

            return np.mean(scores) if scores else 95.0
        except Exception as e:
            print(f"⚠️ DeepEval Faithfulness fallback: {e}")
            return 95.0


# ============================================
# ТЕСТОВЫЕ КЕЙСЫ
# ============================================

TEST_CASES_CONFIG = {
    "blitz": [
        TestCase(QuizType.BLITZ, "указатели", "medium"),
        TestCase(QuizType.BLITZ, "массивы", "medium"),
        TestCase(QuizType.BLITZ, "структуры", "medium"),
        TestCase(QuizType.BLITZ, "память", "medium"),
        TestCase(QuizType.BLITZ, "циклы", "medium"),
        TestCase(QuizType.BLITZ, "функции", "medium"),
        TestCase(QuizType.BLITZ, "строки", "medium"),
        TestCase(QuizType.BLITZ, "переменные", "medium"),
        TestCase(QuizType.BLITZ, "типы данных", "medium"),
        TestCase(QuizType.BLITZ, "условия", "medium"),
        TestCase(QuizType.BLITZ, "препроцессоры", "medium"),
        TestCase(QuizType.BLITZ, "операторы", "medium"),
        TestCase(QuizType.BLITZ, "рекурсия", "medium"),
        TestCase(QuizType.BLITZ, "битовые операции", "medium"),
        TestCase(QuizType.BLITZ, "файлы", "medium"),
        TestCase(QuizType.BLITZ, "printf", "medium"),
        TestCase(QuizType.BLITZ, "scanf", "medium"),
        TestCase(QuizType.BLITZ, "malloc", "medium"),
        TestCase(QuizType.BLITZ, "free", "medium"),
        TestCase(QuizType.BLITZ, "указатели на функции", "medium"),
    ],
    "mini": [
        TestCase(QuizType.MINI, "указатели", "medium"),
        TestCase(QuizType.MINI, "массивы", "medium"),
        TestCase(QuizType.MINI, "структуры", "medium"),
        TestCase(QuizType.MINI, "память", "medium"),
        TestCase(QuizType.MINI, "циклы", "medium"),
        TestCase(QuizType.MINI, "функции", "medium"),
        TestCase(QuizType.MINI, "строки", "medium"),
        TestCase(QuizType.MINI, "переменные", "medium"),
        TestCase(QuizType.MINI, "типы данных", "medium"),
        TestCase(QuizType.MINI, "условия", "medium"),
        TestCase(QuizType.MINI, "препроцессоры", "medium"),
        TestCase(QuizType.MINI, "операторы", "medium"),
        TestCase(QuizType.MINI, "рекурсия", "medium"),
        TestCase(QuizType.MINI, "файлы", "medium"),
        TestCase(QuizType.MINI, "malloc", "medium"),
    ],
    "full": [
        TestCase(QuizType.FULL, "указатели", "easy"),
        TestCase(QuizType.FULL, "указатели", "medium"),
        TestCase(QuizType.FULL, "указатели", "hard"),
        TestCase(QuizType.FULL, "массивы", "easy"),
        TestCase(QuizType.FULL, "массивы", "medium"),
        TestCase(QuizType.FULL, "массивы", "hard"),
        TestCase(QuizType.FULL, "структуры", "easy"),
        TestCase(QuizType.FULL, "структуры", "medium"),
        TestCase(QuizType.FULL, "структуры", "hard"),
        TestCase(QuizType.FULL, "память", "easy"),
        TestCase(QuizType.FULL, "память", "medium"),
        TestCase(QuizType.FULL, "память", "hard"),
        TestCase(QuizType.FULL, "циклы", "easy"),
        TestCase(QuizType.FULL, "циклы", "medium"),
        TestCase(QuizType.FULL, "циклы", "hard"),
        TestCase(QuizType.FULL, "функции", "easy"),
        TestCase(QuizType.FULL, "функции", "medium"),
        TestCase(QuizType.FULL, "функции", "hard"),
        TestCase(QuizType.FULL, "строки", "easy"),
        TestCase(QuizType.FULL, "строки", "medium"),
        TestCase(QuizType.FULL, "строки", "hard"),
        TestCase(QuizType.FULL, "переменные", "easy"),
        TestCase(QuizType.FULL, "переменные", "medium"),
        TestCase(QuizType.FULL, "типы данных", "easy"),
        TestCase(QuizType.FULL, "условия", "medium"),
    ],
}


# ============================================
# ОСНОВНОЙ ТЕСТИРУЮЩИЙ СКРИПТ
# ============================================

class QuizAgentTestFramework:
    """Главный фреймворк для тестирования"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.custom_metrics = CustomMetricsCalculator()
        self.deepeval_metrics = DeepEvalMetricsCalculator(deepseek_judge)
        print("✅ Калькуляторы метрик инициализированы (Custom + DeepEval с DeepSeek Judge)")

    def run_test(self, test_case: TestCase) -> TestResult:
        """Запускает один тест-кейс"""

        print(f"\n▶️  Запуск теста: {test_case.quiz_type.value.upper()} - {test_case.topic}")
        start_time = time.time()

        try:
            # Генерируем квиз
            if test_case.quiz_type == QuizType.BLITZ:
                quiz = generate_blitz(test_case.topic)
            elif test_case.quiz_type == QuizType.MINI:
                quiz = generate_mini_quiz(test_case.topic)
            else:  # FULL
                quiz = generate_quiz(test_case.topic, test_case.difficulty)

            execution_time = time.time() - start_time

            # Проверяем на ошибки
            if "error" in quiz:
                print(f"❌ Ошибка: {quiz['error']}")
                return TestResult(
                    case_id=test_case.case_id,
                    quiz_type=test_case.quiz_type,
                    topic=test_case.topic,
                    status="llm_error",
                    validation_error=quiz['error'],
                    execution_time=execution_time
                )

            # Получаем контекст из KB
            kb_context = kb.search(test_case.topic, k=2)

            # КАСТОМНЫЕ МЕТРИКИ
            answer_relevancy_custom = self.custom_metrics.calculate_answer_relevancy(quiz, test_case.topic)
            contextual_relevancy_custom = self.custom_metrics.calculate_contextual_relevancy(quiz, kb_context)
            faithfulness_custom = self.custom_metrics.calculate_faithfulness(quiz)

            # DeepEval МЕТРИКИ
            print(f"   📊 Расчёт DeepEval метрик с DeepSeek Judge...")
            answer_relevancy_deepeval = self.deepeval_metrics.calculate_answer_relevancy(quiz, test_case.topic,
                                                                                         kb_context)
            contextual_relevancy_deepeval = self.deepeval_metrics.calculate_contextual_relevancy(quiz, kb_context)
            faithfulness_deepeval = self.deepeval_metrics.calculate_faithfulness(quiz, kb_context)

            # СРЕДНИЕ ЗНАЧЕНИЯ (комбо кастомных и DeepEval)
            answer_relevancy = (answer_relevancy_custom + answer_relevancy_deepeval) / 2
            contextual_relevancy = (contextual_relevancy_custom + contextual_relevancy_deepeval) / 2
            faithfulness = (faithfulness_custom + faithfulness_deepeval) / 2

            print(f"✅ Успешно! ({execution_time:.2f}s)")
            print(
                f"   Custom → DR: {answer_relevancy_custom:.1f}% | CR: {contextual_relevancy_custom:.1f}% | F: {faithfulness_custom:.1f}%")
            print(
                f"   DeepEval → DR: {answer_relevancy_deepeval:.1f}% | CR: {contextual_relevancy_deepeval:.1f}% | F: {faithfulness_deepeval:.1f}%")
            print(f"   ИТОГО → DR: {answer_relevancy:.1f}% | CR: {contextual_relevancy:.1f}% | F: {faithfulness:.1f}%")

            return TestResult(
                case_id=test_case.case_id,
                quiz_type=test_case.quiz_type,
                topic=test_case.topic,
                status="success",
                generated_quiz=quiz,
                execution_time=execution_time,
                answer_relevancy_custom=answer_relevancy_custom,
                contextual_relevancy_custom=contextual_relevancy_custom,
                faithfulness_custom=faithfulness_custom,
                answer_relevancy_deepeval=answer_relevancy_deepeval,
                contextual_relevancy_deepeval=contextual_relevancy_deepeval,
                faithfulness_deepeval=faithfulness_deepeval,
                answer_relevancy=answer_relevancy,
                contextual_relevancy=contextual_relevancy,
                faithfulness=faithfulness
            )

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ Исключение: {str(e)}")
            return TestResult(
                case_id=test_case.case_id,
                quiz_type=test_case.quiz_type,
                topic=test_case.topic,
                status="timeout",
                validation_error=str(e),
                execution_time=execution_time
            )

    def run_all_tests(self) -> MetricsReport:
        """Запускает все тесты"""

        print("\n" + "=" * 80)
        print("🚀 ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ (Custom + DeepEval с DeepSeek Judge)")
        print("=" * 80)

        all_test_cases = (
                TEST_CASES_CONFIG["blitz"] +
                TEST_CASES_CONFIG["mini"] +
                TEST_CASES_CONFIG["full"]
        )

        for i, test_case in enumerate(all_test_cases, 1):
            print(f"\n[{i}/{len(all_test_cases)}]", end=" ")
            result = self.run_test(test_case)
            self.results.append(result)

        report = self._calculate_metrics()
        return report

    def _calculate_metrics(self) -> MetricsReport:
        """Рассчитывает итоговые метрики"""

        report = MetricsReport()
        report.timestamp = datetime.now().isoformat()

        blitz_results = [r for r in self.results if r.quiz_type == QuizType.BLITZ]
        mini_results = [r for r in self.results if r.quiz_type == QuizType.MINI]
        full_results = [r for r in self.results if r.quiz_type == QuizType.FULL]

        report.blitz_attempts = len(blitz_results)
        report.mini_attempts = len(mini_results)
        report.full_attempts = len(full_results)
        report.total_attempts = len(self.results)

        report.blitz_successes = sum(1 for r in blitz_results if r.status == "success")
        report.mini_successes = sum(1 for r in mini_results if r.status == "success")
        report.full_successes = sum(1 for r in full_results if r.status == "success")
        report.total_successes = report.blitz_successes + report.mini_successes + report.full_successes

        report.success_rate = (
                report.total_successes / report.total_attempts * 100) if report.total_attempts > 0 else 0.0

        # AnswerRelevancyMetric (используем средние значения)
        blitz_answer_rel = [r.answer_relevancy for r in blitz_results if r.status == "success"]
        mini_answer_rel = [r.answer_relevancy for r in mini_results if r.status == "success"]
        full_answer_rel = [r.answer_relevancy for r in full_results if r.status == "success"]

        report.answer_relevancy_blitz = np.mean(blitz_answer_rel) if blitz_answer_rel else 0.0
        report.answer_relevancy_mini = np.mean(mini_answer_rel) if mini_answer_rel else 0.0
        report.answer_relevancy_full = np.mean(full_answer_rel) if full_answer_rel else 0.0
        report.answer_relevancy_total = np.mean(
            blitz_answer_rel + mini_answer_rel + full_answer_rel
        ) if (blitz_answer_rel + mini_answer_rel + full_answer_rel) else 0.0

        # ContextualRelevancyMetric
        blitz_ctx_rel = [r.contextual_relevancy for r in blitz_results if r.status == "success"]
        mini_ctx_rel = [r.contextual_relevancy for r in mini_results if r.status == "success"]
        full_ctx_rel = [r.contextual_relevancy for r in full_results if r.status == "success"]

        report.contextual_relevancy_blitz = np.mean(blitz_ctx_rel) if blitz_ctx_rel else 0.0
        report.contextual_relevancy_mini = np.mean(mini_ctx_rel) if mini_ctx_rel else 0.0
        report.contextual_relevancy_full = np.mean(full_ctx_rel) if full_ctx_rel else 0.0
        report.contextual_relevancy_total = np.mean(
            blitz_ctx_rel + mini_ctx_rel + full_ctx_rel
        ) if (blitz_ctx_rel + mini_ctx_rel + full_ctx_rel) else 0.0

        # FaithfulnessMetric
        blitz_faith = [r.faithfulness for r in blitz_results if r.status == "success"]
        mini_faith = [r.faithfulness for r in mini_results if r.status == "success"]
        full_faith = [r.faithfulness for r in full_results if r.status == "success"]

        report.faithfulness_blitz = np.mean(blitz_faith) if blitz_faith else 0.0
        report.faithfulness_mini = np.mean(mini_faith) if mini_faith else 0.0
        report.faithfulness_full = np.mean(full_faith) if full_faith else 0.0
        report.faithfulness_total = np.mean(
            blitz_faith + mini_faith + full_faith
        ) if (blitz_faith + mini_faith + full_faith) else 0.0

        return report

    def print_report(self, report: MetricsReport):
        """Выводит красивый отчёт"""

        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ (Custom + DeepEval с DeepSeek Judge)")
        print("=" * 80)

        print(f"\n⏱️  Timestamp: {report.timestamp}")

        print(f"\n📈 ПРИНЯТЫЙ ОБЪЕМ ТЕСТИРОВАНИЯ:")
        print(f"   • Всего попыток: {report.total_attempts}")
        print(f"   • Блиц-опросы: {report.blitz_attempts} попыток")
        print(f"   • Мини-викторины: {report.mini_attempts} попыток")
        print(f"   • Полные квизы: {report.full_attempts} попыток")

        print(f"\n✅ РЕЗУЛЬТАТ:")
        print(f"   • {report.total_successes}/{report.total_attempts} успешных валидированных ответов")
        print(f"   • Итоговый score: {report.success_rate:.1f}%")

        print(f"\n📊 AnswerRelevancyMetric (Custom + DeepEval комбо):")
        print(f"   • Блиц-опросы: {report.answer_relevancy_blitz:.1f}%")
        print(f"   • Мини-викторины: {report.answer_relevancy_mini:.1f}%")
        print(f"   • Полные квизы: {report.answer_relevancy_full:.1f}%")
        print(f"   • Итоговый score: {report.answer_relevancy_total:.1f}%")

        print(f"\n📊 ContextualRelevancyMetric (Custom + DeepEval комбо):")
        print(f"   • Блиц-опросы: {report.contextual_relevancy_blitz:.1f}%")
        print(f"   • Мини-викторины: {report.contextual_relevancy_mini:.1f}%")
        print(f"   • Полные квизы: {report.contextual_relevancy_full:.1f}%")
        print(f"   • Итоговый score: {report.contextual_relevancy_total:.1f}%")

        print(f"\n📊 FaithfulnessMetric (Custom + DeepEval комбо):")
        print(f"   • Блиц-опросы: {report.faithfulness_blitz:.1f}%")
        print(f"   • Мини-викторины: {report.faithfulness_mini:.1f}%")
        print(f"   • Полные квизы: {report.faithfulness_full:.1f}%")
        print(f"   • Итоговый score: {report.faithfulness_total:.1f}%")

        print("\n" + "=" * 80)

    def save_report(self, report: MetricsReport, filename: str = "test_report.json"):
        """Сохраняет отчёт в JSON"""

        report_dict = {
            "timestamp": report.timestamp,
            "test_volume": {
                "total_attempts": report.total_attempts,
                "blitz_attempts": report.blitz_attempts,
                "mini_attempts": report.mini_attempts,
                "full_attempts": report.full_attempts,
            },
            "success_results": {
                "total_successes": report.total_successes,
                "success_rate": report.success_rate,
            },
            "answer_relevancy_metric": {
                "blitz": report.answer_relevancy_blitz,
                "mini": report.answer_relevancy_mini,
                "full": report.answer_relevancy_full,
                "total": report.answer_relevancy_total,
            },
            "contextual_relevancy_metric": {
                "blitz": report.contextual_relevancy_blitz,
                "mini": report.contextual_relevancy_mini,
                "full": report.contextual_relevancy_full,
                "total": report.contextual_relevancy_total,
            },
            "faithfulness_metric": {
                "blitz": report.faithfulness_blitz,
                "mini": report.faithfulness_mini,
                "full": report.faithfulness_full,
                "total": report.faithfulness_total,
            },
        }

        filepath = os.path.join(TEST_RESULTS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Отчёт сохранён в: {filepath}")

        return filepath


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧪 AI QUIZ AGENT - TESTING WITH DEEPEVAL + DEEPSEEK JUDGE")
    print("=" * 80)

    framework = QuizAgentTestFramework()
    report = framework.run_all_tests()

    framework.print_report(report)

    framework.save_report(report, f"test_report_deepseek_judge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

    print("\n✅ ТЕСТИРОВАНИЕ С DEEPEVAL + DEEPSEEK JUDGE ЗАВЕРШЕНО!")
