from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import re

import keyboards
from core import fetch_subtitles_core

router = Router()

youtube_url_pattern = r'(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|live\/|embed\/)?([a-zA-Z0-9_-]{11})(\S*)?'


class fetch_subtitles_FSM(StatesGroup):
    waiting_for_youtube_url = State()


@router.message(F.text == 'Извлечь субтитры из видео')
async def fetch_subtitles_input(message: types.Message, state: FSMContext):
    await state.set_state(fetch_subtitles_FSM.waiting_for_youtube_url)
    await message.answer(
        'Отправьте ссылку на ролик в YouTube',
        reply_markup=keyboards.cancel_input_keyboard(),
    )


@router.message(fetch_subtitles_FSM.waiting_for_youtube_url)
async def youtube_url_entered(message: types.Message, state: FSMContext):
    print("youtube_url: " + message.text)
    if not re.match(youtube_url_pattern, message.text):
        await message.answer(
            'Неверный формат ссылки для ролика из YouTube 🙈\n'
            'Попробуйте ещё раз'
        )
        return
    
    await state.clear()
    youtube_url = message.text

    await fetch_subtitles_core.fetch_subtitles_and_send_to_user(message, youtube_url)
