from config import Config
from database.user_db import UserDB
from database.task_db import TaskDB
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot

import bot.keyboards.inline as inline_keyboards
from agents.stats_analyzer.agent_instance import brief_summary, detailed_summary

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()
task_db = TaskDB()

# Constants
THEMES = Config.C_TOPICS
DIFFICULTIES = Config.TASK_DIFFICULTIES
STATES = Config.BotStates
C_TOPICS = Config.C_TOPICS


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

    # Ask tutor button handler
    @bot.callback_query_handler(func=lambda call: call.data == "ask_tutor")
    async def ask_tutor_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🤖 Пожалуйста, введите ваш вопрос для ИИ-репетитора:",
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )
            await bot.set_state(
                chat_id=chat_id,
                user_id=chat_id,
                state=STATES.WAITING_FOR_TUTOR_QUESTION
            )
        except Exception as e:
            logger.error(f"Error in ask_tutor_callback: {e}")
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

    # Statistics button handler
    @bot.callback_query_handler(func=lambda call: call.data == "statistics")
    async def statistics_callback(call):
        await bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📊 Выберите тип статистики:",
            reply_markup=inline_keyboards.statistics_menu_keyboard()
        )

    # Brief summary of user statistics
    @bot.callback_query_handler(func=lambda call: call.data.startswith("summary_"))
    async def brief_statistics_callback(call):
        chat_id = call.message.chat.id
        user = user_db.get_user(chat_id)
        solutions = user.solutions if user else []
        report = ''

        for solution in enumerate(solutions, start=1):
            task = task_db.get_task(solution[1]['task_id'])
            report += (f"Решена задача сложности {task.difficulty}/3 по теме '{C_TOPICS[task.topic_id]}' "
                       f"с оценкой {solution[1]['score']}/100.\n")

        if not report:
            report = "У вас пока нет решённых задач."
        try:
            if call.data == "summary_brief":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"🔄 Загружаем вашу краткую статистику...",
                )

                ai_report = brief_summary(report)
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"📊 Ваша краткая статистика:\n\n{ai_report}",
                    reply_markup=inline_keyboards.back_to_main_menu_button()
                )
            elif call.data == "summary_detailed":
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"🔄 Загружаем вашу подробную статистику...",
                )

                ai_report = detailed_summary(report)
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"📊 Ваша подробная статистика:\n\n{ai_report}",
                    reply_markup=inline_keyboards.back_to_main_menu_button()
                )
            logger.info(f"Provided statistics summary to user {chat_id}")
        except Exception as e:
            logger.error(f"Error in brief_statistics_callback: {e}")
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

    # Magic agent button handler
    @bot.callback_query_handler(func=lambda call: call.data == "magic_agent")
    async def magic_agent_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🪄 Пожалуйста, введите ваш запрос для Волшебного агента:",
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )
            await bot.set_state(
                chat_id=chat_id,
                user_id=chat_id,
                state=STATES.WAITING_FOR_MAGIC_AGENT_INPUT
            )
        except Exception as e:
            logger.error(f"Error in magic_agent_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )