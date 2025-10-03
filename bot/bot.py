from config import Config
from telebot.async_telebot import AsyncTeleBot
from bot.handlers.commands import commands_handler
from bot.handlers.callbacks import callbacks_handler

# Initialize the bot with the token from the configuration
bot = AsyncTeleBot(
    token=Config.BOT_TOKEN,
    parse_mode='HTML'
)


# Import handlers to register them with the bot
async def register_handlers():
    await commands_handler(bot)
    await callbacks_handler(bot)
