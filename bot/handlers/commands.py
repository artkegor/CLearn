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
async def commands_handler(bot: AsyncTeleBot):
    @bot.message_handler(commands=['start'])
    async def start_command(message):
        chat_id = message.chat.id
        try:
            time_now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            logger.info(f"User {chat_id} started the bot.")

            user_db.add_user(
                user_id=chat_id,
                username=message.from_user.username or "",
                register_date=time_now
            )

            await bot.send_message(
                chat_id=chat_id,
                text="🤖 Добро пожаловать в бота для изучения языка C!\n\n"
                     "👇 Нажмите кнопку ниже, чтобы начать:",
                reply_markup=inline_keyboards.main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
