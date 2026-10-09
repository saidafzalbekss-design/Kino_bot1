from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import main_menu
from utils import safe_edit

router = Router()

WELCOME = "🎬 Salom! Kino kodini yuboring yoki ro'yxatdan tanlang."


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=main_menu(message.from_user.id))


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"🆔 Sizning ID raqamingiz: <code>{message.from_user.id}</code>", parse_mode="HTML")


@router.callback_query(F.data == "home")
async def cb_home(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await safe_edit(call.message, WELCOME, main_menu(call.from_user.id))
    await call.answer()
