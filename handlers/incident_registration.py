import os

import aiofiles
from aiogram import F
from aiogram.types import Message, ReplyKeyboardRemove, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import db, MEDIA_DIR
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
    if not message.text or (message.text and not message.text.strip().replace(" ", "").isdigit()):
        await message.answer(text="Номер этажа должен быть числовым значением")
        return

    await state.update_data(data={"floor": int(message.text.strip().replace(" ", ""))})

    await state.set_state(IncidentRegistrationForm.incident)
    await message.answer(text="Напишите краткое обращение, отправьте фото с описанием или отправьте голосовое сообщение")


@router.message(IncidentRegistrationForm.incident, F.text != "🚫 Отмена")
async def save_incident(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.content_type in [ContentType.TEXT, ContentType.VIDEO, ContentType.VIDEO_NOTE, ContentType.VOICE]:
        content_type = message.content_type

        if content_type == ContentType.TEXT:
            incident = message.text
        else:
            # Если стандартное видео
            if content_type == ContentType.VIDEO:
                file_obj = message.video
                ext = "mp4"

            # Если круглое видел
            elif content_type == ContentType.VIDEO_NOTE:
                file_obj = message.video_note
                ext = "mp4"

            # Если голосовое
            else:
                file_obj = message.voice
                ext = "mp3"

            file_id = file_obj.file_id
            file_info = await message.bot.get_file(file_id)

            file_path = os.path.join(MEDIA_DIR, f"{file_id}.{ext}")

            file = await message.bot.download_file(file_info.file_path)
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file.read())

            incident = file_path

        try:
            # Сохранение обращения в базу данных
            user = await db.get_user(telegram_id=message.from_user.id)
            new_incident = await db.add_incident(
                user_id=user.get("id"),
                incident_description_type=content_type,
                incident=incident,
                floor=data.get("floor")
            )
            await message.answer(
                text=f"✅ Заявка <b>#{new_incident.get('id') if new_incident.get('id') else '-'}</b> успешно отправлена\n"
                     f"🕐 Время регистрации: <b>{new_incident.get('datetime').strftime('%d.%m.%Y %H:%M') if new_incident.get('datetime') else '-'}</b>",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML",
            )

            text = "=== Новое обращение ===\n\n"
            text += f"ID: <b>{new_incident.get('id')}</b>\n"
            text += f"Дата регистрации: <b>{new_incident.get('datetime').strftime('%d.%m.%Y %H:%M') if new_incident.get('datetime') else '-'}</b>\n"
            text += f"ФИО: <b>{data.get('fullname')}</b>\n"
            text += f"Номер телефона: <code>+998{data.get('phone_number')}</code>\n"
            text += f"Этаж: <b>{data.get('floor')}</b>\n"

            if message.text:
                text += f"Тема обращения: <i>{incident}</i>\n"
            else:
                text += f"Тема обращения: 👇\n"

            await message.bot.send_message(
                chat_id=GROUP_ID,
                text=text,
                parse_mode="HTML",
            )

            if not message.text:
                await message.bot.forward_message(
                    chat_id=GROUP_ID,
                    from_chat_id=message.from_user.id,
                    message_id=message.message_id,
                )

            await state.clear()
        except Exception as exp:
            await message.answer(
                text=(f"Произошла ошибка при создании заявки. {exp.__class__.__name__}: {exp}"
                     f"\nПожалуйста, попробуйте отправить обращение заново или "
                     f"свяжитесь с разработчиком: @thedevu101"),
            )
    else:
        await message.answer(
            text="Можно отправлять только текст, видео или аудио сообщения",
        )
