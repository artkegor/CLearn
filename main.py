import os
import asyncio
from telebot.types import BotCommand
from logging_config import setup_logging
from bot.bot import bot, register_handlers
from telebot.async_telebot import asyncio_filters
import agents.task_generator.agent_instance as agent_instance
from agents.task_generator.agent.task_generator import TaskGenerator


# Main entry point for the bot
async def main():
    # Set environment variable to disable tokenizers parallelism
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Set up logging and get bot information
    logger = setup_logging()
    bot_info = await bot.get_me()

    # Import and register handlers
    bot.add_custom_filter(
        custom_filter=asyncio_filters.StateFilter(bot)
    )
    await register_handlers()

    # Set bot commands
    await bot.set_my_commands(
        commands=[
            BotCommand('start', 'Запустить бота')
        ]
    )

    # Initialize agents
    agent_instance.task_generator = TaskGenerator()
    logger.info("Task Generator agent initialized.")

    # Start bot polling
    logger.info("Starting the bot...")
    logger.info(f"Bot started as @{bot_info.username}")
    await bot.infinity_polling()


# Run the main function if this script is executed
if __name__ == '__main__':
    asyncio.run(main())
