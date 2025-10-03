import asyncio
from telebot.types import BotCommand
from bot.bot import bot, register_handlers
from logging_config import setup_logging


# Main entry point for the bot
async def main():
    # Set up logging and get bot information
    logger = setup_logging()
    bot_info = await bot.get_me()

    # Import and register handlers
    await register_handlers()

    # Set bot commands
    await bot.set_my_commands(
        commands=[
            BotCommand('start', 'Запустить бота')
        ]
    )

    # Start bot polling
    logger.info("Starting the bot...")
    logger.info(f"Bot started as @{bot_info.username}")
    await bot.infinity_polling()


# Run the main function if this script is executed
if __name__ == '__main__':
    asyncio.run(main())
