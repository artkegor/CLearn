import os
from config import Config
from langchain_deepseek import ChatDeepSeek

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def init_llm():
    """Initialize and return the DeepSeek chat model."""
    return ChatDeepSeek(
        model="deepseek-chat",
        api_key=Config.DEEPSEEK_API_KEY,
        temperature=0.3,
        max_tokens=4096
    )
