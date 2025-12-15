"""
============================================
RAG CHUNKING & LOADING SYSTEM
Модуль для разбиения текста на чанки с перекрытием
и загрузки в векторную БД (FAISS)
============================================
"""

import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# ============================================
# ПАРАМЕТРЫ ПО УМОЛЧАНИЮ
# ============================================

DEFAULT_CHUNK_SIZE = 1000  # Размер одного чанка (символов)
DEFAULT_CHUNK_OVERLAP = 200  # Перекрытие между чанками (символов)
DEFAULT_SEPARATORS = [
    "\n\n",  # Два перевода строки (абзац)
    "\n",  # Один перевод строки (строка)
    ". ",  # Конец предложения
    " ",  # Пробел
    ",",  # Запятая
    ""  # Символ (если ничего не подошло)
]


# ============================================
# 1. СОЗДАНИЕ СПЛИТТЕРА
# ============================================

def create_text_splitter(
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = None
) -> RecursiveCharacterTextSplitter:
    """
    Создаёт сплиттер для разбиения текста на чанки.

    Args:
        chunk_size: Размер одного чанка в символах
        chunk_overlap: Размер перекрытия между чанками
        separators: Список сепараторов для рекурсивного разбиения

    Returns:
        RecursiveCharacterTextSplitter объект

    Пример:
        splitter = create_text_splitter(chunk_size=500, chunk_overlap=100)
    """
    if separators is None:
        separators = DEFAULT_SEPARATORS

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
    )


# ============================================
# 2. РАЗБИЕНИЕ ТЕКСТА НА ЧАНКИ
# ============================================

def split_text_into_chunks(
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = None
) -> List[str]:
    """
    Разбивает текст на чанки с перекрытием.

    Args:
        text: Исходный текст
        chunk_size: Размер одного чанка
        chunk_overlap: Размер перекрытия
        separators: Сепараторы для разбиения

    Returns:
        Список чанков (строк)

    Пример:
        chunks = split_text_into_chunks("Длинный текст...", chunk_size=500)
        print(f"Создано {len(chunks)} чанков")
    """
    splitter = create_text_splitter(chunk_size, chunk_overlap, separators)

    # Обворачиваем текст в Document объект (как ожидает LangChain)
    from langchain_core.documents import Document
    documents = [Document(page_content=text)]

    # Разбиваем на чанки
    split_docs = splitter.split_documents(documents)

    # Извлекаем только содержимое
    chunks = [doc.page_content for doc in split_docs]

    return chunks


# ============================================
# 3. СОЗДАНИЕ ЭМБЕДДИНГОВ
# ============================================

def create_embeddings(
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> SentenceTransformerEmbeddings:
    """
    Создаёт объект эмбеддингов.

    Args:
        model_name: Имя модели SentenceTransformer

    Returns:
        SentenceTransformerEmbeddings объект

    Рекомендуемые модели:
        - "sentence-transformers/all-MiniLM-L6-v2" (быстрая, легкая)
        - "sentence-transformers/all-mpnet-base-v2" (качественная)
        - "sentence-transformers/paraphrase-multilingual-mpnet-base-v2" (многоязычная)
    """
    return SentenceTransformerEmbeddings(model_name=model_name)


# ============================================
# 4. ЗАГРУЗКА В FAISS (ВЕКТОРНАЯ БД)
# ============================================

def load_documents_to_faiss(
        text: str,
        db_path: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        separators: List[str] = None,
        embeddings=None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> FAISS:
    """
    Разбивает текст на чанки и загружает в FAISS.

    Args:
        text: Исходный текст для чанкирования
        db_path: Путь для сохранения БД (например: "vector_db/my_data")
        chunk_size: Размер чанка
        chunk_overlap: Перекрытие между чанками
        separators: Сепараторы для разбиения
        embeddings: Объект эмбеддингов (если None, создаётся новый)
        model_name: Имя модели для эмбеддингов

    Returns:
        FAISS объект (загруженный и готовый к использованию)

    Пример:
        vectorstore = load_documents_to_faiss(
            text="Мой текст...",
            db_path="vector_db/task_generation_faiss",
            chunk_size=1000
        )
    """
    print("📄 Разбиваю текст на чанки...")
    chunks = split_text_into_chunks(text, chunk_size, chunk_overlap, separators)
    print(f"✅ Создано чанков: {len(chunks)}")

    # Статистика
    total_chars = sum(len(chunk) for chunk in chunks)
    avg_size = total_chars // len(chunks) if chunks else 0
    print(f"   • Всего символов: {total_chars}")
    print(f"   • Средний размер: {avg_size} символов")
    print(f"   • Примерно токенов: {total_chars // 4}")

    # Создаём эмбеддинги если не передали
    if embeddings is None:
        print(f"\n🧮 Загружаю модель эмбеддингов: {model_name}")
        embeddings = create_embeddings(model_name)

    # Преобразуем чанки в Document объекты
    from langchain_core.documents import Document
    documents = [Document(page_content=chunk) for chunk in chunks]

    # Создаём FAISS из документов
    print("🗂️  Создаю FAISS индекс...")
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Создаём директорию если её нет
    os.makedirs(db_path, exist_ok=True)

    # Сохраняем БД
    print(f"💾 Сохраняю БД в {db_path}")
    vectorstore.save_local(db_path)

    print("✅ Готово! FAISS загружена и сохранена.\n")

    return vectorstore


# ============================================
# 5. ЗАГРУЗКА СУЩЕСТВУЮЩЕЙ FAISS БД
# ============================================

def load_faiss_vectorstore(
        db_path: str,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> FAISS:
    """
    Загружает существующую FAISS БД.

    Args:
        db_path: Путь к сохранённой БД
        model_name: Имя модели для эмбеддингов

    Returns:
        FAISS объект

    Пример:
        vectorstore = load_faiss_vectorstore("vector_db/task_generation_faiss")
    """
    print(f"📂 Загружаю FAISS из {db_path}")

    embeddings = create_embeddings(model_name)
    vectorstore = FAISS.load_local(
        db_path,
        embeddings,
        allow_dangerous_deserialization=True
    )

    print("✅ FAISS загружена успешно!\n")
    return vectorstore


# ============================================
# 6. ПОИСК В FAISS (RAG)
# ============================================

def search_similar_chunks(
        vectorstore: FAISS,
        query: str,
        k: int = 5
) -> List[Dict[str, Any]]:
    """
    Ищет похожие чанки в FAISS.

    Args:
        vectorstore: FAISS объект
        query: Поисковый запрос
        k: Количество результатов

    Returns:
        Список похожих чанков с метаданными

    Пример:
        results = search_similar_chunks(vectorstore, "Функции в Python", k=3)
        for result in results:
            print(result['content'])
    """
    results = vectorstore.similarity_search(query, k=k)

    formatted_results = [
        {
            'content': doc.page_content,
            'metadata': doc.metadata if hasattr(doc, 'metadata') else {}
        }
        for doc in results
    ]

    return formatted_results


# ============================================
# 7. ДОБАВЛЕНИЕ НОВЫХ ДОКУМЕНТОВ
# ============================================

def add_documents_to_faiss(
        vectorstore: FAISS,
        new_texts: List[str],
        db_path: str
) -> FAISS:
    """
    Добавляет новые документы в существующую FAISS БД.

    Args:
        vectorstore: Существующий FAISS объект
        new_texts: Список новых текстов/чанков
        db_path: Путь для сохранения обновленной БД

    Returns:
        Обновленный FAISS объект

    Пример:
        new_chunks = ["Новый текст 1", "Новый текст 2"]
        vectorstore = add_documents_to_faiss(vectorstore, new_chunks, "vector_db/my_data")
    """
    from langchain_core.documents import Document

    print(f"➕ Добавляю {len(new_texts)} новых документов...")

    documents = [Document(page_content=text) for text in new_texts]
    vectorstore.add_documents(documents)

    os.makedirs(db_path, exist_ok=True)
    vectorstore.save_local(db_path)

    print(f"✅ Документы добавлены и БД сохранена в {db_path}\n")

    return vectorstore


# ============================================
# 8. УТИЛИТА: ИНФОРМАЦИЯ О БД
# ============================================

def get_vectorstore_info(vectorstore: FAISS) -> Dict[str, Any]:
    """
    Получает информацию о FAISS БД.

    Returns:
        Словарь с информацией о БД
    """
    try:
        index_size = vectorstore.index.ntotal
        return {
            'total_documents': index_size,
            'index_type': type(vectorstore.index).__name__,
            'dimension': vectorstore.index.d if hasattr(vectorstore.index, 'd') else 'Unknown'
        }
    except:
        return {'status': 'Unable to retrieve info'}
