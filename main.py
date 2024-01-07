import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import pytube
import os
import re
from datetime import datetime

import transcriber
import utils
import keyboards


BOT_TOKEN = os.getenv('BOT_TOKEN')
dp = Dispatcher()

youtube_url_pattern = r'(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|live\/|embed\/)?([a-zA-Z0-9_-]{11})(\S*)?'
hms_time_pattern = r'((\d)+:(\d){2}:(\d){2})'  # H/HH:MM:SS format
ms_time_pattern = r'((\d)+:(\d){2})'  # M/MM:SS format


class video_transcription_FSM(StatesGroup):
    waiting_for_youtube_url = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        'Привет! 👋\n'
        'Я Бот-транскриптор 🤗\n'
        'C помощью меня вы можете перевести видео в текст 📝\n'
        'Чтобы начать, нажми на кнопку "Транскрипция видео"',
        reply_markup=keyboards.main_keyboard()
    )
    

@dp.message(F.text == 'Транскрипция видео')
@dp.message(F.text == 'Начать ввод заново')
async def start_video_transcription_input(message: types.Message, state: FSMContext):
    await state.set_state(video_transcription_FSM.waiting_for_youtube_url)
    await message.answer(
        'Отправьте ссылку на ролик в YouTube',
        reply_markup=keyboards.cancel_transcription_keyboard()
    )


@dp.message(F.text == 'Отменить текущий ввод')
async def cancel_current_transcription_input(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Ввод данных для транскрипции видео был отменен 👌',
        reply_markup=keyboards.main_keyboard()
    )


@dp.message(video_transcription_FSM.waiting_for_youtube_url)
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
    await message.answer('Отправьте время начала эпизода в формате: ч:мм:сс или мм:сс\n'
                         'Или нажмите "Пропустить", чтобы начать транскрипцию с начала видео',
                         reply_markup=keyboards.skip_time_inline_keyboard())
    

@dp.callback_query(video_transcription_FSM.waiting_for_start_time, F.data == 'skip_time_input')
async def start_time_skipped(callback: types.CallbackQuery, state: FSMContext):
    print("start_time: skipped")
    await callback.answer('Время начала эпизода пропущено')
    await state.update_data(start_time=0)

    await state.set_state(video_transcription_FSM.waiting_for_end_time)
    await callback.message.answer('Отправьте время окончания эпизода в формате: ч:мм:сс или мм:сс"\n'
                                  'Или нажмите "Пропустить", чтобы провести транскрипцию до конца видео',
                                  reply_markup=keyboards.skip_time_inline_keyboard())


@dp.message(video_transcription_FSM.waiting_for_start_time)
async def start_time_entered(message: types.Message, state: FSMContext):
    input_start_time = message.text
    print("start_time: " + input_start_time)
    if re.match(hms_time_pattern, input_start_time):
        time_object = datetime.strptime(input_start_time, '%H:%M:%S')
        start_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
    elif re.match(ms_time_pattern, input_start_time):
        time_object = datetime.strptime(input_start_time, '%M:%S')
        start_time = time_object.minute * 60 + time_object.second
    else:
        await message.answer(
            'Неверный формат времени для начала эпизода 🙈\n'
            'Поправьте его, пожалуйста, чтобы я cмог его понять\n'
            'Я понимаю в формате: ч:мм:сс или мм:сс'
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
    await message.answer('Отправьте время окончания эпизода в формате: ч:мм:сс или мм:сс"\n'
                         'Или нажмите "Пропустить", чтобы провести транскрипцию до конца видео',
                         reply_markup=keyboards.skip_time_inline_keyboard())


@dp.callback_query(video_transcription_FSM.waiting_for_end_time, F.data == 'skip_time_input')
async def end_time_skipped(callback: types.CallbackQuery, state: FSMContext):
    print("end_time: skipped")
    await callback.answer('Время окончания эпизода пропущено')
    data = await state.get_data()
    youtube_url = data.get('youtube_url')
    start_time = data.get('start_time')
    video = pytube.YouTube(youtube_url)
    end_time = video.length

    await state.clear()
    await transcribe_video_and_send_to_user(callback.message, youtube_url, start_time, end_time)


@dp.message(video_transcription_FSM.waiting_for_end_time)
async def end_time_entered(message: types.Message, state: FSMContext):
    input_end_time = message.text
    print("end_time: " + input_end_time)
    if re.match(hms_time_pattern, input_end_time):
        time_object = datetime.strptime(input_end_time, '%H:%M:%S')
        end_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
    elif re.match(ms_time_pattern, input_end_time):
        time_object = datetime.strptime(input_end_time, '%M:%S')
        end_time = time_object.minute * 60 + time_object.second
    else:
        await message.answer(
            'Неверный формат времени для окончания эпизода 🙈\n'
            'Поправьте его, пожалуйста, чтобы я cмог его понять\n'
            'Я понимаю в формате: ч:мм:сс или мм:сс'
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
    if start_time > end_time:
        await message.answer(
            'Хмм, кажется Вы что-то перепутали 🤔\n'
            'У Вас время начала эпизода опережает время его окончания 🧐'
        )
        return
    
    await state.clear()
    await transcribe_video_and_send_to_user(message, youtube_url, start_time, end_time)


async def transcribe_video_and_send_to_user(message: types.Message, video_url, start_time, end_time):
    await message.answer(
            'Ссылку получил, сейчас выдам файл транскрипции 😇\n'
            'Подождите, пожалуйста, это может занять некоторое время ⏳'
    )

    try:
        mp3_file_path = utils.get_mp3_from_youtube_video(
            video_url, start_time, end_time, audio_folder_path='audio storage'
        )
    except Exception as e:
        await message.answer(
            'К сожалению, произошла ошибка при получении аудиофайла из видео 😔\n'
            'Пожалуйста, обратитесь к разработчику, чтобы ошибка была исправлена 🔧'
        )
        print(f'Error downloading and converting audio from youtube video: {e}')
        return
    
    try:
        transcript = transcriber.transcribe(mp3_file_path, language='ru', format='mp3')
    except:
        await message.answer('Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒')
        return
    finally:
        os.remove(mp3_file_path)

    transcript_file_name = get_transcript_file_name(mp3_file_path)
    transcript_file_path = utils.write_transcript_to_file(
        transcript, folder_path='transcripts', file_name=transcript_file_name
    )
    await send_transcription_to_user(message, transcript_file_path)


def get_transcript_file_name(mp3_file_path):
    mp3_file_name = os.path.basename(mp3_file_path)
    transcript_file_name = os.path.splitext(mp3_file_name)[0] + '.txt'
    transcript_file_name = mp3_file_name.replace('.mp3', '.txt')
    return transcript_file_name


async def send_transcription_to_user(message: types.Message, transcript_file_path):
    with open(transcript_file_path, 'r', encoding='utf-8') as transcript_file:
        file_path = os.path.realpath(transcript_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id, reply_markup=keyboards.main_keyboard())
    os.remove(transcript_file_path)
    print('Transcription was successfully sent to the user')


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot has been launched')
    asyncio.run(main())