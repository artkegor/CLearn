from langchain_deepseek import ChatDeepSeek
from config import Config

llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=Config.DEEPSEEK_API_KEY,
    temperature=0.7,
    max_tokens=4096,
    timeout=120
)