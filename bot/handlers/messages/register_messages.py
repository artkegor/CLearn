from bot.handlers.messages.messages.feedback_messages import messages_handler as feedback_messages_handler
from bot.handlers.messages.messages.task_messages import messages_handler as task_messages_handler
from bot.handlers.messages.messages.tutor_messages import messages_handler as tutor_messages_handler
from bot.handlers.messages.messages.coordinator_messages import messages_handler as coordinator_messages_handler

# Register message handlers with the bot
async def register_messages(bot):
    await feedback_messages_handler(bot)
    await task_messages_handler(bot)
    await tutor_messages_handler(bot)
    await coordinator_messages_handler(bot)
