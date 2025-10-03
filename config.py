import os
from dotenv import load_dotenv
from telebot.handler_backends import State, StatesGroup

# Load environment variables from a .env file if it exists
load_dotenv()


# Configuration class to hold all settings
class Config:
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-default-telegram-bot-token')
    MONGO_URI = os.getenv('MONGO_URI', 'your-default-mongo-uri')
    GPT_API_KEY = os.getenv('OPENAI_API_KEY', 'your-default-openai-api-key')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))
    FEEDBACK_CHAT_ID = int(os.getenv('FEEDBACK_CHAT_ID', '987654321'))
    BOT_ID = int(os.getenv('BOT_ID', '123456789'))

    # Other configuration settings
    C_TOPICS = {
        "1": "Переменные и типы данных",
        "2": "Условные операторы",
        "3": "Циклы",
        "4": "Массивы",
        "5": "Функции",
        "6": "Указатели",
        "7": "Структуры",
        "8": "Работа с файлами",
        "9": "Динамическая память",
        "10": "Препроцессор"
    }

    TASK_DIFFICULTIES = {
        "1": "🟢 Легкий",
        "2": "🟡 Средний",
        "3": "🔴 Сложный"
    }

    # Bot states for managing conversation flow
    class BotStates(StatesGroup):
        WAITING_FOR_FEEDBACK = State()
        WAITING_FOR_TASK_SOLUTION = State()
