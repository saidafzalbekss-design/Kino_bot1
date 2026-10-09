from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

from config import ADMIN_IDS, VIP_CONTACT
from database import get_movie, is_vip


async def has_vip_access(user_id: int) -> bool:
    """Adminlar va faol VIP a'zolar uchun True."""
    return user_id in ADMIN_IDS or await is_vip(user_id)


def vip_denied_text() -> str:
    text = "💎 Bu bo'lim faqat VIP a'zolar uchun.\nVIP olish uchun admin bilan bog'laning."
    if VIP_CONTACT:
        text += f"\n{VIP_CONTACT}"
    return text


async def send_movie(target: Message, code: str, user_id: int) -> str:
    """Kodga mos kinoni yuboradi.

    Qaytaradi: "ok" | "notfound" | "vip" (VIP kino, lekin foydalanuvchi VIP emas)
    """
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
    """Xabarni tahrirlaydi; 'message is not modified' xatosini e'tiborsiz qoldiradi."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


LIST_PREFIXES = ("🎬 Kinoni tanlang", "Hozircha kino yo'q", "💎 VIP kinolar", "💎 Hozircha VIP")


async def show_below(
    call, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Bosh menyudan bosilganda natijani menyu TAGIDA yangi xabar qilib chiqaradi.
    Ro'yxat xabarining o'zida (Oldingi/Keyingi) bosilsa, o'sha xabarni tahrirlaydi."""
    msg = call.message
    if msg.text and msg.text.startswith(LIST_PREFIXES):
        await safe_edit(msg, text, reply_markup)
    else:
        await
