from config import Config
from database.user_db import UserDB
from database.task_db import TaskDB
from logging_config import setup_logging
import bot.keyboards.inline as inline_keyboards
from agents.coordinator.coordinator.coordinator import get_session_statistics, coordinator

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()
task_db = TaskDB()

# Constants
FEEDBACK_CHAT_ID = Config.FEEDBACK_CHAT_ID
STATES = Config.BotStates
BOT_ID = Config.BOT_ID


async def messages_handler(bot):
    @bot.message_handler(func=lambda message: True, state=STATES.WAITING_FOR_MAGIC_AGENT_INPUT,
                         content_types=['text'])
    async def handle_task_submission(message):
        user_input = message.text
        result = coordinator.invoke(
            {
                "messages": [{"role": "user", "content": user_input}]
            }
        )
        response = result["messages"][-1].content
        await bot.send_message(
            chat_id=message.chat.id,
            text=response,
            reply_markup=inline_keyboards.back_to_main_menu_button()
        )
