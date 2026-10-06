import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import admin, start, user


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin handlerlari user'ning umumiy (catch-all) handleridan oldin turishi kerak
    dp.include_routers(start.router, admin.router, user.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
