from bot.database.user_db import UserDB
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot

# Initialize logger
logger = setup_logging()

# Initialize user database
user_db = UserDB()


# Function to handle commands
def commands_handler(bot: AsyncTeleBot):
    @bot.message_handler(commands=['start'])
    def start_command(message):
        chat_id = message.chat.id

        logger.info(f"User {chat_id} started the bot.")
        user_db.add_user(chat_id, message.from_user.username or "")

        bot.send_message(
            chat_id=chat_id,
            text="Welcome to the bot! Use /help to see available commands."
        )
