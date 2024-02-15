from aiogram import types

import os

import utils
import transcriber
import keyboards

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