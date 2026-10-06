from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS


class IsAdmin(BaseFilter):
    """Foydalanuvchi ADMIN_IDS ro'yxatida bo'lsa True qaytaradi."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and event.from_user.id in ADMIN_IDS
