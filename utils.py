import os
import pytube
from pydub import AudioSegment


def get_mp3_from_youtube_video(video_url, audio_folder_path="") -> str:
    video = pytube.YouTube(video_url)
    mp3_file_name = video.title + ".mp3"
    mp3_file_path = os.path.join(audio_folder_path, mp3_file_name)

    if os.path.exists(mp3_file_path):
        print("MP3 file already exists. Skipping download and conversion.")
        return mp3_file_path

    audio_stream = video.streams.get_audio_only()
    print("Downloading the audio stream...")
    mp4_audio_file_path = audio_stream.download(output_path=audio_folder_path)
    print(f"Audio stream (mp4) downloaded to {mp4_audio_file_path}")

    file_size = os.path.getsize(mp4_audio_file_path)
    print(f"Size of the mp4 file is {file_size / 1024:.2f} kilobytes")

    print("Converting mp4 to mp3...")
    audio = AudioSegment.from_file(mp4_audio_file_path, format="mp4")
    audio.export(mp3_file_path, format="mp3")
    print(f"mp4 audio converted to mp3 to {mp3_file_path}")

    os.remove(mp4_audio_file_path)
    print(f"Deleted the mp4 audio file: {mp4_audio_file_path}")

    return mp3_file_path


def trim_audio(audio_file_path, start_time, end_time, format="mp3",) -> str:
    audio = AudioSegment.from_file(audio_file_path, format=format)
    trimmed_audio = audio[start_time * 1000 : end_time * 1000]

    audio_file_folder = os.path.dirname(audio_file_path)
    audio_file_name = os.path.basename(audio_file_path)
    trimmed_audio_file_name = os.path.splitext(audio_file_name)[0] + "_trimmed" + "." + format
    trimmed_audio_file_path = os.path.join(audio_file_folder, trimmed_audio_file_name)

    trimmed_audio.export(trimmed_audio_file_path, format=format)
    return trimmed_audio_file_path

def write_transcript_to_file(transcript, folder_path, file_name) -> str:
    os.makedirs(folder_path, exist_ok=True)
    transcript_file_path = os.path.join(folder_path, file_name)
    with open(transcript_file_path, "w", encoding="utf-8") as transcript_file:
        transcript_file.write(transcript)
    print(f"Transcript saved to: {transcript_file_path}")
    return transcript_file_path