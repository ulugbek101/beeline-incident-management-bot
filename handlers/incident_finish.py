from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from router import router
from loader import db
from config import GROUP_ID


@router.callback_query(lambda call: "solved" in call.data)
async def solve_incident(call: CallbackQuery):
    if "finished" in call.data:
        await call.answer(text="Инцидент уже решён ✅", show_alert=True)
        return

    user = await db.get_user(telegram_id=call.from_user.id)
    if not user:
        await call.answer(text="Вы не зарегистрированы в боте", show_alert=True)
        return

    incident_id = int(call.data.split(":")[-1])

    markup = InlineKeyboardBuilder()
    markup.button(text="Решено ✅", callback_data=f"solved:finished:{incident_id}")
    markup.adjust(1)

    await db.finish_incident(user_id=user.get('id'), incident_id=incident_id)
    await call.message.edit_reply_markup(
        reply_markup=markup.as_markup(),
    )
    await call.answer(text="Инцидент успешно решён ✅", show_alert=True)

    incident_data = await db.get_incident(id=incident_id)
    if not incident_data:
        return

    solver = await db.get_user(user_id=incident_data.get('solved_by'))
    initiator = await db.get_user(user_id=incident_data.get('user_id'))
    incident_solved_by = solver.get('fullname') if solver else '-'
    incident_initiator_telegram_id = initiator.get('telegram_id') if initiator else None

    text = f"Инцидент решён ✅\n"
    text += f"ID: <b>#{incident_data.get('id')}</b>\n"
    text += f"Решивший сотрудник: <b>{incident_solved_by}</b>"

    try:
        await call.bot.send_message(
            chat_id=GROUP_ID,
            text=text,
            parse_mode="HTML",
        )
    except Exception as exp:
        await call.message.answer(
            text=("Произошла ошибка при отправке сообщения об изменении статуса инцидента\n"
                  f"{exp.__class__.__name__}: {exp}\n"
                  f"Пожалуйста, свяжитесь с разработчиком: @thedevu101"),
        )

    try:
        await call.bot.send_message(
            chat_id=incident_initiator_telegram_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as exp:
        await call.message.answer(
            text=("Произошла ошибка при отправке сообщения об изменении статуса инцидента\n"
                  f"{exp.__class__.__name__}: {exp}\n"
                  f"Пожалуйста, свяжитесь с разработчиком: @thedevu101"),
        )
