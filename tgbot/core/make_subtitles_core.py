from aiogram import types

import os

from utils import extract_audio_from_video
from tools import subtitle_maker


async def make_subtitles_and_send_to_user(message: types.Message):
    try:
        video_file_path = await message.video.download()
        print(f"Video from Telegram was successfully downloaded to {video_file_path}")
    except Exception as e:
        await message.answer("К сожалению, произошла ошибка при скачивании видео 🤔")
        print(f"Error while attempting to download video: {e}")
        return

    try:
        audio_file_path = extract_audio_from_video(video_file_path)
        print(f"Audio was successfully extracted from video to {audio_file_path}")
    except Exception as e:
        await message.answer("К сожалению, произошла ошибка при извлечении аудио из видео 🤔")
        print(f"Error while attempting to extract audio from video: {e}")
        return
    
    try:
        subtitles = subtitle_maker.make_subtitles(audio_file_path, language="ru")
        print("Subtitles were successfully created")
    except Exception as e:
        await message.answer(
            "К сожалению, произошла ошибка при создании субтитров 🤔\n"
            f"Причина: {e}"
        )
        print(f"Error while attempting to make subtitles: {e}")
        return
    finally:
        os.remove(audio_file_path)
    
    subtitles_file_name = generate_subtitles_file_name(audio_file_path)
    subtitles_file_path = write_subtitles_to_file(subtitles, folder="subtitles", file_name=subtitles_file_name)
    await send_subtitles_to_user(message, subtitles_file_path)


def generate_subtitles_file_name(audio_file_path):
    audio_file_name = os.path.basename(audio_file_path)
    subtitles_file_name = os.path.splitext(audio_file_name)[0] + ".txt"
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