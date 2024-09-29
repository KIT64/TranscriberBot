from aiogram import types
from pyrogram import Client

import os

from utils import extract_audio_from_video
from tools import subtitle_maker


async def make_subtitles_and_send_to_user(message: types.Message):
    try:
        print("Downloading video from Telegram...")
        video_file_path = await download_video_from_telegram(message, folder="files from telegram")
        print(f"Video from Telegram was successfully downloaded to {video_file_path}")
    except Exception as e:
        await message.answer(
            "К сожалению, произошла ошибка при скачивании видео 🤔\n"
            f"Причина: {e}"
        )
        print(f"Error while attempting to download video: {e}")
        return

    try:
        print("Extracting audio from video...")
        audio_file_path = extract_audio_from_video(video_file_path)
        print(f"Audio was successfully extracted from video to {audio_file_path}")
    except Exception as e:
        await message.answer("К сожалению, произошла ошибка при извлечении аудио из видео 🤔")
        print(f"Error while attempting to extract audio from video: {e}")
        return
    
    try:
        print("Creating subtitles...")
        subtitles = subtitle_maker.make_subtitles(audio_file_path, language="ru", extension="mp3")
        print("Subtitles were successfully created")
    except Exception as e:
        await message.answer(
            "К сожалению, произошла ошибка при создании субтитров 🤔\n"
            f"Причина: {e}"
        )
        print(f"Error while attempting to make subtitles: {e}")
        return
    
    subtitles_file_name = generate_subtitles_file_name(audio_file_path)
    subtitles_file_path = write_subtitles_to_file(subtitles, folder="subtitles", file_name=subtitles_file_name)
    await send_subtitles_to_user(message, subtitles_file_path)


#TODO: file download progress
async def download_video_from_telegram(message: types.Message, folder):
    async with Client(
        "transcriber_bot",
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        bot_token=os.getenv("BOT_TOKEN")
    ) as app:
        os.makedirs(folder, exist_ok=True)
        video_file_name = message.video.file_name
        video_file_path = os.path.abspath(os.path.join(folder, video_file_name))

        if os.path.exists(video_file_path):
            print(f"Video file already exists. Skipping download...")
            return video_file_path

        await app.download_media(message.video, file_name=video_file_path)

    return video_file_path
    

def generate_subtitles_file_name(audio_file_path):
    audio_file_name = os.path.basename(audio_file_path)
    subtitles_file_name = os.path.splitext(audio_file_name)[0] + ".srt"
    return subtitles_file_name


def write_subtitles_to_file(subtitles, folder, file_name):
    os.makedirs(folder, exist_ok=True)
    subtitles_file_path = os.path.join(folder, file_name)
    with open(subtitles_file_path, "w", encoding="utf-8") as subtitles_file:
        subtitles_file.write(subtitles)
    return subtitles_file_path


async def send_subtitles_to_user(message: types.Message, subtitles_file_path):
    with open(subtitles_file_path, "r", encoding="utf-8") as subtitles_file:
        file_path = os.path.realpath(subtitles_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id)
    os.remove(subtitles_file_path)
    print("Subtitles were successfully sent to the user")