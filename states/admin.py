from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    video = State()
    code = State()
    title = State()
    vip = State()
