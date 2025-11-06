import random

from html import escape
from config import Config
from database.user_db import UserDB
from database.task_db import TaskDB
from models.database_models import TaskModel
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot

import bot.keyboards.inline as inline_keyboards
import agents.task_generator.agent_instance as agent_instance

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

    # Handler for task difficulty selection (task generation)
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
                text="⏳ Генерируем задание, пожалуйста подождите..."
            )

            task = agent_instance.task_generator.create_complete_task(topic_id=theme_id, difficulty=int(difficulty_id))
            task_id = str(random.randint(100000, 999999))

            task_model = TaskModel(
                task_id=task_id,
                topic_id=theme_id,
                difficulty=difficulty_id,
                task_text=task.get("task_text", ""),
                test_cases=task.get("test_cases", {}),
                solution_code=task.get("solution_code", ""),
            )

            TaskDB().add_task(task_model)

            if not task.get("success"):
                raise Exception(task.get("error", "Unknown error during task generation"))

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Вы выбрали тему: {theme_name}\n"
                     f"🧠 Сложность: {difficulty_name}\n\n"
                     "📝 Вот ваше задание:\n\n"
                     "" + escape(task["task_text"]) + "\n\n",
                reply_markup=inline_keyboards.task_interaction_keyboard(
                    task_id=task_id
                )
            )
        except Exception as e:
            logger.error(f"Error in choose_task_difficulty_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    # Handler for submitting solution
    @bot.callback_query_handler(func=lambda call: call.data.startswith("submit_solution_"))
    async def submit_solution_callback(call):
        chat_id = call.message.chat.id
        task_id = call.data.split("_")[-1]

        try:
            await bot.send_message(
                chat_id=chat_id,
                text="✍️ Пожалуйста, отправьте ваше решение в следующем сообщении. "
                     "Убедитесь, что вы отправляете полный код на C."
            )
            await bot.set_state(
                chat_id=chat_id,
                user_id=chat_id,
                state=STATES.WAITING_FOR_TASK_SOLUTION
            )
            async with bot.retrieve_data(
                    chat_id=chat_id,
                    user_id=chat_id
            ) as data:
                data["current_task_id"] = task_id
        except Exception as e:
            logger.error(f"Error in submit_solution_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    # Handler for showing solution
    @bot.callback_query_handler(func=lambda call: call.data.startswith("show_solution_"))
    async def show_solution_callback(call):
        chat_id = call.message.chat.id
        task_id = call.data.split("_")[-1]

        try:
            task = TaskDB().tasks.find_one({"task_id": task_id})
            if not task:
                raise Exception("Task not found")

            solution_code = task.get("solution_code", "Решение не найдено.")

            await bot.send_message(
                chat_id=chat_id,
                text=f"🧩 Решение задания:\n\n```c\n{solution_code}\n```",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error in show_solution_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
