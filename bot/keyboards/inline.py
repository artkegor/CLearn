from config import Config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Constants
THEMES = Config.C_TOPICS
DIFFICULTIES = Config.TASK_DIFFICULTIES


# Main menu inline keyboard
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            text="🔧 Решить задание",
            callback_data="solve_task"
        ),
        InlineKeyboardButton(
            text="🎬 Пройти викторину",
            callback_data="take_quiz"
        ),
        InlineKeyboardButton(
            text="👤 Профиль",
            callback_data="profile"
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="statistics"
        ),
        InlineKeyboardButton(
            text="⁉️ Обратная связь",
            callback_data="feedback"
        )
    ]
    keyboard.add(*buttons)
    return keyboard


# Back to main menu button
def back_to_main_menu_button():
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    ]
    keyboard.add(*buttons)
    return keyboard


# Statistics keyboard
def statistics_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            text="📈 Краткая статистика",
            callback_data="summary_brief"
        ),
        InlineKeyboardButton(
            text="📊 Подробная статистика",
            callback_data="summary_detailed"
        ),
    ]
    keyboard.add(*buttons)
    return keyboard


# Choose task theme keyboard
def choose_task_theme_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(
            text=text,
            callback_data=f"task_theme_{task_id}"
        ) for task_id, text in THEMES.items()
    ]
    buttons.append(
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    )
    keyboard.add(*buttons)
    return keyboard


# Choose task difficulty keyboard
def choose_task_difficulty_keyboard(theme_id: str):
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [
        InlineKeyboardButton(
            text=text,
            callback_data=f"task_difficulty_{theme_id}_{difficulty_id}"
        ) for difficulty_id, text in DIFFICULTIES.items()
    ]
    buttons.append(
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    )
    keyboard.add(*buttons)
    return keyboard


# Task interaction keyboard
def task_interaction_keyboard(task_id: str):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            "✅ Сдать решение",
            callback_data=f"submit_solution_{task_id}"
        ),
        InlineKeyboardButton(
            text="🧩 Показать решение",
            callback_data=f"show_solution_{task_id}"
        ),
        InlineKeyboardButton(
            text="🔄 Новое задание",
            callback_data="solve_task"
        ),
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    ]
    keyboard.add(*buttons)
    return keyboard


# After submission keyboard
def after_submission_keyboard(task_id: str, solution_id: str):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            text="✅ Сдать другое решение",
            callback_data=f"submit_solution_{task_id}"
        ),
        InlineKeyboardButton(
            text="💡 Проанализировать код",
            callback_data=f"analyze_solution_{solution_id}"
        ),
        InlineKeyboardButton(
            text="🧩 Показать решение",
            callback_data=f"show_solution_{task_id}"
        ),
        InlineKeyboardButton(
            text="🔄 Решить другое задание",
            callback_data="solve_task"
        ),
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    ]
    keyboard.add(*buttons)
    return keyboard


# Choose quiz theme keyboard
def choose_quiz_theme_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(
            text=text,
            callback_data=f"quiz_theme_{theme_id}"
        ) for theme_id, text in THEMES.items()
    ]
    buttons.append(
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    )
    keyboard.add(*buttons)
    return keyboard


# Choose quiz type keyboard
def choose_quiz_type_keyboard(theme_id: str):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            text="⚡️ Блиц-викторина",
            callback_data=f"quiz_type_blitz_{theme_id}"
        ),
        InlineKeyboardButton(
            text="🧠 Мини-викторина",
            callback_data=f"quiz_type_mini_{theme_id}"
        ),
        InlineKeyboardButton(
            text="📚 Полная викторина",
            callback_data=f"quiz_type_full_{theme_id}"
        ),
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    ]
    keyboard.add(*buttons)
    return keyboard


# Quiz question keyboard
def quiz_question_keyboard(quiz_id: str, question_index, correct_answers_count: int):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(
            text="1️⃣",
            callback_data=f"quiz_answer_{quiz_id}_{question_index}_0_{correct_answers_count}"
        ),
        InlineKeyboardButton(
            text="2️⃣",
            callback_data=f"quiz_answer_{quiz_id}_{question_index}_1_{correct_answers_count}"
        ),
        InlineKeyboardButton(
            text="3️⃣",
            callback_data=f"quiz_answer_{quiz_id}_{question_index}_2_{correct_answers_count}"
        ),
        InlineKeyboardButton(
            text="4️⃣",
            callback_data=f"quiz_answer_{quiz_id}_{question_index}_3_{correct_answers_count}"
        )
    ]
    keyboard.add(*buttons)
    return keyboard
