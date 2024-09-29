import os
from openai import OpenAI
from utils import split_audio, get_bitrate

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_FILE_SIZE = 25  # MEGABYTES


def transcribe(audio_file_path: str, language="ru", extension="mp3") -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)

    file_size = os.path.getsize(audio_file_path)
    print(f"The size of the file to be transcribed is {file_size / 1024:.2f} kilobytes")

    if file_size < MAX_FILE_SIZE * 1024 * 1024:
        try:
            with open(audio_file_path, "rb") as audio_file:
                full_transcript = client.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", language=language, response_format="text"
                )
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            raise e
        return full_transcript

    bitrate_kbps = get_bitrate(audio_file_path) / 1024
    print(f"Bitrate: {bitrate_kbps:.3f} kbps")
    max_length = ((MAX_FILE_SIZE * 1024 * 8) / bitrate_kbps) - 1  # -1 second to ensure
    audio_chunks = split_audio(audio_file_path, max_length, extension)

    transcripts = []
    for chunk_index, chunk_path in enumerate(audio_chunks):
        try:
            print(f"Transcribing audio chunk #{chunk_index}")
            with open(chunk_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", language=language, response_format="text"
                )
                transcripts.append(response)
        except Exception as e:
            print(f"Error transcribing audio chunk #{chunk_index}: {e}")
        finally:
            os.remove(chunk_path)

    full_transcript = " ".join(transcript.strip() for transcript in transcripts)
    return full_transcript


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python transcriber.py <path_to_audio_file>")
        sys.exit(1)

    audio_file_path = sys.argv[1]
    transcript = transcribe(audio_file_path)
    print(transcript)
