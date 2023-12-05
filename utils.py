import os
import pytube
from pydub import AudioSegment


def get_mp3_from_youtube_video(video_url, start_time, end_time, audio_folder_path="") -> str:
    video = pytube.YouTube(video_url)
    mp4_audio_file_path = os.path.join(audio_folder_path, sanitize_filename(video.title) + ".mp4")
    mp3_file_path = os.path.join(audio_folder_path, sanitize_filename(video.title) + ".mp3")

    if os.path.exists(mp4_audio_file_path):
        print("MP4 file already exists. Skipping download.")
    else:
        try:
            audio_stream = video.streams.get_audio_only()
            print("Downloading the audio stream...")
            mp4_audio_file_path = audio_stream.download(output_path=audio_folder_path)
            if os.path.exists(mp4_audio_file_path):
                print(f"Audio stream (mp4) downloaded to {mp4_audio_file_path}")
            else:
                print(f"Audio stream (mp4) failed to download")
        except Exception as e:
            os.remove(mp4_audio_file_path)
            print(f"Error while attempting to download audio stream from youtube: {e}")
            raise e

    print("Converting mp4 to mp3...")
    mp3_audio = AudioSegment.from_file(
        mp4_audio_file_path, format="mp4", start_second=start_time, duration=(end_time - start_time)
    )
    mp3_audio.export(mp3_file_path, format="mp3")
    print(f"MP4 audio was successfully converted to mp3")

    return mp3_file_path


def write_transcript_to_file(transcript, folder_path, file_name) -> str:
    os.makedirs(folder_path, exist_ok=True)
    transcript_file_path = os.path.join(folder_path, file_name)
    with open(transcript_file_path, "w", encoding="utf-8") as transcript_file:
        transcript_file.write(transcript)
    return transcript_file_path

def sanitize_filename(filename):
    # Replace invalid characters with underscores
    invalid_chars = {'.', '/'}
    sanitized_filename = ''.join(char if char not in invalid_chars else '_' for char in filename)
    return sanitized_filename