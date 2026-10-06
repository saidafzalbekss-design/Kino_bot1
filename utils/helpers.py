from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

from database import get_movie


async def send_movie(target: Message, code: str) -> bool:
    """Kodga mos kinoni yuboradi. Topilmasa False qaytaradi."""
    movie = await get_movie(code)
    if not movie:
        return False

    title, file_id, file_type = movie
    caption = f"🎬 {title}"
    if file_type == "video":
        await target.answer_video(file_id, caption=caption)
    elif file_type == "animation":
        await target.answer_animation(file_id, caption=caption)
    elif file_type == "video_note":
        await target.answer_video_note(file_id)
        await target.answer(caption)
    else:
        await target.answer_document(file_id, caption=caption)
    return True


async def safe_edit(
    message: Message, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Xabarni tahrirlaydi; 'message is not modified' xatosini e'tiborsiz qoldiradi."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
