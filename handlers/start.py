from aiogram import types
from aiogram.filters.command import CommandStart, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from router import router
from loader import db
from states.forms import IncidentRegistrationForm
from handlers.user_registration import user_registration
from handlers.incident_registration import incident_registration


@router.message(Command(commands=["start", "create_incident"], prefix="/"))
async def start(message: types.Message, command: CommandObject, state: FSMContext):
    if message.chat.type != "private":
        await message.answer(text="Обращения в бот должны происходить на странице самого бота, а не в группе")
        return

    floor = command.args

    user = await db.get_user(telegram_id=message.from_user.id)

    # Команда /start без QR кода и сотрудник ранее не был зарегистрирован в системе
    # if not floor and not user:
    #     await message.answer(f"Здравствуйте {message.from_user.full_name}. Пожалуйста отсканируйте QR код")
    #     return

    # Если QR код - не числовое значение
    if floor and not floor.isdigit():
        await message.answer("Ссылка - неверна, пожалуйста отсканируйте QR код заново")
        return

    # QR код верный, но сотрудник обращается в 1-раз - начинаем его регистрацию
    if not floor or (not user and floor and floor.isdigit()):
        await state.update_data(data={"floor": floor})
        await user_registration(message=message, state=state)
        return

    else:
        if floor:
            await incident_registration(message=message, state=state, floor=int(floor))
        else:
            markup = ReplyKeyboardBuilder()
            markup.button(text="🚫 Отмена")
            markup.adjust(1)

            await state.update_data(data={"fullname": user.get('fullname')})
            await state.update_data(data={"phone_number": user.get('phone_number')})

            await state.set_state(IncidentRegistrationForm.floor)
            await message.answer(
                text="Номер этажа",
                reply_markup=markup.as_markup(
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
            )

