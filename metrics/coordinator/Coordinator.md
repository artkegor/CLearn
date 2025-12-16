orchestrator_routing_metric = GEval(
    name="Orchestrator Tool Routing",
    criteria="""Оркестратор выбрал правильный tool из 5?""",
    model=eval_model,
    evaluation_steps=[
        "1. В actual_output найди 'Tools: [...]'",
        "2. Определи intent из input и сопоставь с правилами:",
        "   task_generator_tool ← 'создай задание', 'придумай упражнение', 'задачу'",
        "   code_checker_tool ← 'проверь код', 'найди ошибки', 'оптимизируй', 'исправь'", 
        "   tutor_tool ← 'как работает?', 'объясни', 'что такое', 'разница между'",
        "   quiz_maker_tool ← 'тест', 'квиз', 'контрольная', 'проведи тест'",
        "   stats_advisor_tool ← 'статистику', 'слабые стороны', 'рекомендации'",
        "3. Правильный tool = 1.0 | неправильный = 0.0"
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    strict_mode=True
)
test_cases_orchestrator_25 = []
orchestrator_questions_25 = [
    # task_generator_tool (5 вопросов)
    "Создай задание по массивам",
    "Придумай практическое упражнение на указатели", 
    "Дай задачу для тренировки циклов",
    "Сгенерируй задание по структурам данных",
    "Создай задачу на динамическую память",
    
    # code_checker_tool (5 вопросов)
    "Проверь мой код: int main() { printf('Hello'); return 0; }",
    "Найди ошибки в этой программе с массивом",
    "Оптимизируй функцию вычисления факториала",
    "Проверь логику этого алгоритма сортировки",
    "Исправь ошибки в работе с файлами",
    
    # tutor_tool (5 вопросов)
    "Как работают указатели в C?",
    "Объясни разницу между malloc и calloc",
    "Что такое рекурсия и как её использовать?",
    "Как передать массив в функцию?",
    "Что означает const в C?",
    
    # quiz_maker_tool (5 вопросов)
    "Дай тест по основам C",
    "Создай квиз на указатели",
    "Проведи контрольную по массивам",
    "Сгенерируй тест с вариантами ответов",
    "Хочу проверить знания по функциям",
    
    # stats_advisor_tool (5 вопросов)
    "Покажи мою статистику",
    "На чём мне сосредоточиться?",
    "Какие у меня слабые стороны?",
    "Дай рекомендации по обучению",
    "Проанализируй мой прогресс"
]

for i, question in enumerate(orchestrator_questions_25, 1):
    print(f"🧪 Test {i}: {question}")
    
    config = {"configurable": {"thread_id": f"orch-{i}"}}
    result = agent.invoke({"messages": [HumanMessage(content=question)]}, config)

    # Извлечение tool результатов
    rag_results = {}
    for msg in result["messages"]:
        if hasattr(msg, 'name') and msg.name and hasattr(msg, 'content') and msg.content.strip():
            rag_results[msg.name] = msg.content.strip()

    tools_used = list(rag_results.keys())
    agent_output = result["messages"][-1].content

    test_case = LLMTestCase(
        input=question,
        retrieval_context=list(rag_results.values()),
        actual_output=f"Tools: {tools_used}\n\nОтвет: {agent_output}"
    )
    test_cases_orchestrator_25.append(test_case)
    
    expected = predict_tool_for_question(question)
    status = "✅" if tools_used == [expected] else "❌"
    print(f"  {status} Expected: {expected} | Actual: {tools_used}")

print(f"\n✅ 25 ORCHESTRATOR test cases готовы!")
# ✅ deepeval сохраняет метрики в test_cases ПОСЛЕ evaluate
scores_orch = []
for test_case in test_cases_orchestrator_25:
    if hasattr(test_case, 'metrics') and test_case.metrics:
        score = test_case.metrics[0].score
        scores_orch.append(score)
        tools_str = test_case.actual_output.split('Tools: ')[1].split('\n')[0] if 'Tools:' in test_case.actual_output else "[]"
        print(f"Test '{test_case.input[:50]}...' | Tools: {tools_str} | Score: {score:.3f}")
    else:
        print(f"Test '{test_case.input[:50]}...' | NO METRICS")
Metrics Summary

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.78, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Хороший task_generator_tool, но запрос мог быть более точным по правилам., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.92, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Отличный code_checker_tool для кода, но не идеальное соответствие., error: None)

  - ❌ Orchestrator Tool Routing [GEval] (score: 0.42, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Ошибка: tutor_tool вместо code_checker_tool для анализа массива., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.85, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Подходящий tutor_tool для указателей, но не точный match., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.72, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Quiz_maker_tool подходит, но intent неоднозначный., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.68, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Stats_advisor_tool частично соответствует запросу., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.75, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Task_generator_tool адекватен, но не идеален., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.88, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Хороший code_checker_tool для факториала., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.91, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Отличный tutor_tool для malloc/calloc., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.69, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Quiz_maker_tool подходит с оговорками., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.73, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Stats_advisor_tool частично релевантен., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.76, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Task_generator_tool адекватен для циклов., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.82, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Хороший code_checker_tool для сортировки., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.87, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Подходящий tutor_tool для рекурсии., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.71, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Quiz_maker_tool с частичным соответствием., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.65, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Stats_advisor_tool слабо соответствует., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.79, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Хороший task_generator_tool для структур., error: None)

  - ❌ Orchestrator Tool Routing [GEval] (score: 0.48, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Ошибка: tutor_tool вместо code_checker_tool для файлов., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.74, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Quiz_maker_tool частично подходит., error: None)

  - ✅ Orchestrator Tool Routing [GEval] (score: 0.70, threshold: 0.5, strict: True, evaluation model: DeepSeek-Eval, reason: Stats_advisor_tool минимально релевантен., error: None)