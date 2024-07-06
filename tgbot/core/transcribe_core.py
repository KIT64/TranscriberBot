from aiogram import types

import os

import utils
from tools import transcriber
import keyboards

async def transcribe_video_and_send_to_user(message: types.Message, video_url, start_time, end_time):
    await message.answer(
        'Ссылку получил, сейчас выдам файл транскрипции 😇\n'
        'Подождите, пожалуйста, это может занять некоторое время ⏳'
    )

    try:
        mp4_file_path = utils.download_audio_from_youtube_video(
            video_url, audio_folder_path='audio storage'
        )
        print(f'Audio was successfully downloaded to {mp4_file_path}')
    except Exception as e:
        await message.answer(
            'К сожалению, произошла ошибка при скачивании аудиофайла с YouTube 😔\n'
        )
        print(f'Error downloading audio from youtube video: {e}')
        return

    try:
        mp3_file_path = utils.trim_and_convert_to_mp3(mp4_file_path, start_time, end_time)
        print(f'Audio was successfully trimmed and converted to {mp3_file_path}')
    except Exception as e:
        await message.answer(
            'К сожалению, произошла ошибка при обработке аудиофайла 😔\n'
        )
        print(f'Error trimming and converting: {e}')
        return

    try:
        transcript = transcriber.transcribe(mp3_file_path, language='ru', format='mp3')
        print(f'Transcription was successfully completed')
    except:
        await message.answer('Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒')
        return
    finally:
        os.remove(mp3_file_path)

    transcript_file_name = get_transcript_file_name(mp3_file_path)
    transcript_file_path = write_transcript_to_file(transcript, folder_path='transcripts', file_name=transcript_file_name)
    await send_transcription_to_user(message, transcript_file_path)


def get_transcript_file_name(mp3_file_path):
    mp3_file_name = os.path.basename(mp3_file_path)
    transcript_file_name = os.path.splitext(mp3_file_name)[0] + '.txt'
    transcript_file_name = mp3_file_name.replace('.mp3', '.txt')
    return transcript_file_name


def write_transcript_to_file(transcript, folder_path, file_name) -> str:
    os.makedirs(folder_path, exist_ok=True)
    transcript_file_path = os.path.join(folder_path, file_name)
    with open(transcript_file_path, "w", encoding="utf-8") as transcript_file:
        transcript_file.write(transcript)
    return transcript_file_path


async def send_transcription_to_user(message: types.Message, transcript_file_path):
    with open(transcript_file_path, 'r', encoding='utf-8') as transcript_file:
        file_path = os.path.realpath(transcript_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id, reply_markup=keyboards.main_keyboard())
    os.remove(transcript_file_path)
    print('Transcription was successfully sent to the user')