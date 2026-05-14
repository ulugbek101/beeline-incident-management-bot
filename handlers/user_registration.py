from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp, db
from states.forms import UserRegistrationForm


async def user_registration(message: Message, state: FSMContext):
    await message.answer(text=f"Здравствуйте {message.from_user.full_name}, вы не найдене в базе данных. Пожалуйста представтесь, как ваше полное имя (Имя и Фамилия) ?")
    await state.set_state(UserRegistrationForm.fullname)



@dp.message(UserRegistrationForm.fullname)
async def save_fullname(message: Message, state: FSMContext):
    await message.answer(text="✅ Имя и Фамилия успешно сохранены")
    await state.update_data(data={"fullname": message.text})

    markup = ReplyKeyboardBuilder()
    markup.button(text="📞 Поделиться контактом", request_contact=True)
    markup.adjust(1)

    await message.answer(
        text="👇 Введите свой номер телефона в нижеуказанном формате: \n90 123 45 67 или 901234567\n\nили просто поделитесь контактом нажав на кнопку ниже",
        reply_markup=markup.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    )

    await state.set_state(UserRegistrationForm.phone_number)


@dp.message(UserRegistrationForm.phone_number)
async def save_phone_number(message: Message, state: FSMContext):
    phone_number = None

    if message.text and message.text.strip().replace(" ", "").isdigit() and len(message.text.strip().replace(" ", "")) == 9:
        phone_number = message.text.strip().replace(" ", "")

    elif message.contact and not message.text:
        phone_number = message.contact.phone_number[3:]

    else:
        await message.answer(text="⛔️ Пожалуста, отправьте номер телефона в вышеуказанном формате, не что то другое")
        return

    await message.answer(
        text="✅ Номер телефона успешно сохранен",
        reply_markup=ReplyKeyboardRemove(),
    )

    data = await state.get_data()

    await db.add_user(telegram_id=message.from_user.id, fullname=data.get("fullname", ""), phone_number=phone_number)

    await state.clear()
