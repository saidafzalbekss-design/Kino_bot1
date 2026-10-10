from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import ADMIN_IDS, PAGE_SIZE, VIP_CONTACT


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu(user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [_btn("🎬 Kinolar ro'yxati", "list:0")],
        [_btn("💎 VIP kinolar", "viplist:0")],
    ]
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
    movies: [(code, title, is_vip), ...]
    mode:   'list'    -> oddiy kinolarni ko'rish
            'viplist' -> VIP kinolarni ko'rish
            'dellist' -> kinoni o'chirish (faqat admin)
    """
    rows = []
    for code, title, is_vip in movies:
        if mode in ("list", "viplist"):
            icon = "💎" if is_vip else "🎬"
            rows.append([_btn(f"{icon} {title}"[:60], f"movie:{code}")])
        else:
            icon = "💎 " if is_vip else ""
            rows.append([_btn(f"🗑 {icon}{code} — {title}"[:60], f"del:{code}")])

    nav = []
    if page > 0:
        nav.append(_btn("◀️ Oldingi", f"{mode}:{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(_btn("Keyingi ▶️", f"{mode}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([_btn("🏠 Bosh menyu", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vip_choice_kb() -> InlineKeyboardMarkup:
    """Kino qo'shishda: oddiy yoki VIP tanlash."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn("🎬 Oddiy", "vipsel:0"),
                _btn("💎 VIP", "vipsel:1"),
            ]
        ]
    )


def confirm_delete_kb(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _btn("✅ Ha, o'chirish", f"delyes:{code}"),
                _btn("↩️ Yo'q", "dellist:0"),
            ]
        ]
    )
def vip_contact_kb() -> InlineKeyboardMarkup:
    """VIP olmoqchi bo'lganlar uchun: admin lichkasiga o'tish tugmalari."""
    usernames = [u.strip().lstrip("@") for u in VIP_CONTACT.split(",") if u.strip()]
    rows = []
    for i, username in enumerate(usernames, start=1):
        label = "✍️ Adminga yozish" if len(usernames) == 1 else f"✍️ {i}-adminga yozish"
        rows.append([InlineKeyboardButton(text=label, url=f"https://t.me/{username}")])
    rows.append([_btn("🏠 Bosh menyu", "home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
