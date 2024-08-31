from aiogram import types

import re
from pytubefix import YouTube
import os

from tools import subtitle_fetcher
from utils import sanitize_filename
import keyboards


async def fetch_subtitles_and_send_to_user(message: types.Message, youtube_url: str):
    try:
        video_id = get_youtube_video_id(youtube_url)
    except Exception as e:
        await message.answer(
            'К сожалению, произошла ошибка при извлечении ID видео из ссылки с YouTube 😔\n'
            'Пожалуйста, удостоверьтесь, что вы ввели ссылку на ролик из YouTube'
        )
        print(f'Error getting youtube video id: {e}')
        return
    
    try:
        subtitles = subtitle_fetcher.fetch_subtitles(video_id, languages=['ru'])
    except:
        await message.answer(
            'К сожалению, произошла ошибка при извлечении субтитров с YouTube 😔\n'
            'Вероятно, для вашего ролика нет субтитров на русском языке 🤔'
        )
        print(f'Error fetching subtitles: {e}')
        return
    
    try:
        subtitles_file_name = generate_subtitles_file_name(youtube_url)
        subtitles_file_path = subtitle_fetcher.write_subtitles_to_file(
            subtitles, folder_path='subtitles', file_name=subtitles_file_name
        )
    except Exception as e:
        await message.answer(
            'К сожалению, произошла ошибка при записи субтитров в файл 😔'
        )
        print(f'Error writing subtitles to file: {e}')
        return
    
    await send_subtitles_file_to_user(message, subtitles_file_path)



def get_youtube_video_id(youtube_url) -> str:
    youtube_url_pattern = r'(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/(watch\?v=|live\/|embed\/)?([a-zA-Z0-9_-]{11})(\S*)?'

    if re.match(youtube_url_pattern, youtube_url):
        return re.match(youtube_url_pattern, youtube_url).group(5)
    else:
        raise ValueError('YouTube url is not valid')
    

def generate_subtitles_file_name(youtube_url) -> str:
    try:
        youtube_video = YouTube(youtube_url)
        return sanitize_filename(youtube_video.title) + '.txt'
    except Exception as e:
        print(f'Error retrieving video title: {e}')
        return ''
    

async def send_subtitles_file_to_user(message: types.Message, subtitles_file_path):
    with open(subtitles_file_path, 'r', encoding='utf-8') as subtitles_file:
        file_path = os.path.realpath(subtitles_file.name)
        file_id = types.FSInputFile(file_path)
    await message.answer_document(file_id, reply_markup=keyboards.main_keyboard())
    os.remove(subtitles_file_path)
    print('Subtitles file was successfully sent to the user')