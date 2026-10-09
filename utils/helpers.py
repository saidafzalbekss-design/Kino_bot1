async def show_below(
    call, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Menyudagi tugma bosilsa: menyu xabarini o'chiradi, natijani eng pastda yangi xabar qiladi.
    Ro'yxat xabarining o'zida (Oldingi/Keyingi) bosilsa, o'sha xabarni tahrirlaydi."""
    msg = call.message
    if msg.text and msg.text.startswith(LIST_PREFIXES):
        await safe_edit(msg, text, reply_markup)
    else:
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass  # xabar allaqachon o'chgan yoki 48 soatdan eski bo'lsa
        await msg.answer(text, reply_markup=reply_markup)
