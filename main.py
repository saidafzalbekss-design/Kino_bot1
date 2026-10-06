import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN
from database import init_db
from handlers import admin, start, user


async def start_web_server() -> web.AppRunner:
    """Render Web Service port kutadi, shuning uchun kichik web server ishga tushiramiz.
    UptimeRobot shu manzilga so'rov yuborib, servisni uyg'oq ushlab turadi."""

    async def health(_: web.Request) -> web.Response:
        return web.Response(text="Bot ishlayapti")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    logging.info("Web server %s portda ishga tushdi", port)
    return runner


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. Render'da Environment Variables ga qo'shing.")

    await init_db()
    runner = await start_web_server()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin handlerlari user'ning umumiy (catch-all) handleridan oldin turishi kerak
    dp.include_routers(start.router, admin.router, user.router)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
