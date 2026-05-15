from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot):
    await bot.set_my_commands(
        commands=[
            BotCommand(
                command="start",
                description="Запуск бота",
            ),
            BotCommand(
                command="help",
                description="Руководство",
            ),
        ]
    )
