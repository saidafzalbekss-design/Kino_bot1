from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import PAGE_SIZE
from database import count_movies, get_movies_page
from keyboards import main_menu, movies_kb
from utils import has_vip_access, safe_edit, send_movie, vip_denied_text

router = Router()


@router.callback_query(F.data.startswith("list:"))
async def cb_list(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[1])
    total = await count_movies(vip=False)
    movies = await get_movies_page(page, PAGE_SIZE, vip=False)

    text = "🎬 Kinoni tanlang:" if total else "Hozircha kino yo'q."
    await safe_edit(call.message, text, movies_kb(movies, page, total, "list"))
    await call.answer()


@router.callback_query(F.data.startswith("viplist:"))
async def cb_viplist(call: CallbackQuery) -> None:
    if not await has_vip_access(call.from_user.id):
        await call.answer(vip_denied_text(), show_alert=True)
        return

    page = int(call.data.split(":")[1])
    total = await count_movies(vip=True)
    movies = await get_movies_page(page, PAGE_SIZE, vip=True)

    text = "💎 VIP kinolar:" if total else "💎 Hozircha VIP kino yo'q."
    await safe_edit(call.message, text, movies_kb(movies, page, total, "viplist"))
    await call.answer()


@router.callback_query(F.data.startswith("movie:"))
async def cb_movie(call: CallbackQuery) -> None:
    code = call.data.split(":", 1)[1]
    status = await send_movie(call.message, code, call.from_user.id)
    if status == "ok":
        await call.answer()
    elif status == "vip":
        await call.answer(vip_denied_text(), show_alert=True)
    else:
        await call.answer("Kino topilmadi", show_alert=True)


@router.message(F.text & ~F.text.startswith("/"))
async def by_code(message: Message) -> None:
    status = await send_movie(message, message.text.strip(), message.from_user.id)
    if status == "vip":
        await message.answer(
            vip_denied_text(), reply_markup=main_menu(message.from_user.id)
        )
    elif status == "notfound":
        await message.answer(
            "😕 Bunday kodli kino topilmadi.",
            reply_markup=main_menu(message.from_user.id),
        )


# Admin bo'lmagan kishi admin tugmasini bossa yoki tugma eskirgan bo'lsa
@router.callback_query()
async def fallback(call: CallbackQuery) -> None:
    await call.answer("Ruxsat yo'q yoki tugma eskirgan", show_alert=True)
