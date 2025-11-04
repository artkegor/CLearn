from config import Config
from database.user_db import UserDB
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot

import bot.keyboards.inline as inline_keyboards

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()

# Constants
THEMES = Config.C_TOPICS
DIFFICULTIES = Config.TASK_DIFFICULTIES
STATES = Config.BotStates


# Function to handle commands
async def callbacks_handler(bot: AsyncTeleBot):
    # Back to main menu handler
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
    async def back_to_main_menu_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🏠 Главное меню:",
                reply_markup=inline_keyboards.main_menu_keyboard()
            )
            await bot.delete_state(
                chat_id=chat_id,
                user_id=chat_id
            )
        except Exception as e:
            logger.error(f"Error in back_to_main_menu_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    # Profile button handler
    @bot.callback_query_handler(func=lambda call: call.data == "profile")
    async def profile_callback(call):
        chat_id = call.message.chat.id
        user = user_db.get_user(chat_id)

        if user:
            username = user.username
            register_date = user.register_date

            profile_text = (f"👤 Профиль пользователя:\n\n"
                            f"🔹 ID: {chat_id}\n"
                            f"🔹 Имя пользователя: @{username}\n"
                            f"🔹 Дата регистрации: {register_date}\n")
        else:
            profile_text = "❗ Пользователь не найден в базе данных."

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=profile_text,
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )
        except Exception as e:
            logger.error(f"Error in profile_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    # Handler for feedback button
    @bot.callback_query_handler(func=lambda call: call.data == "feedback")
    async def feedback_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="📢 Пожалуйста, напишите ваш вопрос и мы на него ответим.\n\n"
                     "При необходимости вы можете прикрепить фото, видео или документ.",
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )
            await bot.set_state(
                chat_id=chat_id,
                user_id=chat_id,
                state=STATES.WAITING_FOR_FEEDBACK
            )
        except Exception as e:
            logger.error(f"Error in feedback_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
