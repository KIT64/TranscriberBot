from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def make_subtitles(audio_file_path, language="ru"):
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        subtitles = client.audio.transcriptions.create(
            file=audio_file_path, model="whisper-1", language=language, response_format="srt"
        )
    except Exception as e:
        print("Error transcribing audio into .srt")
        raise e

    return subtitles