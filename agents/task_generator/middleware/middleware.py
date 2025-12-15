from typing import Dict, Any, Optional
import re
import json
from datetime import datetime
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from langchain.agents.middleware import before_agent, after_agent, after_model, before_model


# ============================================
# 1. MIDDLEWARE ВАЛИДАЦИИ ВХОДНЫХ ДАННЫХ
# ============================================
# Проверяет topic_id (1-10) и difficulty (1-3) ДО запуска агента
@before_agent
def validate_input_middleware(state: Dict[str, Any], runtime: Runtime) -> Optional[Dict[str, Any]]:
    """
    Валидирует пользовательский ввод (topic_id и difficulty) перед запуском агента.
    Возвращает сообщение об ошибке если валидация не прошла, позволяя агенту пропустить выполнение.

    Назначение: Предотвратить отправку невалидных запросов в LLM, экономить токены и время.
    """
    messages = state.get("messages", [])

    # Если нет сообщений, нечего валидировать
    if not messages:
        return None

    # Получаем последнее сообщение пользователя в нижнем регистре
    user_message = messages[-1].content.lower()
    errors = []

    # Проверяем topic_id (должен быть 1-10)
    topic_match = re.search(r"тема\s*(\d+)|topic\s*(\d+)", user_message)
    if topic_match:
        topic_id = int(topic_match.group(1) or topic_match.group(2))
        if topic_id not in range(1, 11):
            errors.append(f"❌ ID темы должен быть от 1 до 10 (получен {topic_id})")

    # Проверяем difficulty (должен быть 1-3)
    difficulty_match = re.search(r"сложност[ь]?\s*(\d)|difficulty\s*(\d)", user_message)
    if difficulty_match:
        difficulty = int(difficulty_match.group(1) or difficulty_match.group(2))
        if difficulty not in [1, 2, 3]:
            errors.append(f"❌ Сложность должна быть 1, 2 или 3 (получена {difficulty})")

    # Если есть ошибки валидации, возвращаем сообщение об ошибке
    if errors:
        error_msg = "\n".join(errors)
        return {
            "messages": messages + [AIMessage(error_msg)]
        }

    return None


# ============================================
# 2. MIDDLEWARE ОБОГАЩЕНИЯ КОНТЕКСТА
# ============================================
# Добавляет контекст RAG и системную информацию ДО каждого вызова LLM

@before_model
def enrich_context_middleware(state: Dict[str, Any], runtime: Runtime) -> Optional[Dict[str, Any]]:
    """
    Обогащает контекст сообщений перед каждым вызовом LLM.
    - Добавляет временную метку
    - Добавляет счётчик количества сообщений
    - Подготавливает управление контекстным окном

    Назначение: Убедиться что LLM имеет актуальный контекст о состоянии беседы.
    """
    messages = state.get("messages", [])

    # Если сообщений больше одного
    if len(messages) > 1:
        # Добавляем системное примечание о состоянии беседы каждые 3 сообщения
        if len(messages) % 3 == 0:
            conversation_summary = {
                "total_messages": len(messages),
                "timestamp": datetime.now().isoformat(),
                "last_user_action": "tool_execution" if len(messages) > 1 else "initial"
            }

            # Опционально добавляем в состояние для отслеживания
            state["conversation_meta"] = conversation_summary

    return None


# ============================================
# 3. MIDDLEWARE ЛОГИРОВАНИЯ ОТВЕТОВ
# ============================================
# Логирует каждый ответ модели для мониторинга и отладки

@after_model
def log_model_response_middleware(state: Dict[str, Any], runtime: Runtime) -> Optional[Dict[str, Any]]:
    """
    Логирует ответы модели для отладки, мониторинга и аналитики.

    Назначение: Отслеживать какие инструменты выбирает агент, качество ответов и паттерны выполнения.
    """
    messages = state.get("messages", [])

    # Если нет сообщений, нечего логировать
    if not messages:
        return None

    # Получаем последний ответ
    last_response = messages[-1]

    # Извлекаем информацию об использованных инструментах
    tool_calls = []
    if hasattr(last_response, 'tool_calls') and last_response.tool_calls:
        for tool_call in last_response.tool_calls:
            # ИСПРАВЛЕНИЕ: tool_call может быть словарём или объектом
            # Проверяем оба варианта
            if isinstance(tool_call, dict):
                # Если это словарь
                tool_calls.append({
                    "name": tool_call.get("name", "unknown"),
                    "args": str(tool_call.get("args", ""))[:100]
                })
            else:
                # Если это объект с атрибутами
                tool_calls.append({
                    "name": getattr(tool_call, "name", "unknown"),
                    "args": str(getattr(tool_call, "args", ""))[:100]
                })

    # Логируем в консоль (в production отправляем в LangSmith или сервис логирования)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message_type": type(last_response).__name__,
        "content_preview": str(last_response.content)[:200] if last_response.content else "No content",
        "tool_calls": tool_calls,
        "total_messages_so_far": len(messages)
    }

    print(f"\n📊 [Лог ответа агента]\n{json.dumps(log_entry, indent=2, ensure_ascii=False)}\n")

    return None
