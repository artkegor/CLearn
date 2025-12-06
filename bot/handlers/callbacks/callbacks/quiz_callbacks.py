import random
from html import escape

from config import Config
from database.user_db import UserDB
from database.task_db import TaskDB
from database.quiz_db import QuizDB
from logging_config import setup_logging
from telebot.async_telebot import AsyncTeleBot
from bot.keyboards import inline
from models.database_models import QuizModel
from agents.quiz_generator.agent_instance import blitz, mini, full

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()
task_db = TaskDB()
quiz_db = QuizDB()

# Constants
THEMES = Config.C_TOPICS
DIFFICULTIES = Config.TASK_DIFFICULTIES
STATES = Config.BotStates


# Function to handle commands
async def callbacks_handler(bot: AsyncTeleBot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("take_quiz"))
    async def take_quiz_callback(call):
        chat_id = call.message.chat.id

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="📝 Выберите тему викторины:",
                reply_markup=inline.choose_quiz_theme_keyboard()
            )
        except Exception as e:
            logger.error(f"Error in take_quiz_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_theme_"))
    async def choose_quiz_theme_callback(call):
        chat_id = call.message.chat.id
        theme_id = call.data.split("_")[-1]
        theme_name = THEMES.get(theme_id, "Неизвестная тема")

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ Вы выбрали тему: {theme_name}\n\n"
                     "Выберите тип викторины:",
                reply_markup=inline.choose_quiz_type_keyboard(theme_id)
            )
        except Exception as e:
            logger.error(f"Error in choose_quiz_theme_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_type_"))
    async def choose_quiz_type_callback(call):
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        quiz_type = parts[2]
        theme_id = parts[3]
        theme_name = THEMES.get(theme_id, "Неизвестная тема")

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"📚 Вы выбрали тему: {theme_name}\n"
                     f"🧠 Вы выбрали тип викторины: {quiz_type.capitalize()}\n\n"
                     "Викторина будет сгенерирована в ближайшее время. Пожалуйста, подождите...",
            )

            quiz = {}
            if quiz_type == "blitz":
                quiz = blitz(topic=theme_name)
            elif quiz_type == "mini":
                quiz = mini(topic=theme_name)
            elif quiz_type == "full":
                quiz = full(topic=theme_name)

            logger.info(f"Generated quiz: {quiz}")

            quiz_id = random.randint(100000, 999999)
            quiz_data = QuizModel(
                quiz_id=str(quiz_id),
                topic=theme_id,
                type=quiz_type,
                quiz_title=quiz.get("quiz_title", "Викторина"),
                questions=quiz.get("questions", []),
            )

            quiz_db.add_quiz(quiz_data)

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"🎉 Ваша викторина готова!\n"
                     f"Название: {quiz_data.quiz_title}\n"
                     f"Количество вопросов: {len(quiz_data.questions)}\n\n"
                     f"Вопрос 1: {quiz_data.questions[0]['question_text']}\n\n"
                     f"Варианты ответов:\n"
                     f"1️⃣. {quiz_data.questions[0]['options'][0]}\n"
                     f"2️⃣. {quiz_data.questions[0]['options'][1]}\n"
                     f"3️⃣. {quiz_data.questions[0]['options'][2]}\n"
                     f"4️⃣. {quiz_data.questions[0]['options'][3]}",
                reply_markup=inline.quiz_question_keyboard(str(quiz_id), 0, 0)
            )

        except Exception as e:
            logger.error(f"Error in choose_quiz_type_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка при генерации викторины. Пожалуйста, попробуйте снова позже."
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_answer_"))
    async def quiz_answer_callback(call):
        chat_id = call.message.chat.id
        parts = call.data.split("_")
        quiz_id = parts[2]
        question_index = int(parts[3])
        selected_option = int(parts[4])
        correct_answers_count = int(parts[5])

        try:
            quiz = quiz_db.get_quiz(quiz_id)
            if not quiz:
                raise ValueError("Quiz not found")

            question = quiz.questions[question_index]
            correct_answer = question['correct_answer']

            if selected_option == correct_answer:
                correct_answers_count += 1
                response_text = "✅ Правильно!"
            else:
                emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
                response_text = f"❌ Неправильно! Правильный ответ: {emojis[correct_answer + 1]}️ - {question['options'][correct_answer]}"

            next_question_index = question_index + 1
            if next_question_index < len(quiz.questions):
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=escape(f"{response_text}\n\n"
                                f"Вопрос {next_question_index + 1}: {quiz.questions[next_question_index]['question_text']}\n\n"
                                f"Варианты ответов:\n"
                                f"1️⃣. {quiz.questions[next_question_index]['options'][0]}\n"
                                f"2️⃣. {quiz.questions[next_question_index]['options'][1]}\n"
                                f"3️⃣. {quiz.questions[next_question_index]['options'][2]}\n"
                                f"4️⃣. {quiz.questions[next_question_index]['options'][3]}"),
                    reply_markup=inline.quiz_question_keyboard(quiz_id, next_question_index, correct_answers_count)
                )
            else:
                user_db.add_solved_quiz(
                    user_id=chat_id,
                    quiz_id=quiz_id,
                    score=correct_answers_count
                )

                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"{response_text}\n\n🎉 Вы прошли викторину!\n"
                         f"Ваш результат: {correct_answers_count} из {len(quiz.questions)} правильных ответов.",
                    reply_markup=inline.back_to_main_menu_button()
                )



        except Exception as e:
            logger.error(f"Error in quiz_answer_callback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка при обработке вашего ответа. Пожалуйста, попробуйте снова позже."
            )
