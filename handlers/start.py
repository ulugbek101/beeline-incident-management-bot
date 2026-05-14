from aiogram import types
from aiogram.filters.command import CommandStart, CommandObject

from router import router


@router.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    floor = command.args

    if floor is None:
        # Plain /start — no QR code used
        await message.answer("Assalomu alaykum! Iltimos, qavatdagi QR-kodni skaner qiling.")
        return

    if not floor.isdigit():
        await message.answer("Запуск бота возможен только с помощью ссылки, которую вы можете получить отсканировава QR код")
        return

    # Deep link with a valid floor number — route to incident flow
    await message.answer(f"{floor}-qavatdan xabar qabul qilindi. Muammoni tasvirlab bering.")
