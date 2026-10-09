

async def show_below(
    call, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Bosh menyudan bosilganda natijani menyu TAGIDA yangi xabar qilib chiqaradi.
    Ro'yxat xabarining o'zida (Oldingi/Keyingi) bosilsa, o'sha xabarni tahrirlaydi."""
    msg = call.message
    if msg.text and msg.text.startswith(LIST_PREFIXES):
        await safe_edit(msg, text, reply_markup)
    else:
        await msg.answer(text, reply_markup=reply_markup)


LIST_PREFIXES = ("🎬 Kinoni tanlang", "Hozircha kino yo'q", "💎 VIP kinolar", "💎 Hozircha VIP")
