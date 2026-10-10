import logging

from aiogram import BaseMiddleware

from database import add_user


class TrackUsers(BaseMiddleware):
    """Botga yozgan / tugma bosgan har bir yangi odamni bazaga yozadi."""

    def __init__(self) -> None:
        self._seen: set[int] = set()  # har safar bazaga murojaat qilmaslik uchun

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user and not user.is_bot and user.id not in self._seen:
            try:
                await add_user(user.id)
                self._seen.add(user.id)
            except Exception:
                logging.exception("add_user xatosi")
        return await handler(event, data)
