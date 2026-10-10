import hashlib
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import BOT_TOKEN
from database import init_db
from handlers import admin, start, user
from middlewares import TrackUsers

# Render o'zi RENDER_EXTERNAL_URL beradi (masalan https://kino-bot.onrender.com)
BASE_URL = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = hashlib.sha256((BOT_TOKEN or "").encode()).hexdigest()[:32]


async def health(_: web.Request) -> web.Response:
    return web.Response(text="Bot ishlayapti")


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    await init_db()
    await bot.set_webhook(
        url=f"{BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dispatcher.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    logging.info("Webhook o'rnatildi: %s%s", BASE_URL, WEBHOOK_PATH)


async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. Render'da Environment Variables ga qo'shing.")
    if not BASE_URL:
        raise SystemExit("WEBHOOK_URL yoki RENDER_EXTERNAL_URL topilmadi.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin handlerlari user'ning umumiy (catch-all) handleridan oldin turishi kerak
    dp.include_routers(start.router, admin.router, user.router)
    tracker = TrackUsers()
    dp.message.outer_middleware(tracker)
    dp.callback_query.outer_middleware(tracker)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
