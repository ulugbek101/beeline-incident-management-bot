from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import db
from router import router
from states.forms import IncidentRegistrationForm
from config import GROUP_ID


async def incident_registration(message: Message, state: FSMContext, floor: int):
    user = await db.get_user(telegram_id=message.from_user.id)

    await state.update_data(data={"fullname": user.get("fullname")})
    await state.update_data(data={"phone_number": user.get("phone_number")})

    markup = ReplyKeyboardBuilder()
    markup.button(text="🚫 Отмена")
    markup.adjust(1)

    await state.update_data(data={"floor": floor})

    await state.set_state(IncidentRegistrationForm.incident)
    await message.answer(
        text="Напишите краткое обращение, отправьте фото с описанием или отправьте голосовое сообщение",
        reply_markup=markup.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    )

@router.message(IncidentRegistrationForm.floor, F.text != "🚫 Отмена")
async def save_floor(message: Message, state: FSMContext):
    if not message.text.strip().replace(" ", "").isdigit():
        await message.answer(text="Номер этажа должен быть числовым значением")
        return

    await state.update_data(data={"floor": int(message.text.strip().replace(" ", ""))})

    await state.set_state(IncidentRegistrationForm.incident)
    await message.answer(text="Напишите краткое обращение, отправьте фото с описанием или отправьте голосовое сообщение")


@router.message(IncidentRegistrationForm.incident, F.text != "🚫 Отмена")
async def save_incident(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.send_message(
        chat_id=GROUP_ID,
        text=f"ФИО: {data.get('fullname')}\nНомер телефона: +998{data.get('phone_number')}\nЭтаж: {data.get('floor')}",
    )
    await message.bot.forward_message(
        chat_id=GROUP_ID,
        from_chat_id=message.from_user.id,
        message_id=message.message_id,
    )

    await state.clear()

    await message.answer(
        text="✅ Заявка успешно отправлена",
        reply_markup=ReplyKeyboardRemove(),
    )
