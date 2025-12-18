# ============================================
# КВИЗ-ТЕСТЕР: Система тестирования квизов
# Проверяет 60 квизов (20 блиц + 15 мини + 25 полных)
# с метриками корректности JSON и качества
# ============================================

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import tool

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter

load_dotenv()

# ============================================
# КОНФИГУРАЦИЯ
# ============================================
os.environ["DEEPSEEK_API_KEY"] = "sk-2e4ea2a8435d4d54b3dbe83f7359dd2c"
TEST_RESULTS_DIR = "./test_results"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)


# ============================================
# ENUMS И DATACLASS'Ы
# ============================================

class QuizType(Enum):
    BLITZ = "blitz"
    MINI = "mini"
    FULL = "full"


@dataclass
class TestCase:
    quiz_type: QuizType
    topic: str
    difficulty: str = "medium"
    case_id: str = ""

    def __post_init__(self):
        if not self.case_id:
            self.case_id = f"{self.quiz_type.value}_{self.topic}_{int(time.time() * 1000) % 100000}"


@dataclass
class TestResult:
    case_id: str
    quiz_type: QuizType
    topic: str
    status: str  # "success", "validation_error", "llm_error"
    generated_quiz: Dict = field(default_factory=dict)
    validation_error: str = ""
    execution_time: float = 0.0

    # Метрики
    json_correctness: float = 0.0
    structure_validity: float = 0.0
    content_quality: float = 0.0


@dataclass
class MetricsReport:
    total_attempts: int = 0
    total_successes: int = 0
    blitz_attempts: int = 0
    blitz_successes: int = 0
    mini_attempts: int = 0
    mini_successes: int = 0
    full_attempts: int = 0
    full_successes: int = 0

    json_correctness_avg: float = 0.0
    structure_validity_avg: float = 0.0
    content_quality_avg: float = 0.0

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

# ============================================
# KNOWLEDGE BASE (ТОЛЬКО ФАЙЛЫ, БЕЗ СЕМАНТИКИ)
# ============================================

class KnowledgeBase:
    """
    Загружает .txt файлы из папки knowledge/ рядом со скриптом и
    возвращает общий текст (или первые N символов).
    Без embeddings / FAISS / semantic search.
    """

    def __init__(self, knowledge_dir: str = "knowledge"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.knowledge_path = os.path.join(script_dir, knowledge_dir)
        self.docs: List[str] = []
        self.sources: List[str] = []
        self._load_files()

    def _load_files(self):
        if not os.path.exists(self.knowledge_path):
            raise FileNotFoundError(f"Папка knowledge/ не найдена: {self.knowledge_path}")

        loader = DirectoryLoader(
            self.knowledge_path,
            glob="*.txt",
            loader_cls=TextLoader,
            show_progress=False,
        )
        file_docs = loader.load()  # список Document
        if not file_docs:
            raise FileNotFoundError(f"В knowledge/ нет .txt файлов: {self.knowledge_path}")

        self.docs = [d.page_content for d in file_docs]
        self.sources = [d.metadata.get("source", "") for d in file_docs]
        print(f"✅ KnowledgeBase: загружено файлов: {len(self.docs)}")

    def get_context(self, limit_chars: int = 6000) -> str:
        """
        Возвращает один большой контекст, склеивая все файлы.
        limit_chars — чтобы не улететь в контекст/токены.
        """
        combined = "\n\n---\n\n".join(self.docs)
        return combined[:limit_chars]

    def debug_sources(self) -> List[str]:
        return self.sources


# ============================================
# LLM ИНИЦИАЛИЗАЦИЯ
# ============================================

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.3,
    max_tokens=4096,
    api_key=os.environ.get("DEEPSEEK_API_KEY")
)
print("✅ LLM инициализирована")

kb = KnowledgeBase()


# ============================================
# TOOLS
# ============================================

@tool
def get_c_knowledge(query: str) -> str:
    """Retrieve knowledge from the RAG system."""
    return kb.search(query, k=3)


# ============================================
# TOOLS (ТОЛЬКО knowledge/, БЕЗ retriever/search)
# ============================================

@tool(return_direct=True)
def get_c_knowledge(query: str) -> str:
    """Return raw knowledge base text (no semantic search)."""
    return kb.get_context(limit_chars=6000)

@tool(return_direct=True)
def create_blitz_quiz(topic: str) -> str:
    """Create a blitz quiz (3 options, correct 0-2)."""
    try:
        context = kb.get_context(limit_chars=6000)
        prompt = f"""Ты генератор блиц-вопросов по C.

Контекст:
{context}

Сгенерируй JSON блиц-опрос по теме "{topic}". Требования:
- 5 вопросов
- 3 варианта ответа на каждый
- correct = число от 0 до 2
Верни ТОЛЬКО валидный JSON строго в формате:
{{
  "topic": "{topic}",
  "type": "blitz",
  "questions": [
    {{
      "question": "string",
      "options": ["string","string","string"],
      "correct": 0
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            return json.dumps({"error": "JSON not found", "raw": text[:200]}, ensure_ascii=False)
        return text[start:end]
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool(return_direct=True)
def create_mini_quiz(topic: str) -> str:
    """Create a mini quiz (2-4 options + explanation)."""
    try:
        context = kb.get_context(limit_chars=6000)
        prompt = f"""Ты генератор мини-викторин по C.

Контекст:
{context}

Сгенерируй JSON мини-викторину по теме "{topic}". Требования:
- 7 вопросов
- 2-4 варианта ответа
- correct = индекс правильного варианта
- explanation = пояснение
Верни ТОЛЬКО валидный JSON строго в формате:
{{
  "topic": "{topic}",
  "type": "mini",
  "context_snippet": "",
  "questions": [
    {{
      "question": "string",
      "options": ["string","string"],
      "correct": 0,
      "explanation": "string"
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            return json.dumps({"error": "JSON not found", "raw": text[:200]}, ensure_ascii=False)
        return text[start:end]
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@tool(return_direct=True)
def create_full_quiz(topic: str, difficulty: str = "medium") -> str:
    """Create a full quiz (4 options + explanation)."""
    try:
        context = kb.get_context(limit_chars=6000)
        question_count = {"easy": 5, "medium": 7, "hard": 10}.get(difficulty.lower(), 7)

        prompt = f"""Ты генератор образовательных квизов по языку C.

Контекст:
{context}

Сгенерируй полный квиз по теме "{topic}" сложности "{difficulty}":
- {question_count} вопросов
- 4 варианта ответа
- correct = индекс 0..3
- explanation = 2-3 предложения
Верни ТОЛЬКО валидный JSON строго в формате:
{{
  "topic": "{topic}",
  "type": "full",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "string",
      "options": ["string","string","string","string"],
      "correct": 0,
      "explanation": "string"
    }}
  ]
}}
"""
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            return json.dumps({"error": "JSON not found", "raw": text[:200]}, ensure_ascii=False)
        return text[start:end]
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)



tools = [get_c_knowledge, create_blitz_quiz, create_mini_quiz, create_full_quiz]
print("✅ Tools готовы")

# ============================================
# REACT АГЕНТ
# ============================================
# ============================================
# REACT АГЕНТ
# ============================================

react_prompt = """Ты JSON-генератор квизов по C. Всегда используй инструменты.

{tools}

Доступные инструменты: {tool_names}

Формат ответа:
Question: {input}
Thought: что нужно сделать
Action: название_инструмента
Action Input: параметры
Observation: результат
Thought: проверяю результат
Final Answer: JSON результат

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""

prompt_template = PromptTemplate(
    template=react_prompt,
    input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
)

agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
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
        except:
            pass
    return {}


def normalize_blitz_data(raw_data: Dict) -> Dict:
    normalized = {
        "topic": raw_data.get("topic", "Topic"),
        "type": "blitz",
        "questions": []
    }
    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:3]
        while len(options) < 3:
            options.append(f"Opt{len(options) + 1}")
        correct = max(0, min(q.get("correct", 0), 2))
        normalized["questions"].append({
            "question": q.get("question", "Q?"),
            "options": options,
            "correct": correct
        })
    return normalized


def normalize_mini_data(raw_data: Dict) -> Dict:
    normalized = {
        "topic": raw_data.get("topic", "Topic"),
        "type": "mini",
        "context_snippet": "",
        "questions": []
    }
    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:4]
        if len(options) < 2:
            options.extend([f"Opt{j + 1}" for j in range(len(options), 2)])
        correct = max(0, min(q.get("correct", 0), len(options) - 1))
        normalized["questions"].append({
            "question": q.get("question", "Q?"),
            "options": options,
            "correct": correct,
            "explanation": q.get("explanation", "Reason")
        })
    return normalized


def normalize_full_data(raw_data: Dict) -> Dict:
    normalized = {
        "topic": raw_data.get("topic", "Topic"),
        "type": "full",
        "difficulty": raw_data.get("difficulty", "medium"),
        "questions": []
    }
    for q in raw_data.get("questions", []):
        options = q.get("options", [])[:4]
        if len(options) < 4:
            options.extend([f"Opt{j + 1}" for j in range(len(options), 4)])
        correct = max(0, min(q.get("correct", 0), 3))
        normalized["questions"].append({
            "question": q.get("question", "Q?"),
            "options": options,
            "correct": correct,
            "explanation": q.get("explanation", "Reason")[:1000]
        })
    return normalized


def validate_quiz(data: Dict, kind: str) -> Dict:
    """Валидирует через Pydantic"""
    if kind == "blitz":
        normalized = normalize_blitz_data(data)
        model_class = BlitzQuiz
    elif kind == "mini":
        normalized = normalize_mini_data(data)
        model_class = MiniQuiz
    elif kind == "full":
        normalized = normalize_full_data(data)
        model_class = FullQuiz
    else:
        return {}

    try:
        quiz = model_class(**normalized)
        return json.loads(quiz.model_dump_json(ensure_ascii=False))
    except ValidationError:
        return {}


def generate_blitz(topic: str) -> Dict:
    try:
        result = agent_executor.invoke({"input": f"Создай БЛИЦ по '{topic}'"})
        raw = (result.get("output") or "").strip()
        data = extract_json(raw)

        if not data:
            raw_tool = create_blitz_quiz.invoke({"topic": topic})
            data = extract_json(raw_tool)

        return validate_quiz(data, "blitz") if data else {}
    except:
        try:
            raw_tool = create_blitz_quiz.invoke({"topic": topic})
            data = extract_json(raw_tool)
            return validate_quiz(data, "blitz") if data else {}
        except:
            return {}

def generate_mini(topic: str) -> Dict:
    try:
        result = agent_executor.invoke({"input": f"Создай МИНИ по '{topic}'"})
        raw = (result.get("output") or "").strip()
        data = extract_json(raw)

        if not data:
            raw_tool = create_mini_quiz.invoke({"topic": topic})
            data = extract_json(raw_tool)

        return validate_quiz(data, "mini") if data else {}
    except:
        try:
            raw_tool = create_mini_quiz.invoke({"topic": topic})
            data = extract_json(raw_tool)
            return validate_quiz(data, "mini") if data else {}
        except:
            return {}

def generate_full(topic: str, difficulty: str = "medium") -> Dict:
    try:
        result = agent_executor.invoke({"input": f"Создай КВИЗ по '{topic}' сложности '{difficulty}'"})
        raw = (result.get("output") or "").strip()
        data = extract_json(raw)

        if not data:
            raw_tool = create_full_quiz.invoke({"topic": topic, "difficulty": difficulty})
            data = extract_json(raw_tool)

        return validate_quiz(data, "full") if data else {}
    except:
        try:
            raw_tool = create_full_quiz.invoke({"topic": topic, "difficulty": difficulty})
            data = extract_json(raw_tool)
            return validate_quiz(data, "full") if data else {}
        except:
            return {}

# ============================================
# МЕТРИКИ
# ============================================

class JsonCorrectnessMetric:
    """Проверяет корректность JSON структуры квиза"""

    @staticmethod
    def measure(quiz: Dict, quiz_type: str) -> float:
        """Возвращает оценку 0-100"""
        if not quiz or "error" in quiz:
            return 0.0

        score = 100.0

        # Проверка обязательных полей
        if "topic" not in quiz:
            score -= 10
        if "type" not in quiz:
            score -= 10
        if quiz.get("type") != quiz_type:
            score -= 15

        # Проверка вопросов
        questions = quiz.get("questions", [])
        if not questions:
            return 0.0

        # Минимальное и максимальное количество вопросов
        if quiz_type == "blitz":
            if len(questions) < 3 or len(questions) > 5:
                score -= 20
        elif quiz_type == "mini":
            if len(questions) < 3 or len(questions) > 7:
                score -= 20
        elif quiz_type == "full":
            if len(questions) < 5 or len(questions) > 10:
                score -= 20

        # Проверка структуры вопросов
        issues_per_question = 0
        for q in questions:
            q_score = 0
            if "question" not in q:
                q_score -= 5
            if "options" not in q:
                q_score -= 10
            elif not isinstance(q["options"], list):
                q_score -= 10
            else:
                expected_options = {"blitz": 3, "mini": 2, "full": 4}.get(quiz_type, 4)
                if len(q["options"]) < 2 or len(q["options"]) > expected_options + 1:
                    q_score -= 5

            if "correct" not in q:
                q_score -= 10
            elif not isinstance(q["correct"], int) or q["correct"] < 0:
                q_score -= 5

            if quiz_type in ["mini", "full"] and "explanation" not in q:
                q_score -= 5

            if q_score < 0:
                issues_per_question += 1

        if issues_per_question > 0:
            score -= min(15, issues_per_question * 3)

        return max(0.0, score)


class StructureValidityMetric:
    """Проверяет валидность структуры через Pydantic"""

    @staticmethod
    def measure(quiz: Dict, quiz_type: str) -> float:
        if not quiz or "error" in quiz:
            return 0.0

        try:
            if quiz_type == "blitz":
                BlitzQuiz(**quiz)
            elif quiz_type == "mini":
                MiniQuiz(**quiz)
            elif quiz_type == "full":
                FullQuiz(**quiz)
            return 100.0
        except ValidationError:
            return 50.0
        except:
            return 0.0


class ContentQualityMetric:
    """Проверяет качество контента"""

    @staticmethod
    def measure(quiz: Dict, topic: str) -> float:
        if not quiz or "error" in quiz:
            return 0.0

        score = 80.0
        questions = quiz.get("questions", [])

        for q in questions:
            question_text = q.get("question", "").lower()

            # Проверяем релевантность теме
            topic_words = topic.lower().split()
            if any(word in question_text for word in topic_words):
                score += 5

            # Проверяем длину вопроса
            if len(q.get("question", "")) < 5:
                score -= 2

            # Проверяем варианты ответов
            options = q.get("options", [])
            if len(set(options)) < len(options):
                score -= 3

            for opt in options:
                if len(opt) < 2:
                    score -= 2

        return min(100.0, max(0.0, score))


# ============================================
# ТЕСТОВЫЙ ФРЕЙМВОРК
# ============================================

TEST_CASES_CONFIG = {
    "blitz": [
        TestCase(QuizType.BLITZ, "указатели"),
        TestCase(QuizType.BLITZ, "массивы"),
        TestCase(QuizType.BLITZ, "структуры"),
        TestCase(QuizType.BLITZ, "память"),
        TestCase(QuizType.BLITZ, "циклы"),
        TestCase(QuizType.BLITZ, "функции"),
        TestCase(QuizType.BLITZ, "строки"),
        TestCase(QuizType.BLITZ, "переменные"),
        TestCase(QuizType.BLITZ, "типы данных"),
        TestCase(QuizType.BLITZ, "условия"),
        TestCase(QuizType.BLITZ, "препроцессоры"),
        TestCase(QuizType.BLITZ, "операторы"),
        TestCase(QuizType.BLITZ, "рекурсия"),
        TestCase(QuizType.BLITZ, "битовые операции"),
        TestCase(QuizType.BLITZ, "файлы"),
        TestCase(QuizType.BLITZ, "printf"),
        TestCase(QuizType.BLITZ, "scanf"),
        TestCase(QuizType.BLITZ, "malloc"),
        TestCase(QuizType.BLITZ, "free"),
        TestCase(QuizType.BLITZ, "указатели на функции"),
    ],
    "mini": [
        TestCase(QuizType.MINI, "указатели"),
        TestCase(QuizType.MINI, "массивы"),
        TestCase(QuizType.MINI, "структуры"),
        TestCase(QuizType.MINI, "память"),
        TestCase(QuizType.MINI, "циклы"),
        TestCase(QuizType.MINI, "функции"),
        TestCase(QuizType.MINI, "строки"),
        TestCase(QuizType.MINI, "переменные"),
        TestCase(QuizType.MINI, "типы данных"),
        TestCase(QuizType.MINI, "условия"),
        TestCase(QuizType.MINI, "препроцессоры"),
        TestCase(QuizType.MINI, "операторы"),
        TestCase(QuizType.MINI, "рекурсия"),
        TestCase(QuizType.MINI, "файлы"),
        TestCase(QuizType.MINI, "malloc"),
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


class QuizTestFramework:
    """Главный фреймворк тестирования"""

    def __init__(self):
        self.results: List[TestResult] = []
        self.json_metric = JsonCorrectnessMetric()
        self.structure_metric = StructureValidityMetric()
        self.quality_metric = ContentQualityMetric()
        print("✅ Тестовый фреймворк инициализирован")

    def run_test(self, test_case: TestCase) -> TestResult:
        """Запускает один тест"""
        start_time = time.time()

        try:
            if test_case.quiz_type == QuizType.BLITZ:
                quiz = generate_blitz(test_case.topic)
            elif test_case.quiz_type == QuizType.MINI:
                quiz = generate_mini(test_case.topic)
            else:
                quiz = generate_full(test_case.topic, test_case.difficulty)

            execution_time = time.time() - start_time

            if not quiz or "error" in quiz:
                return TestResult(
                    case_id=test_case.case_id,
                    quiz_type=test_case.quiz_type,
                    topic=test_case.topic,
                    status="llm_error",
                    validation_error=quiz.get("error", "Unknown error") if quiz else "Empty response",
                    execution_time=execution_time
                )

            json_score = self.json_metric.measure(quiz, test_case.quiz_type.value)
            structure_score = self.structure_metric.measure(quiz, test_case.quiz_type.value)
            quality_score = self.quality_metric.measure(quiz, test_case.topic)

            status = "success" if json_score > 70 and structure_score > 50 else "validation_error"

            return TestResult(
                case_id=test_case.case_id,
                quiz_type=test_case.quiz_type,
                topic=test_case.topic,
                status=status,
                generated_quiz=quiz,
                execution_time=execution_time,
                json_correctness=json_score,
                structure_validity=structure_score,
                content_quality=quality_score
            )

        except Exception as e:
            return TestResult(
                case_id=test_case.case_id,
                quiz_type=test_case.quiz_type,
                topic=test_case.topic,
                status="llm_error",
                validation_error=str(e),
                execution_time=time.time() - start_time
            )

    def run_all_tests(self) -> MetricsReport:
        """Запускает все 60 тестов"""
        print("\n" + "=" * 80)
        print("🚀 ЗАПУСК ПОЛНОГО НАБОРА ТЕСТОВ (60 тестов)")
        print("=" * 80)

        # Собираем ровно 60 тестов: 20 + 15 + 25
        blitz_cases = TEST_CASES_CONFIG["blitz"][:20]
        mini_cases = TEST_CASES_CONFIG["mini"][:15]
        full_cases = TEST_CASES_CONFIG["full"][:25]

        all_test_cases = blitz_cases + mini_cases + full_cases
        assert len(all_test_cases) == 60, f"Expected 60 tests, got {len(all_test_cases)}"

        for i, test_case in enumerate(all_test_cases, 1):
            print(
                f"\n[{i}/{len(all_test_cases)}] ▶️  Запуск теста: {test_case.quiz_type.value.upper()} - {test_case.topic}")
            result = self.run_test(test_case)
            self.results.append(result)

            if result.status == "success":
                print(
                    f"✅ Успешно! JSON: {result.json_correctness:.1f}% | Структура: {result.structure_validity:.1f}% | Качество: {result.content_quality:.1f}%")
            else:
                print(f"❌ Ошибка: {result.validation_error[:80]}")

        report = self._calculate_metrics()
        return report

    def _calculate_metrics(self) -> MetricsReport:
        """Рассчитывает метрики"""
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

        successful_results = [r for r in self.results if r.status == "success"]
        if successful_results:
            report.json_correctness_avg = np.mean([r.json_correctness for r in successful_results])
            report.structure_validity_avg = np.mean([r.structure_validity for r in successful_results])
            report.content_quality_avg = np.mean([r.content_quality for r in successful_results])

        return report

    def print_report(self, report: MetricsReport):
        """Выводит отчёт в нужном формате"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЁТ ТЕСТИРОВАНИЯ")
        print("=" * 80)

        print("\nПринятый объем тестирования:")
        print(f"\t•\tВсего попыток: {report.total_attempts}")
        print(f"\t•\tБлиц-опросы: {report.blitz_attempts} попыток")
        print(f"\t•\tМини-викторины: {report.mini_attempts} попыток")
        print(f"\t•\tПолные квизы: {report.full_attempts} попыток")

        print("\nРезультат")
        print(f"\t•\t{report.total_successes}/{report.total_attempts} успешных валидированных ответов")
        print(f"\t•\tИтоговый score: {report.success_rate:.0f}%")

        print("\n📈 Метрики качества:")
        print(f"\t•\tJSON корректность: {report.json_correctness_avg:.1f}%")
        print(f"\t•\tСтруктурная валидность: {report.structure_validity_avg:.1f}%")
        print(f"\t•\tКачество контента: {report.content_quality_avg:.1f}%")

        print("\n" + "=" * 80)

    def save_report(self, report: MetricsReport):
        """Сохраняет отчёт"""
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
            "metrics": {
                "json_correctness_avg": report.json_correctness_avg,
                "structure_validity_avg": report.structure_validity_avg,
                "content_quality_avg": report.content_quality_avg,
            },
        }

        filepath = os.path.join(TEST_RESULTS_DIR, "test_report.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        print(f"✅ Отчёт сохранён: {filepath}")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    framework = QuizTestFramework()
    report = framework.run_all_tests()
    framework.print_report(report)
    framework.save_report(report)
