import os
import pytubefix

import subprocess


def download_audio_from_youtube_video(video_url, audio_folder_path="") -> str:
    video = pytubefix.YouTube(video_url)
    mp4_audio_file_path = os.path.join(audio_folder_path, sanitize_filename(video.title) + ".mp4")

    if os.path.exists(mp4_audio_file_path):
        print(f"Audio stream (mp4) already exists. Skipping download...")
        return mp4_audio_file_path
    
    try:
        audio_stream = video.streams.filter(only_audio=True, file_extension="mp4").order_by("abr").desc().first()
        print("Downloading the audio stream...")
        mp4_audio_file_path = audio_stream.download(output_path=audio_folder_path)
        if os.path.exists(mp4_audio_file_path):
            print(f"Audio stream (mp4) downloaded to {mp4_audio_file_path}")
        else:
            print(f"Audio stream (mp4) failed to download")
    except Exception as e:
        print(f"Error while attempting to download audio stream from youtube: {e}")
        raise e

    return mp4_audio_file_path


def trim_and_convert_to_mp3(file_path, start_time=None, end_time=None):
    extension = os.path.splitext(file_path)[1]
    if extension == ".mp3":
        print(f"Conversion skipped. {file_path} is already in mp3 format")
        return file_path

    mp3_file_path = os.path.splitext(file_path)[0] + ".mp3"

    ffmpeg_command = [
        'ffmpeg',
    ]
    if start_time is not None:
        ffmpeg_command.extend(['-ss', str(start_time)])
    if end_time is not None:
        ffmpeg_command.extend(['-to', str(end_time)])
    ffmpeg_command.extend([
        '-i', file_path,
        '-vn',
        '-acodec', 'libmp3lame',
        '-y',
        mp3_file_path
    ])

    try:
        subprocess.run(ffmpeg_command, check=True)
        return mp3_file_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error while trimming and converting {file_path} to mp3: {e}")


def extract_audio_from_video(video_path):
    audio_file_path = os.path.splitext(video_path)[0] + ".mp3"

    if os.path.exists(audio_file_path):
        print(f"Audio file already exists. Skipping extraction...")
        return audio_file_path

    ffmpeg_command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-acodec', 'libmp3lame',
        '-y',
        audio_file_path
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        return os.path.splitext(video_path)[0] + ".mp3"
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error while extracting audio from {video_path} and converting to mp3: {e}")


def sanitize_filename(filename):
    invalid_chars = {'.', '/', '\\', '?', '|'}
    sanitized_filename = ''.join(char if char not in invalid_chars else '' for char in filename)
    return sanitized_filename