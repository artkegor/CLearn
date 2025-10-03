from config import Config
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Constants
themes = Config.C_TOPICS


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
        ) for task_id, text in themes.items()
    ]
    buttons.append(
        InlineKeyboardButton(
            text="⬅️ В главное меню",
            callback_data="back_to_main_menu"
        )
    )
    keyboard.add(*buttons)
    return keyboard
