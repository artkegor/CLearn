from config import Config
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

from bot.handlers.callbacks.register_callbacks import register_callbacks
from bot.handlers.commands.register_commands import register_commands
from bot.handlers.messages.register_messages import register_messages

# Initialize the bot with the token from the configuration
bot = AsyncTeleBot(
    token=Config.BOT_TOKEN,
    parse_mode='HTML',
    state_storage=StateMemoryStorage()
)


# Import handlers to register them with the bot
async def register_handlers():
    await register_commands(bot)
    await register_messages(bot)
    await register_callbacks(bot)
