from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
import logging
import ast
from dotenv import load_dotenv
import os
from handlers.globe import router
from handlers.back import back_router
from database.core import AsyncCore


load_dotenv()

token = os.getenv('TOKEN')
admin_id = tuple(ast.literal_eval(os.getenv('ADMIN_ID')))

bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_routers(router, back_router)


async def start_bot(bot: Bot):
    for element in admin_id:
        await bot.send_message(chat_id=element, text='Бот запущен!')

dp.startup.register(start_bot)


async def main():
    try:
        await AsyncCore.create_tables()
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO) # Подключение логирования
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
