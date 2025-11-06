import datetime

from config import Config
from database.task_db import TaskDB
from database.user_db import UserDB
from logging_config import setup_logging
from database.feedback_db import FeedbackDB
from telebot.async_telebot import AsyncTeleBot
from models.database_models import FeedbackModel
import bot.keyboards.inline as inline_keyboards
from compiler.compiler import run_c_task_in_sandbox

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()
feedback_db = FeedbackDB()

# Constants
FEEDBACK_CHAT_ID = Config.FEEDBACK_CHAT_ID
STATES = Config.BotStates
BOT_ID = Config.BOT_ID


# Function to handle all messages
async def messages_handler(bot: AsyncTeleBot):
    # Handler for feedback messages
    @bot.message_handler(func=lambda message: True, state=STATES.WAITING_FOR_FEEDBACK,
                         content_types=['text', 'photo', 'video', 'document', 'audio'])
    async def handle_feedback(message):
        time_now = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        chat_id = message.chat.id
        try:
            await bot.send_message(
                chat_id=FEEDBACK_CHAT_ID,
                text=f"📢 Новый отзыв от пользователя @{message.from_user.username} (ID: {chat_id}).\n\n"
                     f"Для ответа, пожалуйста, используйте функцию 'Ответить' на сообщение ниже и отправьте сообщение сюда."
            )

            message_id = await bot.copy_message(
                chat_id=FEEDBACK_CHAT_ID,
                from_chat_id=chat_id,
                message_id=message.message_id
            )

            feedback = FeedbackModel(
                user_id=chat_id,
                message_id=message_id.message_id,
                date=time_now
            )
            feedback_db.add_feedback(
                feedback=feedback
            )

            await bot.send_message(
                chat_id=chat_id,
                text="✅ Спасибо за обратную связь! Мы получили ваше сообщение и обязательно вернемся с ответом.",
                reply_markup=inline_keyboards.main_menu_keyboard()
            )

            await bot.delete_state(
                chat_id=chat_id,
                user_id=chat_id
            )

            logger.info(f"Received feedback from user {chat_id}")
        except Exception as e:
            logger.error(f"Error in handle_feedback: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка при отправке вашего отзыва. Пожалуйста, попробуйте снова позже."
            )

    # Handler for admin responses to feedback
    @bot.message_handler(func=lambda message: message.chat.id == FEEDBACK_CHAT_ID
                                              and message.reply_to_message
                                              and message.reply_to_message.from_user.id == BOT_ID,
                         content_types=['text', 'photo', 'video', 'document', 'audio'])
    async def handle_feedback_response(message):
        try:
            original_message_id = message.reply_to_message.message_id
            feedback = feedback_db.get_feedback(original_message_id)

            if feedback:
                if feedback.status != 'new':
                    await bot.send_message(
                        chat_id=FEEDBACK_CHAT_ID,
                        text="❗ Этот отзыв уже был обработан."
                    )
                    return

                user_id = feedback.user_id
                await bot.send_message(
                    chat_id=user_id,
                    text=f"📢 Ответ на ваш отзыв:"
                )

                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=FEEDBACK_CHAT_ID,
                    message_id=message.message_id
                )

                await bot.send_message(
                    chat_id=FEEDBACK_CHAT_ID,
                    text="✅ Ответ успешно отправлен пользователю."
                )

                feedback_db.mark_feedback_as_answered(original_message_id)
                logger.info(f"Sent feedback response to user {user_id}")
            else:
                await bot.send_message(
                    chat_id=FEEDBACK_CHAT_ID,
                    text="❗ Не удалось найти пользователя для этого отзыва."
                )
        except Exception as e:
            logger.error(f"Error in handle_feedback_response: {e}")
            await bot.send_message(
                chat_id=FEEDBACK_CHAT_ID,
                text="❗ Произошла ошибка при отправке ответа. Пожалуйста, попробуйте снова позже."
            )

    # Handler for task submission messages
    @bot.message_handler(func=lambda message: True, state=STATES.WAITING_FOR_TASK_SOLUTION,
                         content_types=['text', 'photo', 'video', 'document', 'audio'])
    async def handle_task_submission(message):
        if message.content_type != 'document':
            await bot.send_message(
                chat_id=message.chat.id,
                text="❗ Пожалуйста, отправьте ваше решение в виде файла."
            )
            return

        document = message.document
        if not document.file_name.endswith('.c'):
            await bot.send_message(
                chat_id=message.chat.id,
                text="❗ Пожалуйста, отправьте файл с расширением .c"
            )
            return

        chat_id = message.chat.id
        async with bot.retrieve_data(
                chat_id=chat_id,
                user_id=chat_id
        ) as data:
            task_id = data.get("current_task_id")

        try:
            file_info = await bot.get_file(document.file_id)
            file_path = file_info.file_path
            downloaded_file = await bot.download_file(file_path)

            user_file_path = f'temp/{chat_id}_{task_id}_solution.c'
            with open(user_file_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            task = TaskDB().tasks.find_one({"task_id": task_id})
            test_cases = task.get("test_cases", [])

            result = await run_c_task_in_sandbox(
                filename=user_file_path,
                test_cases=test_cases
            )

            log = result["log"]
            passed = result["passed"]
            total = result["total"]
            score = (passed / total) * 100 if total > 0 else 0

            await bot.send_message(
                chat_id=chat_id,
                text=f"🧪 Результаты тестирования вашего решения:\n\n"
                     f"{log}\n",
                reply_markup=inline_keyboards.after_submission_keyboard(
                    task_id=task_id
                )
            )

            await bot.delete_state(
                chat_id=chat_id,
                user_id=chat_id
            )

            logger.info(f"Processed task submission from user {chat_id} for task {task_id}")
        except Exception as e:
            logger.error(f"Error in handle_task_submission: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="❗ Произошла ошибка при обработке вашего решения. Пожалуйста, попробуйте снова позже."
            )
