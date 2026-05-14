from aiogram.types import Message
from aiogram.fsm.context import FSMContext


async def incident_registration(message: Message, state: FSMContext):
    await message.answer(text="Регистрация инцидента")
