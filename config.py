import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()


# Configuration class to hold all settings
class Config:
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your-default-telegram-bot-token')
    MONGO_URI = os.getenv('MONGO_URI', 'your-default-mongo-uri')
    GPT_API_KEY = os.getenv('OPENAI_API_KEY', 'your-default-openai-api-key')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '123456789'))

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
