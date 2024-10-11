from aiogram import types
from aiogram.types import FSInputFile
from pyrogram import Client
import os
import uuid

import utils
from tools import transcriber
import keyboards

MAX_MESSAGE_LENGTH = 4096

async def transcribe_video_and_send_to_user(message: types.Message, video_url, start_time, end_time):
    await message.answer(
        'Ссылку получил, сейчас выдам файл транскрипции 😇\n'
        'Подождите, пожалуйста, это может занять некоторое время ⏳'
    )

    try:
        mp4_file_path = utils.download_audio_from_youtube_video(
            video_url, audio_folder_path='files from youtube'
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
        transcript = transcriber.transcribe(mp3_file_path, language='ru', extension='mp3')
        print(f'Transcription was successfully completed')
    except:
        await message.answer(
            'Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒\n'
            f'Причина: {e}'
        )
        return
    finally:
        os.remove(mp3_file_path)

    transcript_file_name = generate_transcript_file_name(mp3_file_path)
    transcript_file_path = write_transcript_to_file(transcript, folder_path='transcripts', file_name=transcript_file_name)
    await send_transcription_to_user(message, transcript_file_path)


async def transcribe_audio_and_send_to_user(message: types.Message, is_channel=False):
    try:
        print("Downloading audio from Telegram...")
        audio_file_path = await download_audio_from_telegram(message, folder="files from telegram")
        print(f"Audio from Telegram was successfully downloaded to {audio_file_path}")
    except Exception as e:
        error_message = f"К сожалению, произошла ошибка при скачивании аудио 😔\nПричина: {e}"
        await send_message(message, error_message, is_channel)
        print(f"Error while attempting to download audio: {e}")
        return

    try:
        print("Transcribing audio...")
        file_extension = os.path.splitext(audio_file_path)[1].lower()[1:]
        transcript = transcriber.transcribe(audio_file_path, language="ru", extension=file_extension)
        print("Audio was successfully transcribed")
    except Exception as e:
        error_message = f"Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒\nПричина: {e}"
        await send_message(message, error_message, is_channel)
        return
    # finally:
    #     os.remove(audio_file_path)

    if len(transcript) <= MAX_MESSAGE_LENGTH:
        await send_message(message, f"💬 {transcript}", is_channel)
    else:
        transcript_file_name = generate_transcript_file_name(audio_file_path)
        transcript_file_path = write_transcript_to_file(transcript, folder_path='transcripts', file_name=transcript_file_name)
        await send_transcription_file(message, transcript_file_path, is_channel)


async def send_message(message: types.Message, text: str, is_channel: bool):
    if is_channel:
        await message.answer(text, reply_to_message_id=message.message_id)
    else:
        await message.reply(text)


async def send_transcription_file(message: types.Message, transcript_file_path: str, is_channel: bool):
    file = FSInputFile(transcript_file_path)
    if is_channel:
        await message.answer_document(file, reply_to_message_id=message.message_id)
    else:
        await message.reply_document(file)
    os.remove(transcript_file_path)
    print('Transcription was successfully sent to the user')


def generate_transcript_file_name(mp3_file_path):
    mp3_file_name = os.path.basename(mp3_file_path)
    transcript_file_name = os.path.splitext(mp3_file_name)[0] + '.txt'
    return transcript_file_name


def write_transcript_to_file(transcript, folder_path, file_name):
    os.makedirs(folder_path, exist_ok=True)
    transcript_file_path = os.path.join(folder_path, file_name)
    with open(transcript_file_path, "w", encoding="utf-8-sig") as transcript_file:
        transcript_file.write(transcript)
    return transcript_file_path

async def send_transcription_to_user(message: types.Message, transcript_file_path):
    with open(transcript_file_path, 'r', encoding='utf-8') as transcript_file:
        file_path = os.path.realpath(transcript_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id, reply_markup=keyboards.main_keyboard())
    os.remove(transcript_file_path)
    print('Transcription was successfully sent to the user')

#TODO: file download progress
async def download_audio_from_telegram(message: types.Message, folder):
    async with Client(
        f"bot_session_{uuid.uuid4()}",
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        bot_token=os.getenv("BOT_TOKEN")
    ) as app:
        os.makedirs(folder, exist_ok=True)

        if message.voice:
            print(f"Voice message detected")
            file = message.voice
            mime_type = file.mime_type
            print(f"Mime type: {mime_type}")
            if mime_type == "audio/ogg":
                file_extension = ".ogg"
            elif mime_type == "audio/mpeg":
                file_extension = ".m4a"
            else:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
        elif message.audio:
            print(f"Audio message detected")
            mime_type = message.audio.mime_type
            print(f"Mime type: {mime_type}")
            file = message.audio
            file_extension = ".mp3"
        else:
            raise ValueError("This function only works with voice messages or audio files")

        audio_file_name = f"audio_{message.message_id}{file_extension}"
        audio_file_path = os.path.abspath(os.path.join(folder, audio_file_name))

        if os.path.exists(audio_file_path):
            print(f"Audio file already exists. Skipping download...")
            return audio_file_path

        await app.download_media(file, file_name=audio_file_path)

    print(f"Audio file downloaded: {audio_file_path}")
    return audio_file_path