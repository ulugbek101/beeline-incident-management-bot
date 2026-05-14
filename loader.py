from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from utils.db_api.db import Database

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

db = Database(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, db_name=DB_NAME)
