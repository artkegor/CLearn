from config import Config
from telebot.async_telebot import AsyncTeleBot

# Initialize the bot with the token from the configuration
bot = AsyncTeleBot(Config.BOT_TOKEN, parse_mode='HTML')
