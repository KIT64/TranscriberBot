from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import pytube
import re
from datetime import datetime

import keyboards
from core import transcribe_core


router = Router()

youtube_url_pattern = r'(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|live\/|embed\/)?([a-zA-Z0-9_-]{11})(\S*)?'
hms_time_pattern = r'^(\d){1,2}:(\d){2}:(\d){2}$'  # H/HH:MM:SS format
ms_time_pattern = r'^(\d){1,2}:(\d){2}$'  # M/MM:SS format


class video_transcription_FSM(StatesGroup):
    waiting_for_youtube_url = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


@router.message(F.text == 'Сделать транскрипцию видео')
async def start_video_transcription_input(message: types.Message, state: FSMContext):
    await state.set_state(video_transcription_FSM.waiting_for_youtube_url)
    await message.answer(
        'Отправьте ссылку на ролик в YouTube',
        reply_markup=keyboards.cancel_input_keyboard(),
    )


@router.message(video_transcription_FSM.waiting_for_youtube_url)
async def youtube_url_entered(message: types.Message, state: FSMContext):
    print("youtube_url: " + message.text)
    if not re.match(youtube_url_pattern, message.text):
        await message.answer(
            'Неверный формат ссылки для ролика из YouTube 🙈\n'
            'Попробуйте ещё раз'
        )
        return
    await state.update_data(youtube_url=message.text)

    await state.set_state(video_transcription_FSM.waiting_for_start_time)
    await message.answer(
        'Отправьте время начала эпизода в формате: ч:мм:сс или мм:сс\n'
        'Или нажмите "Пропустить", чтобы начать транскрипцию с начала видео',
        reply_markup=keyboards.skip_time_inline_keyboard(),
    )


@router.callback_query(video_transcription_FSM.waiting_for_start_time, F.data == 'skip_time_input')
async def start_time_skipped(callback: types.CallbackQuery, state: FSMContext):
    print("start_time: skipped")
    await callback.answer('Время начала эпизода пропущено')
    await state.update_data(start_time=None)

    await state.set_state(video_transcription_FSM.waiting_for_end_time)
    await callback.message.answer(
        'Отправьте время окончания эпизода в формате: ч:мм:сс или мм:сс"\n'
        'Или нажмите "Пропустить", чтобы провести транскрипцию до конца видео',
        reply_markup=keyboards.skip_time_inline_keyboard(),
    )


@router.message(video_transcription_FSM.waiting_for_start_time)
async def start_time_entered(message: types.Message, state: FSMContext):
    input_start_time = message.text
    print("start_time: " + input_start_time)
    if re.match(hms_time_pattern, input_start_time):
        try:
            time_object = datetime.strptime(input_start_time, '%H:%M:%S')
            start_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
        except Exception as e:
            await message.answer(
                'Пожалуйста, удостоверьтесь, что в часах всё ещё 60 минут, а в минуте 60 секунд 🧐\n'
                'Попробуйте ещё раз'
            )
            print(f"Error converting input start_time: {e}")
            return
    elif re.match(ms_time_pattern, input_start_time):
        try:
            time_object = datetime.strptime(input_start_time, '%M:%S')
            start_time = time_object.minute * 60 + time_object.second
        except Exception as e:
            await message.answer(
                'Пожалуйста, удостоверьтесь, что в минутах всё ещё 60 секунд 🧐\n'
                'Попробуйте ещё раз'
            )
            print(f"Error converting input start_time: {e}")
            return
    else:
        await message.answer(
            'Неверный формат времени для начала эпизода 🙈\n'
            'Я понимаю в формате: ч:мм:сс или мм:сс\n'
            'Попробуйте ещё раз'
        )
        print("Wrong time format")
        return
    data = await state.get_data()
    video = pytube.YouTube(data.get('youtube_url'))
    if start_time > video.length:
        await message.answer(
            'Время начала эпизода больше, чем длина всего видео 😲\n'
            'Вы что-то перепутали 🤔\n'
            'Попробуйте ещё раз'
        )
        return
    await state.update_data(start_time=start_time)

    await state.set_state(video_transcription_FSM.waiting_for_end_time)
    await message.answer(
        'Отправьте время окончания эпизода в формате: ч:мм:сс или мм:сс"\n'
        'Или нажмите "Пропустить", чтобы провести транскрипцию до конца видео',
        reply_markup=keyboards.skip_time_inline_keyboard(),
    )


@router.callback_query(video_transcription_FSM.waiting_for_end_time, F.data == 'skip_time_input')
async def end_time_skipped(callback: types.CallbackQuery, state: FSMContext):
    print("end_time: skipped")
    await callback.answer('Время окончания эпизода пропущено')
    data = await state.get_data()
    youtube_url = data.get('youtube_url')
    start_time = data.get('start_time')
    end_time = None

    await state.clear()
    await transcribe_core.transcribe_video_and_send_to_user(callback.message, youtube_url, start_time, end_time)


@router.message(video_transcription_FSM.waiting_for_end_time)
async def end_time_entered(message: types.Message, state: FSMContext):
    input_end_time = message.text
    print("end_time: " + input_end_time)
    if re.match(hms_time_pattern, input_end_time):
        try:
            time_object = datetime.strptime(input_end_time, '%H:%M:%S')
            end_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
        except Exception as e:
            await message.answer(
                'Пожалуйста, удостоверьтесь, что в часах всё ещё 60 минут, а в минуте 60 секунд 🧐\n'
                'Попробуйте ещё раз'
            )
            print(f"Error converting input end_time: {e}")
            return
    elif re.match(ms_time_pattern, input_end_time):
        try:
            time_object = datetime.strptime(input_end_time, '%M:%S')
            end_time = time_object.minute * 60 + time_object.second
        except Exception as e:
            await message.answer(
                'Пожалуйста, удостоверьтесь, что в минутах всё ещё 60 секунд 🧐\n'
                'Попробуйте ещё раз'
            )
            print(f"Error converting input end_time: {e}")
            return
    else:
        await message.answer(
            'Неверный формат времени для окончания эпизода 🙈\n'
            'Я понимаю в формате: ч:мм:сс или мм:сс\n'
            'Попробуйте ещё раз'
        )
        print("Wrong time format")
        return
    data = await state.get_data()
    youtube_url = data.get('youtube_url')
    start_time = data.get('start_time')
    video = pytube.YouTube(youtube_url)
    if end_time > video.length:
        await message.answer(
            'Время окончания эпизода больше, чем длина всего видео 😲\n'
            'Вы что-то перепутали 🤔\n'
            'Попробуйте ещё раз'
        )
        return
    if start_time is not None:
        if start_time > end_time:
            await message.answer(
                'Хмм, кажется Вы что-то перепутали 🤔\n'
                'У Вас время начала эпизода опережает время его окончания 🧐'
            )
            return

    await state.clear()
    await transcribe_core.transcribe_video_and_send_to_user(message, youtube_url, start_time, end_time)