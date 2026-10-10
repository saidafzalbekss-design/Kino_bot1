from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

from config import ADMIN_IDS, VIP_CONTACT
from database import get_movie, is_vip

LIST_PREFIXES = (
    "🎬 Kinoni tanlang",
    "Hozircha kino yo'q",
    "💎 VIP kinolar",
    "💎 Hozircha VIP",
)


async def has_vip_access(user_id: int) -> bool:
    return user_id in ADMIN_IDS or await is_vip(user_id)


def vip_denied_text() -> str:
    return (
        "💎 Bu bo'lim faqat VIP a'zolar uchun.\n\n"
        "VIP bo'lish uchun pastdagi tugma orqali adminga shaxsiy xabar yozing."
    )


async def send_movie(target: Message, code: str, user_id: int) -> str:
    movie = await get_movie(code)
    if not movie:
        return "notfound"

    title, file_id, file_type, vip = movie
    if vip and not await has_vip_access(user_id):
        return "vip"

    caption = f"{'💎' if vip else '🎬'} {title}"
    if file_type == "video":
        await target.answer_video(file_id, caption=caption)
    elif file_type == "animation":
        await target.answer_animation(file_id, caption=caption)
    elif file_type == "video_note":
        await target.answer_video_note(file_id)
        await target.answer(caption)
    else:
        await target.answer_document(file_id, caption=caption)
    return "ok"


async def safe_edit(
    message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def show_below(
    call, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    msg = call.message
    if msg.text and msg.text.startswith(LIST_PREFIXES):
        await safe_edit(msg, text, reply_markup)
    else:
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass
        await msg.answer(text, reply_markup=reply_markup)
