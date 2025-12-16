import pytest
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.prompt.utils import schema_type_map
from deepeval.test_case import LLMTestCase
from agents.code_analyzer.tools.analyze_and_advise import analyze_and_advise_tool
from deepeval.test_case import LLMTestCaseParams
from config import Config
import asyncio
import requests
from typing import Any
from deepeval.models.base_model import DeepEvalBaseLLM


class DeepSeekLLM(DeepEvalBaseLLM):
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model_name = model

    def load_model(self):
        return self

    def get_model_name(self):
        return self.model_name

    # === Синхронная генерация текста ===
    def generate(self, prompt: str) -> str:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    # === Асинхронная генерация "сырой" строки ===
    async def a_generate_raw(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, prompt)

    # === Асинхронная генерация с поддержкой схем DeepEval ===
    async def a_generate(self, prompt: str, schema: Any = None, **kwargs):
        text = await self.a_generate_raw(prompt)

        if schema is None:
            return text  # без кортежа

        if schema.__name__ == "Answer":
            class Answer:
                def __init__(self, answer):
                    self.answer = answer

            return Answer(text)

        if schema.__name__ == "Answers":
            class Answer:
                def __init__(self, answer):
                    self.answer = answer

            class Answers:
                def __init__(self, answers):
                    self.answers = answers

            return Answers([Answer(text)])

        if schema.__name__ == "ReasonScore":
            class ReasonScore:
                def __init__(self, score, reason):
                    self.score = score
                    self.reason = reason

            return ReasonScore(score=1.0, reason=text)

        if schema.__name__ == "Verdicts":
            class Verdict:
                def __init__(self, verdict):
                    self.verdict = verdict

            class Verdicts:
                def __init__(self, verdicts):
                    self.verdicts = verdicts

            return Verdicts([Verdict(text)])

        if schema.__name__ == "Claims":
            class Claims:
                def __init__(self, claims):
                    self.claims = claims

            return Claims([text])

        if schema.__name__ == "Statements":
            class Statements:
                def __init__(self, statements):
                    self.statements = statements

            return Statements([text])

        if schema.__name__ == "Truths":
            class Truths:
                def __init__(self, truths):
                    self.truths = truths

            return Truths([text])

        if schema.__name__ == "ReasonScore":
            class ReasonScore:
                def __init__(self, score, reason):
                    self.score = score
                    self.reason = reason

            return ReasonScore(score=1.0, reason=text)

        if schema.__name__ == "FaithfulnessScoreReason":
            class FaithfulnessScoreReason:
                def __init__(self, score, reason):
                    self.score = score
                    self.reason = reason

            return FaithfulnessScoreReason(score=1.0, reason=text)

        if schema.__name__ == "Reason":
            class Reason:
                def __init__(self, reason):
                    self.reason = reason

            return Reason(text)
        return text

    # === Асинхронный "сырой" ответ для GEval ===
    async def a_generate_raw_response(self, prompt: str, **kwargs):
        content = await self.a_generate_raw(prompt)

        class Message:
            def __init__(self, content: str):
                self.content = content

        class Choice:
            def __init__(self, message: Message):
                self.message = message

        class Response:
            def __init__(self, content: str):
                self.choices = [Choice(Message(content))]

        return Response(content), 0.0


@pytest.fixture(scope="session")
def deepseek_model():
    return DeepSeekLLM(api_key=Config.DEEPSEEK_API_KEY)


TEST_CASES = [
    # 1. Границы массива
    {
        "task": "Напишите функцию sum_array, принимающую массив int arr[] и размер n, возвращающую сумму элементов.",
        "user_code": """
int sum_array(int arr[], int n) {
    int sum = 0;
    for(int i = 0; i <= n; i++) {
        sum += arr[i];
    }
    return sum;
}
        """,
        "error": "Array index out of bounds at index n"
    },

    # 2. Бесконечная рекурсия
    {
        "task": "Реализуйте функцию factorial(int n), возвращающую факториал числа n (n >= 0).",
        "user_code": """
int factorial(int n) {
    if (n == 0) return 1;
    return n * factorial(n);
}
        """,
        "error": "Stack overflow"
    },

    # 3. Нулевой размер массива
    {
        "task": "Напишите функцию find_max(int arr[], int n), возвращающую максимальный элемент массива.",
        "user_code": """
int find_max(int arr[], int n) {
    int max = arr[0];
    for(int i = 1; i < n; i++) {
        if(arr[i] > max) max = arr[i];
    }
    return max;
}
        """,
        "error": "Segmentation fault when n=0"
    },

    # 4. Неправильные указатели
    {
        "task": "Создайте функцию swap(int *a, int *b), меняющую местами значения двух чисел.",
        "user_code": """
void swap(int a, int b) {
    int temp = a;
    a = temp;
    b = temp;
}
        """,
        "error": "Values not swapped"
    },

    # 5. Неправильное условие цикла
    {
        "task": "Напишите функцию reverse_array, переставляющую элементы массива в обратном порядке.",
        "user_code": """
void reverse_array(int arr[], int n) {
    for(int i = 0; i < n; i++) {
        int temp = arr[i];
        arr[i] = arr[n-1-i];
        arr[n-1-i] = temp;
    }
}
        """,
        "error": "Array elements not reversed correctly"
    },

    # 6. Отсутствие проверки NULL
    {
        "task": "Напишите функцию strlen(char *str), возвращающую длину строки.",
        "user_code": """
int strlen(char *str) {
    int len = 0;
    while(str[len] != '\\0') {
        len++;
    }
    return len;
}
        """,
        "error": "Segmentation fault on NULL pointer"
    },

    # 7. Неправильная инициализация
    {
        "task": "Реализуйте бинарный поиск: int binary_search(int arr[], int n, int key).",
        "user_code": """
int binary_search(int arr[], int n, int key) {
    int left = 0, right = n;
    while(left <= right) {
        int mid = (left + right) / 2;
        if(arr[mid] == key) return mid;
        if(arr[mid] < key) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
        """,
        "error": "Infinite loop on some inputs"
    },

    # 8. Логическая ошибка
    {
        "task": "Напишите функцию is_prime(int n), возвращающую 1 если n простое, 0 иначе.",
        "user_code": """
int is_prime(int n) {
    if(n <= 1) return 0;
    for(int i = 2; i <= n; i++) {
        if(n % i == 0) return 0;
    }
    return 1;
}
        """,
        "error": "Too slow for large n"
    },

    # 9. Ошибка с динамической памятью
    {
        "task": "Создайте функцию allocate_array(int n), выделяющую массив из n int.",
        "user_code": """
int* allocate_array(int n) {
    int *arr = malloc(n);
    return arr;
}
        """,
        "error": "Wrong memory allocation size"
    },

    # 10. Неправильная работа со строками
    {
        "task": "Напишите функцию strcpy(char *dest, char *src), копирующую строку src в dest.",
        "user_code": """
void strcpy(char *dest, char *src) {
    while(*src != '\\0') {
        *dest = *src;
        dest++;
        src++;
    }
    *dest = *src;
}
        """,
        "error": "Works but missing null terminator explanation needed"
    },

    # 11. Ошибка с указателями на массивы
    {
        "task": "Реализуйте функцию matrix_multiply для умножения двух матриц 2x2.",
        "user_code": """
void matrix_multiply(int a[2][2], int b[2][2], int result[2][2]) {
    for(int i = 0; i < 2; i++) {
        for(int j = 0; j < 2; j++) {
            result[i][j] = a[i][j] + b[i][j];  // + вместо *
        }
    }
}
        """,
        "error": "Matrix multiplication incorrect"
    },

    # 12. Неправильная структура
    {
        "task": "Напишите функцию bubble_sort для сортировки массива по возрастанию.",
        "user_code": """
void bubble_sort(int arr[], int n) {
    for(int i = 0; i < n-1; i++) {
        for(int j = 0; j < n-1; j++) {
            if(arr[j] > arr[j+1]) {
                int temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
}
        """,
        "error": "Inefficient, too many iterations"
    },

    # 13. Ошибка с битвыми операциями
    {
        "task": "Напишите функцию set_bit(int n, int pos), устанавливающую бит pos в 1.",
        "user_code": """
int set_bit(int n, int pos) {
    n = n | (1 << pos);
    return n;
}
        """,
        "error": "Code looks correct but test expects void return"
    },

    # 14. Неправильная работа с файлами
    {
        "task": "Напишите функцию read_file(char *filename), читающую файл в строку.",
        "user_code": """
char* read_file(char *filename) {
    FILE *f = fopen(filename, "r");
    char buffer[1000];
    fscanf(f, "%s", buffer);
    fclose(f);
    return buffer;  // Локальная переменная!
}
        """,
        "error": "Segmentation fault after function returns"
    },

    # 15. Логическая ошибка в условии
    {
        "task": "Реализуйте функцию power(int base, int exp), возвращающую base^exp.",
        "user_code": """
int power(int base, int exp) {
    int result = 1;
    for(int i = 0; i <= exp; i++) {
        result *= base;
    }
    return result;
}
        """,
        "error": "Wrong result for exp=0"
    },

    # 16. Ошибка с typedef
    {
        "task": "Создайте структуру Point {int x, y;} и функцию distance(Point a, Point b).",
        "user_code": """
typedef struct {
    int x, y;
} Point;

float distance(Point a, Point b) {
    int dx = a.x - b.x;
    int dy = a.y - b.y;
    return dx*dx + dy*dy;  // Нет sqrt!
}
        """,
        "error": "Distance squared instead of actual distance"
    },

    # 17. Неправильная работа с enum
    {
        "task": "Создайте enum Color {RED, GREEN, BLUE} и функцию print_color(Color c).",
        "user_code": """
enum Color {RED, GREEN, BLUE};
void print_color(Color c) {
    switch(c) {
        case 0: printf("RED"); break;
        case 1: printf("GREEN"); break;
        case 2: printf("BLUE"); break;
    }
}
        """,
        "error": "Uses magic numbers instead of enum values"
    },

    # 18. Ошибка с префиксными/постфиксными инкрементами
    {
        "task": "Напишите функцию count_even(int arr[], int n), считающую четные числа.",
        "user_code": """
int count_even(int arr[], int n) {
    int count = 0;
    for(int i = 0; i < n; i++) {
        if(arr[i++] % 2 == 0) count++;
    }
    return count;
}
        """,
        "error": "Wrong count, i increments twice"
    },

    # 19. Неправильное использование malloc
    {
        "task": "Создайте функцию create_string_copy(char *str), возвращающую копию строки.",
        "user_code": """
char* create_string_copy(char *str) {
    char *copy = malloc(strlen(str));
    strcpy(copy, str);
    return copy;
}
        """,
        "error": "Buffer overflow, missing space for null terminator"
    },

    # 20. Ошибка с логическими операторами
    {
        "task": "Напишите функцию is_leap_year(int year), проверяющую високосный год.",
        "user_code": """
int is_leap_year(int year) {
    return (year % 4 == 0 || year % 100 == 0 || year % 400 == 0);
}
        """,
        "error": "Wrong leap year logic"
    }
]


@pytest.fixture(scope="session")
def metrics(deepseek_model):
    relevancy = AnswerRelevancyMetric(
        threshold=0.7,
        model=deepseek_model,
        strict_mode=False
    )

    faithfulness = FaithfulnessMetric(
        threshold=0.8,
        model=deepseek_model,
        strict_mode=False
    )

    geval = GEval(
        name="C Code Advice Quality",
        criteria="Качество и полезность советов по исправлению ошибок в C-коде",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT
        ],
        evaluation_steps=[
            "Проверь четкость и конкретность советов по исправлению C-кода",
            "Оцени соответствие советов условию задачи и ошибке",
            "Убедись, что советы помогают самостоятельно исправить код без готового решения",
            "Проверь соблюдение формата: объяснение проблемы, конкретные места, четкие советы"
        ],
        threshold=0.8,
        model=deepseek_model
    )

    return [relevancy, faithfulness, geval]


def create_test_case(task, user_code, error, actual_output):
    """Создает LLMTestCase для DeepEval"""
    return LLMTestCase(
        input=f"Задача: {task}\nКод: {user_code}\nОшибка: {error}",
        actual_output=actual_output,
        retrieval_context=[task, user_code, error],
        expected_output="Четкие рекомендации по исправлению ошибки без готового кода"
    )


def test_agent_metrics(metrics):
    """Основной тест всех метрик агента"""
    results = []

    print("🚀 Запуск тестирования ИИ-агента анализа C-кода...\n")

    for i, case in enumerate(TEST_CASES, 1):
        print(f"Тест {i}/{len(TEST_CASES)}: {case['task'][:60]}...")

        # Получаем ответ агента
        agent_response = analyze_and_advise_tool.invoke({"task_text": case["task"],
                                                         "user_code": case["user_code"],
                                                         "error_text": case["error"]})

        if agent_response.get("success") and agent_response.get("advice"):
            test_case = create_test_case(
                case["task"],
                case["user_code"],
                case["error"],
                agent_response["advice"]
            )

            # Оценка всеми тремя метриками
            evaluate([test_case], metrics)

            results.append({
                "test_num": i,
                "task": case["task"][:50] + "..." if len(case["task"]) > 50 else case["task"],
                "relevancy": test_case.metrics[0].score,
                "faithfulness": test_case.metrics[1].score,
                "geval": test_case.metrics[2].score,
                "overall": test_case.score,
                "reason": test_case.reason
            })

            print(f"✅ Relevancy: {test_case.metrics[0].score:.2f}")
            print(f"✅ Faithfulness: {test_case.metrics[1].score:.2f}")
            print(f"✅ G-Eval: {test_case.metrics[2].score:.2f}")
            print()
        else:
            print(f"❌ Агент вернул ошибку: {agent_response}")
            results.append({
                "test_num": i,
                "task": case["task"][:50] + "...",
                "error": "Agent failed"
            })
            print()

    # Итоговая статистика
    print("=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)

    successful_tests = [r for r in results if "error" not in r]
    if successful_tests:
        avg_relevancy = sum(r["relevancy"] for r in successful_tests) / len(successful_tests)
        avg_faithfulness = sum(r["faithfulness"] for r in successful_tests) / len(successful_tests)
        avg_geval = sum(r["geval"] for r in successful_tests) / len(successful_tests)

        print(f"Средний Relevancy:     {avg_relevancy:.3f}")
        print(f"Средний Faithfulness:  {avg_faithfulness:.3f}")
        print(f"Средний G-Eval:        {avg_geval:.3f}")
        print(f"Успешных тестов:       {len(successful_tests)}/{len(TEST_CASES)}")

        if avg_relevancy >= 0.7 and avg_faithfulness >= 0.8 and avg_geval >= 0.8:
            print("🎉 АГЕНТ ПРОШЕЛ ВСЕ МЕТРИКИ!")
        else:
            print("⚠️  Требуется доработка агента")

    return results


# Прямой запуск без pytest
if __name__ == "__main__":
    metrics_fixture = metrics()
    results = test_agent_metrics(metrics_fixture)

    # Сохранение результатов
    with open("agent_test_results.txt", "w", encoding="utf-8") as f:
        f.write("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ИИ-агента\n")
        f.write("=" * 50 + "\n\n")
        for result in results:
            f.write(f"Тест {result['test_num']}: {result['task']}\n")
            if "error" not in result:
                f.write(f"Relevancy: {result['relevancy']:.3f}\n")
                f.write(f"Faithfulness: {result['faithfulness']:.3f}\n")
                f.write(f"G-Eval: {result['geval']:.3f}\n")
                f.write(f"Общая оценка: {result['overall']:.3f}\n")
                f.write(f"Причина: {result['reason']}\n")
            else:
                f.write(f"Ошибка: {result['error']}\n")
            f.write("-" * 50 + "\n")

    print("📄 Результаты сохранены в agent_test_results.txt")
