import asyncio
import logging

from loader import dp, bot, db
from handlers import cancel
from handlers.start import router
from utils.commands import set_bot_commands

async def main():
    await db.connect()
    await db.create_users_table()
    await db.create_incidents_table()
    await db.migrate_add_document_caption()
    await db.migrate_datetime_default()
    await bot.delete_webhook(drop_pending_updates=True)

    await set_bot_commands(bot=bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    dp.include_router(router=router)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
