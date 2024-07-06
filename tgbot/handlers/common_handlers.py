from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import keyboards


router = Router()

@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        'Привет! 👋\n'
        'Я Бот-транскриптор 🤗\n'
        'C помощью меня вы можете перевести видео в текст 📝\n'
        'Чтобы начать, нажмите на одну из предложенных ниже кнопок',
        reply_markup=keyboards.main_keyboard(),
    )


@router.message(F.text == 'Отменить текущий ввод')
async def cancel_current_video_input(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Ввод данных для видео был отменен 👌',
        reply_markup=keyboards.main_keyboard(),
    )
    print('Current video input was canceled')