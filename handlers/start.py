from aiogram import types
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from router import router
from loader import db

from handlers.user_registration import user_registration
from handlers.incident_registration import incident_registration


@router.message(CommandStart())
async def start(message: types.Message, command: CommandObject, state: FSMContext):
    floor = command.args

    user = await db.get_user(telegram_id=message.from_user.id)

    # Команда /start без QR кода и сотрудник ранее не был зарегистрирован в системе
    if floor is None and not user:
        await message.answer(f"Здравствуйте {message.from_user.full_name}. Пожалуйста отсканируйте QR код")
        return

    # Если QR код - не числовое значение
    if floor and not floor.isdigit():
        await message.answer("Ссылка - неверна, пожалуйста отсканируйте QR код заново")
        return

    # QR код верный, но сотрудник обращается в 1-раз - начинаем его регистрацию
    if not user:
        await user_registration(message=message, state=state)

    else:
        await incident_registration(message=message, state=state)

