import datetime

from bot.database.user_db import UserDB
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot

import bot.keyboards.inline as inline_keyboards

# Initialize logger
logger = setup_logging()

# Initialize user database
user_db = UserDB()


# Function to handle commands
async def callbacks_handler(bot: AsyncTeleBot):
    @bot.callback_query_handler(func=lambda call: call.data == "solve_task")
    async def start_learning_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="📚 Выберите тему задания:",
                reply_markup=inline_keyboards.choose_task_theme_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in start_learning_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
