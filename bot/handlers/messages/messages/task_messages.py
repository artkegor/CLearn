from config import Config
from database.user_db import UserDB
from database.task_db import TaskDB
from logging_config import setup_logging
import bot.keyboards.inline as inline_keyboards
from compiler.compiler import run_c_task_in_sandbox

# Initialize logger
logger = setup_logging()

# Initialize database
user_db = UserDB()
task_db = TaskDB()

# Constants
FEEDBACK_CHAT_ID = Config.FEEDBACK_CHAT_ID
STATES = Config.BotStates
BOT_ID = Config.BOT_ID


# Handler for task submission messages
async def messages_handler(bot):
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

            solution_id = user_db.add_solution(
                user_id=chat_id,
                task_id=task_id,
                solution_code=downloaded_file.decode('utf-8'),
                score=score,
                log=log
            )

            await bot.send_message(
                chat_id=chat_id,
                text=f"🧪 Результаты тестирования вашего решения:\n\n"
                     f"{log}\n",
                reply_markup=inline_keyboards.after_submission_keyboard(
                    task_id=task_id,
                    solution_id=solution_id
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
