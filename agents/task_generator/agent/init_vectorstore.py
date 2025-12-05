import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Script path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
EXAMPLES_PATH = os.path.join(BASE_DIR, "../c_knowledge_data/Tasks_examples.md")
VECTORSTORE_PATH = os.path.join(BASE_DIR, "../vector_db/task_generation_faiss")

# Embeddings model
embeddings = SentenceTransformerEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# Load example tasks from markdown file
def load_from_markdown():
    example_tasks = []

    if not os.path.exists(EXAMPLES_PATH):
        print(f"❌ Файл {EXAMPLES_PATH} не найден!")
        return []

    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")
        current_task = ""

        for line in lines:
            if line.strip():
                current_task += line + "\n"
            else:
                if current_task.strip():
                    example_tasks.append(current_task.strip())
                    current_task = ""

        if current_task.strip():
            example_tasks.append(current_task.strip())

    return example_tasks


# Initialize vector store
example_tasks = load_from_markdown()

if not example_tasks:
    print("⚠️ Не удалось загрузить примеры. Проверь файл Tasks_examples.md")
else:
    print(f"📚 Загружено {len(example_tasks)} примеров из Tasks_examples.md")
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    vectorstore = FAISS.from_texts(example_tasks, embeddings)
    vectorstore.save_local(VECTORSTORE_PATH)
    print("✅ Индекс успешно создан и сохранен!")
    print(f"📁 Сохранен в: {VECTORSTORE_PATH}")
