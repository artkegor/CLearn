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
            text="👤 Профиль",
            callback_data="profile"
        ),
        InlineKeyboardButton(
            text="⁉️ Обратная связь",
            callback_data="feedback"
        ),
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
