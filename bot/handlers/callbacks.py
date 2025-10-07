from config import Config
from bot.database.user_db import UserDB
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

    # Handler for solve task button
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

    # Handler for task theme selection
    @bot.callback_query_handler(func=lambda call: call.data.startswith("task_theme_"))
    async def choose_task_theme_callback(call):
        chat_id = call.message.chat.id
        theme_id = call.data.split("_")[-1]
        theme_name = THEMES.get(theme_id, "Неизвестная тема")

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Вы выбрали тему: {theme_name}\n\n"
                     "Выберите сложность задания:",
                reply_markup=inline_keyboards.choose_task_difficulty_keyboard(theme_id)
            )
        except Exception as e:
            logger.error(f"Error in choose_task_theme_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    # Handler for task difficulty selection
    @bot.callback_query_handler(func=lambda call: call.data.startswith("task_difficulty_"))
    async def choose_task_difficulty_callback(call):
        chat_id = call.message.chat.id
        theme_id = call.data.split("_")[-2]
        difficulty_id = call.data.split("_")[-1]
        theme_name = THEMES.get(theme_id, "Неизвестная тема")
        difficulty_name = DIFFICULTIES.get(difficulty_id, "Неизвестная сложность")

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Вы выбрали тему: {theme_name}\n"
                     f"🧠 Сложность: {difficulty_name}\n\n"
                     "Задание будет здесь (пока заглушка).",
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )
        except Exception as e:
            logger.error(f"Error in choose_task_difficulty_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
