import asyncio
from bot.bot import bot
from logging_config import setup_logging


# Main entry point for the bot
async def main():
    logger = setup_logging()
    logger.info("Starting the bot...")
    await bot.infinity_polling()


# Run the main function if this script is executed
if __name__ == '__main__':
    asyncio.run(main())
