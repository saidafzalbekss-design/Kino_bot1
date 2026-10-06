from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import ADMIN_IDS, PAGE_SIZE


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu(user_id: int) -> InlineKeyboardMarkup:
    rows = [[_btn("🎬 Kinolar ro'yxati", "list:0")]]
    if user_id in ADMIN_IDS:
        rows.append(
            [
                _btn("➕ Kino qo'shish", "add"),
                _btn("🗑 Kino o'chirish", "dellist:0"),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


CANCEL_TEXT = "❌ Bekor qilish"


def cancel_reply_kb() -> ReplyKeyboardMarkup:
    """Kino qo'shish paytida pastda chiqadigan oddiy (reply) tugma."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        input_field_placeholder="Kinoni shu yerga yuboring...",
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn(CANCEL_TEXT, "cancel")]])


def movies_kb(movies, page: int, total: int, mode: str) -> InlineKeyboardMarkup:
    """
    movies: [(code, title), ...]
    mode:   'list'    -> kinoni ko'rish
            'dellist' -> kinoni o'chirish (faqat admin)
    """
    rows = []
    for code, title in movies:
        if mode == "list":
            rows.append([_btn(f"🎬 {title}"[:60], f"movie:{code}")])
        else:
            rows.append([_btn(f"🗑 {code} — {title}"[:60], f"del:{code}")])

    nav = []
    if page > 0:
        nav.append(_btn("◀️ Oldingi", f"{mode}:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(_btn("Keyingi ▶️", f"{mode}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn("🏠 Bosh menyu", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_kb(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn("✅ Ha, o'chirish", f"delyes:{code}"),
                _btn("↩️ Yo'q", "dellist:0"),
            ]
        ]
    )
