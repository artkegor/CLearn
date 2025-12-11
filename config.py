import os
from dotenv import load_dotenv
from telebot.handler_backends import State, StatesGroup

# Load environment variables from a .env file if it exists
load_dotenv()


# Configuration class to hold all settings
class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-default-telegram-bot-token')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))
    FEEDBACK_CHAT_ID = int(os.getenv('FEEDBACK_CHAT_ID', '987654321'))
    BOT_ID = int(os.getenv('BOT_ID', '123456789'))

    # Database Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'your-default-mongo-uri')

    # API Configuration
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
    DEEPSEEK_MODEL = "deepseek-chat"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_TEMPERATURE = 0.7
    DEEPSEEK_MAX_TOKENS = 4096

    # Bot states for managing conversation flow
    class BotStates(StatesGroup):
        WAITING_FOR_FEEDBACK = State()
        WAITING_FOR_TASK_SOLUTION = State()
        WAITING_FOR_TUTOR_QUESTION = State()
        WAITING_FOR_MAGIC_AGENT_INPUT = State()

    # Other configuration settings
    C_TOPICS = {
        "1": "Переменные и типы данных",
        "2": "Условные операторы",
        "3": "Циклы",
        "4": "Массивы",
        "5": "Функции",
        "6": "Указатели",
        "7": "Структуры данных",
        "8": "Работа с файлами",
        "9": "Динамическая память",
        "10": "Препроцессор"
    }

    TASK_DIFFICULTIES = {
        "1": "🟢 Легкий",
        "2": "🟡 Средний",
        "3": "🔴 Сложный"
    }
