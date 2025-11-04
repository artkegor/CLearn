from bot.handlers.commands.commands.start import commands_handler as start_commands_handler


async def register_commands(bot):
    await start_commands_handler(bot)
