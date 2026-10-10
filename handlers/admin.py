from datetime import datetime, timezone

import asyncpg
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import PAGE_SIZE
from database import (
    add_movie,
    add_vip,
    count_movies,
    delete_movie,
    get_movie,
    get_movies_page,
    list_vips,
    movie_exists,
    remove_vip,
    set_movie_vip,
)
from filters import IsAdmin
from keyboards import (
    CANCEL_TEXT,
    cancel_reply_kb,
    confirm_delete_kb,
    main_menu,
    movies_kb,
    vip_choice_kb,
)
from states import AddMovie
from utils import safe_edit

MAX_CODE_LEN = 20  # callback_data 64 bayt bilan cheklangan
MAX_TITLE_LEN = 900  # caption limiti 1024 belgi

router = Router()
# Bu routerdagi hamma handler faqat adminlar uchun
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ============ Kino qo'shish ============
async def _begin_add(message: Message, state: FSMContext, user_id: int) -> None:
    """Kino qo'shishni boshlaydi: holatni o'rnatadi va reply tugma bilan so'raydi."""
    await state.clear()
    await state.set_state(AddMovie.video)
    await message.answer(
        "🎥 Kinoni (video yoki fayl ko'rinishida) yuboring.\n\n"
        "Bekor qilish uchun pastdagi tugmani bosing.",
        reply_markup=cancel_reply_kb(),
    )


async def _finish(message: Message, state: FSMContext, text: str) -> None:
    """Holatni tozalaydi, reply tugmani olib tashlaydi va bosh menyuni ko'rsatadi."""
    await state.clear()
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await message.answer(WELCOME_ADMIN, reply_markup=main_menu(message.chat.id))


WELCOME_ADMIN = "🏠 Bosh menyu:"


@router.message(Command("addmovie"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await _begin_add(message, state, message.from_user.id)


@router.callback_query(F.data == "add")
async def cb_add(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _begin_add(call.message, state, call.from_user.id)


# --- Bekor qilish (buyruq, inline tugma va reply tugma) ---
@router.message(Command("cancel"))
@router.message(F.text == CANCEL_TEXT)
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await _finish(message, state, "❌ Bekor qilindi.")


@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await _finish(call.message, state, "❌ Bekor qilindi.")


# --- 1-qadam: video / fayl ---
@router.message(AddMovie.video, F.video | F.document | F.animation | F.video_note)
async def got_video(message: Message, state: FSMContext) -> None:
    if message.video:
        file_id, file_type = message.video.file_id, "video"
    elif message.animation:
        file_id, file_type = message.animation.file_id, "animation"
    elif message.video_note:
        file_id, file_type = message.video_note.file_id, "video_note"
    else:
        file_id, file_type = message.document.file_id, "document"

    await state.update_data(file_id=file_id, file_type=file_type)
    await state.set_state(AddMovie.code)
    await message.answer(
        "🔢 Kino uchun kod kiriting (masalan: 101):",
        reply_markup=cancel_reply_kb(),
    )


@router.message(AddMovie.video)
async def wrong_video(message: Message) -> None:
    await message.answer(
        "⚠️ Iltimos, video yoki fayl yuboring.",
        reply_markup=cancel_reply_kb(),
    )


# --- 2-qadam: kod ---
@router.message(AddMovie.code, F.text)
async def got_code(message: Message, state: FSMContext) -> None:
    code = message.text.strip()

    if not code or code.startswith("/") or len(code) > MAX_CODE_LEN:
        await message.answer(
            f"⚠️ Kod noto'g'ri (buyruq bo'lmasin, {MAX_CODE_LEN} belgidan oshmasin). "
            "Qayta kiriting:",
            reply_markup=cancel_reply_kb(),
        )
        return

    if await movie_exists(code):
        await message.answer(
            "⚠️ Bu kod band. Boshqa kod kiriting:", reply_markup=cancel_reply_kb()
        )
        return

    await state.update_data(code=code)
    await state.set_state(AddMovie.title)
    await message.answer(
        "📝 Kino nomini (tavsifini) kiriting:", reply_markup=cancel_reply_kb()
    )


@router.message(AddMovie.code)
async def wrong_code(message: Message) -> None:
    await message.answer("⚠️ Kodni matn ko'rinishida yuboring.", reply_markup=cancel_reply_kb())


# --- 3-qadam: nom ---
@router.message(AddMovie.title, F.text)
async def got_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    title = message.text.strip()

    if not title or title.startswith("/"):
        await message.answer("⚠️ Nom noto'g'ri. Qayta kiriting:", reply_markup=cancel_reply_kb())
        return
    title = title[:MAX_TITLE_LEN]

    if not data.get("file_id"):
        # Holat buzilgan bo'lsa (masalan bot qayta ishga tushgan)
        await _finish(message, state, "⚠️ Xatolik: video topilmadi. Qaytadan boshlang.")
        return

    await state.update_data(title=title)
    await state.set_state(AddMovie.vip)
    await message.answer("Bu kino qaysi bo'limga qo'shilsin?", reply_markup=vip_choice_kb())


# --- 4-qadam: oddiy yoki VIP ---
@router.callback_query(AddMovie.vip, F.data.startswith("vipsel:"))
async def got_vip_choice(call: CallbackQuery, state: FSMContext) -> None:
    is_vip = call.data.split(":")[1] == "1"
    data = await state.get_data()
    await call.answer()

    if not data.get("file_id") or not data.get("code") or not data.get("title"):
        await _finish(call.message, state, "⚠️ Xatolik: ma'lumot topilmadi. Qaytadan boshlang.")
        return

    try:
        await add_movie(
            data["code"], data["title"], data["file_id"], data["file_type"], is_vip
        )
    except asyncpg.UniqueViolationError:
        await call.message.answer(
            "⚠️ Bu kod allaqachon band. Boshqa kod kiriting:",
            reply_markup=cancel_reply_kb(),
        )
        await state.set_state(AddMovie.code)
        return

    section = "💎 VIP" if is_vip else "🎬 Oddiy"
    await _finish(
        call.message,
        state,
        f"✅ Kino qo'shildi!\nKod: {data['code']}\nNomi: {data['title']}\nBo'lim: {section}",
    )


@router.message(AddMovie.vip)
async def wrong_vip(message: Message) -> None:
    await message.answer("⚠️ Yuqoridagi tugmalardan birini tanlang.", reply_markup=vip_choice_kb())


@router.message(AddMovie.title)
async def wrong_title(message: Message) -> None:
    await message.answer("⚠️ Nomni matn ko'rinishida yuboring.", reply_markup=cancel_reply_kb())


# ============ Kino o'chirish ============
@router.callback_query(F.data.startswith("dellist:"))
async def cb_dellist(call: CallbackQuery) -> None:
    page = int(call.data.split(":")[1])
    total = await count_movies()
    movies = await get_movies_page(page, PAGE_SIZE)

    text = "🗑 O'chirish uchun kinoni tanlang:" if total else "Hozircha kino yo'q."
    await safe_edit(call.message, text, movies_kb(movies, page, total, "dellist"))
    await call.answer()


@router.callback_query(F.data.startswith("del:"))
async def cb_del_confirm(call: CallbackQuery) -> None:
    code = call.data.split(":", 1)[1]
    await safe_edit(
        call.message,
        f"❓ {code} kodli kinoni o'chirasizmi?",
        confirm_delete_kb(code),
    )
    await call.answer()


@router.callback_query(F.data.startswith("delyes:"))
async def cb_del_yes(call: CallbackQuery) -> None:
    code = call.data.split(":", 1)[1]
    await delete_movie(code)

    total = await count_movies()
    movies = await get_movies_page(0, PAGE_SIZE)
    text = (
        "🗑 O'chirildi.\n\nYana o'chirish uchun tanlang:"
        if total
        else "🗑 O'chirildi. Kino qolmadi."
    )
    await safe_edit(call.message, text, movies_kb(movies, 0, total, "dellist"))
    await call.answer()


# ============ VIP boshqaruvi ============
@router.message(Command("addvip"))
async def cmd_addvip(message: Message, command: CommandObject, bot: Bot) -> None:
    args = (command.args or "").split()
    ok = (
        1 <= len(args) <= 2
        and args[0].isdigit()
        and (len(args) == 1 or (args[1].isdigit() and int(args[1]) > 0))
    )
    if not ok:
        await message.answer(
            "Foydalanish:\n"
            "/addvip <user_id> — muddatsiz VIP\n"
            "/addvip <user_id> <kun> — masalan: /addvip 123456789 30"
        )
        return

    user_id = int(args[0])
    days = int(args[1]) if len(args) == 2 else None
    await add_vip(user_id, days)

    term = "muddatsiz" if days is None else f"{days} kun"
    await message.answer(f"✅ {user_id} VIP qilindi ({term}).")
    try:
        await bot.send_message(
            user_id, f"💎 Tabriklaymiz! Sizga VIP berildi ({term}).\n/start ni bosing."
        )
    except Exception:
        pass  # foydalanuvchi botni hali ishga tushirmagan bo'lishi mumkin


@router.message(Command("delvip"))
async def cmd_delvip(message: Message, command: CommandObject) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Foydalanish: /delvip <user_id>")
        return
    if await remove_vip(int(arg)):
        await message.answer(f"🗑 {arg} VIP ro'yxatdan o'chirildi.")
    else:
        await message.answer("Bu foydalanuvchi VIP ro'yxatda yo'q.")


@router.message(Command("vips"))
async def cmd_vips(message: Message) -> None:
    rows = await list_vips()
    if not rows:
        await message.answer("Hozircha VIP foydalanuvchi yo'q.")
        return
    lines = ["💎 VIP foydalanuvchilar:"]
    for user_id, expires in rows:
        if expires is None:
            until = "muddatsiz"
        else:
            until = datetime.fromtimestamp(expires, timezone.utc).strftime("%d.%m.%Y") + " gacha"
        lines.append(f"{user_id} — {until}")
    await message.answer("\n".join(lines))


@router.message(Command("movievip"))
async def cmd_movievip(message: Message, command: CommandObject) -> None:
    """Mavjud kinoni VIP <-> oddiy qilib almashtiradi."""
    code = (command.args or "").strip()
    if not code:
        await message.answer("Foydalanish: /movievip <kino_kodi>")
        return
    movie = await get_movie(code)
    if not movie:
        await message.answer("😕 Bunday kodli kino topilmadi.")
        return
    new_state = not movie[3]
    await set_movie_vip(code, new_state)
    await message.answer(
        f"{code} — {movie[0]}\nEndi: {'💎 VIP' if new_state else '🎬 Oddiy'}"
    )
