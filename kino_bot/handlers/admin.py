import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from config import PAGE_SIZE
from database import (
    add_movie,
    count_movies,
    delete_movie,
    get_movies_page,
    movie_exists,
)
from filters import IsAdmin
from keyboards import (
    CANCEL_TEXT,
    cancel_reply_kb,
    confirm_delete_kb,
    main_menu,
    movies_kb,
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

    try:
        await add_movie(data["code"], title, data["file_id"], data["file_type"])
    except aiosqlite.IntegrityError:
        await message.answer("⚠️ Bu kod allaqachon band. Boshqa kod kiriting:", reply_markup=cancel_reply_kb())
        await state.set_state(AddMovie.code)
        return

    await _finish(
        message,
        state,
        f"✅ Kino qo'shildi!\nKod: {data['code']}\nNomi: {title}",
    )


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
