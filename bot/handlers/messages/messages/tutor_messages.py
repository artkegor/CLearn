from config import Config
from logging_config import setup_logging
import bot.keyboards.inline as inline_keyboards
from agents.tutor.agent_instance import answer_question

# Initialize logger
logger = setup_logging()

# Constants
FEEDBACK_CHAT_ID = Config.FEEDBACK_CHAT_ID
STATES = Config.BotStates
BOT_ID = Config.BOT_ID


# Handler for task tutor messages
async def messages_handler(bot):
    @bot.message_handler(func=lambda message: True, state=STATES.WAITING_FOR_TUTOR_QUESTION,
                         content_types=['text', 'photo', 'video', 'document', 'audio'])
    async def handle_tutor_question(message):
        chat_id = message.chat.id
        question = message.text

        if not question:
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Пожалуйста, введите текстовый вопрос для ИИ-репетитора."
            )
            return

        try:
            logger.info(f"Received tutor question from user {chat_id}: {question}")
            tutor_response = answer_question(
                question=question,
                user_id=str(chat_id)
            )

            await bot.send_message(
                chat_id=chat_id,
                text=tutor_response,
                reply_markup=inline_keyboards.back_to_main_menu_button()
            )

            await bot.delete_state(
                chat_id=chat_id,
                user_id=chat_id
            )
        except Exception as e:
            logger.error(f"Error in handle_tutor_question: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка. Пожалуйста, попробуйте снова позже."
            )
