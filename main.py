import asyncio
from aiogram import Bot, Dispatcher, types, F

import os
import pytube
from datetime import datetime

import transcriber
import utils


BOT_TOKEN = os.getenv("BOT_TOKEN")
dp = Dispatcher()

youtube_url_pattern = r"(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|embed\/)?([a-zA-Z0-9_-]{11})(\S*)?"
time_pattern_optional = r"((\d)+:(\d){2}:(\d){2})?"  # H/HH:MM:SS format

@dp.message(
    F.text.regexp(
        r"^"
        + youtube_url_pattern
        + r"(\s)?"
        + time_pattern_optional
        + r"(\s)?"
        + time_pattern_optional
        + r"$"
    )
)
async def transcribe_video(message: types.Message):
    await message.answer(
            "Ссылку получил, сейчас выдам файл транскрипции 😇\n"
            "Подожди, пожалуйста, это может занять некоторое время ⏳"
    )
    args = message.text.split(" ")
    video_url = args[0]
    print(f"video_url: {video_url}")
    youtube_video = pytube.YouTube(video_url)

    try:
        input_start_time = args[1]
        time_object = datetime.strptime(input_start_time, "%H:%M:%S")
        start_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
        if start_time > youtube_video.length:
            await message.answer("Время старта больше, чем длина всего видео 😲😲😲")
            print("Failed to transcript the video: start_time > video.length")
            return
    except ValueError:
        await message.answer(
                "Формат времени для старта неверный\n"
                "Поправьте его, пожалуйста, чтобы я cмог его понять ❤️\n"
                "Я понимаю в формате: ЧЧ:ММ:СС или Ч:ММ:СС"
            )
        print("Failed to transcript the video: wrong time format for start_time ")
        return
    except IndexError:
        start_time = 0
    print(f"start_time: {start_time}")

    try:
        input_end_time = args[2]
        time_object = datetime.strptime(input_end_time, "%H:%M:%S")
        end_time = time_object.hour * 3600 + time_object.minute * 60 + time_object.second
        if end_time > youtube_video.length:
            await message.answer("Время финиша больше, чем длина всего видео 🤨")
            print("Failed to transcript the video: end_time > video.length")
            return
        if start_time > end_time:
            await message.answer(
                "Хмм, кажется Вы что-то перепутали 🤔\n"
                "У Вас время старта опережает время финиша 🧐"
            )
            print("Failed to transcript the video: start_time > end_time")
            return
    except ValueError:
        await message.answer(
                "Формат времени для финиша неверный\n"
                "Поправьте его, пожалуйста, чтобы я cмог его понять ❤️\n"
                "Я понимаю в формате: ЧЧ:ММ:СС или Ч:ММ:СС"
            )
        print("Failed to transcript the video: wrong format for end_time")
        return
    except IndexError:
        end_time = youtube_video.length
    print(f"end_time: {end_time}")

    try:
        mp3_file_path = utils.get_mp3_from_youtube_video(
            video_url, audio_folder_path="audio to transcribe"
        )
    except Exception as e:
        await message.answer(
            "К сожалению, произошла ошибка при получении аудиофайла из видео 😔\n"
            "Пожалуйста, обратитесь к разработчику, чтобы ошибка была исправлена 🔧"
        )
        print(f"Error downloading and converting audio from youtube video: {e}")
        return

    if start_time == 0 and end_time == youtube_video.length:
        try:
            transcript = transcriber.transcribe(mp3_file_path, language="ru", format="mp3")
        except:
            await message.answer("Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒")
            return
    else:
        print("Trimming the audio...")
        trimmed_mp3_file_path = utils.trim_audio(mp3_file_path, start_time, end_time, format="mp3")
        print(f"File was successfully trimmed to: {trimmed_mp3_file_path}")
        try:
            transcript = transcriber.transcribe(trimmed_mp3_file_path, language="ru", format="mp3")
        except:
            await message.answer("Произошла ошибка, похоже, что сервис транскрипции OpenAI временно не доступен 😒")
            return
        finally:
            os.remove(trimmed_mp3_file_path)

    mp3_file_name = os.path.basename(mp3_file_path)
    transcript_file_name = os.path.splitext(mp3_file_name)[0] + ".txt"
    transcript_file_name = mp3_file_name.replace(".mp3", ".txt")
    transcript_file_path = utils.write_transcript_to_file(
        transcript, folder_path="transcripts", file_name=transcript_file_name
    )

    with open(transcript_file_path, "r", encoding="utf-8") as transcript_file:
        file_path = os.path.realpath(transcript_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id)


async def main():
    bot = Bot(BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot has been launched")
    asyncio.run(main())