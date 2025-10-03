from config import Config
from telebot.async_telebot import AsyncTeleBot
from bot.handlers.commands import commands_handler
from bot.handlers.callbacks import callbacks_handler
from bot.handlers.messages import messages_handler
from telebot.asyncio_storage import StateMemoryStorage

# Initialize the bot with the token from the configuration
bot = AsyncTeleBot(
    token=Config.BOT_TOKEN,
    parse_mode='HTML',
    state_storage=StateMemoryStorage()
)

# Import handlers to register them with the bot
async def register_handlers():
    await commands_handler(bot)
    await callbacks_handler(bot)
    await messages_handler(bot)
