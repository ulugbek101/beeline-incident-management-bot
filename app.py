import asyncio
import logging

from loader import dp, bot, db
from handlers.start import router


async def main():
    await db.connect()
    await db.create_users_table()
    await db.create_incidents_table()
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    dp.include_router(router=router)
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
