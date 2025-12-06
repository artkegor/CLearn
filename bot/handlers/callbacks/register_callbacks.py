from bot.handlers.callbacks.callbacks.base_callbacks import callbacks_handler as base_callbacks_handler
from bot.handlers.callbacks.callbacks.task_callbacks import callbacks_handler as task_callbacks_handler
from bot.handlers.callbacks.callbacks.quiz_callbacks import callbacks_handler as quiz_callbacks_handler


async def register_callbacks(bot):
    await base_callbacks_handler(bot)
    await task_callbacks_handler(bot)
    await quiz_callbacks_handler(bot)
