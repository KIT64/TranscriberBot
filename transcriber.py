import os
from pydub import AudioSegment
from pydub.utils import mediainfo
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_FILE_SIZE = 25  # MEGABYTES


def split_audio(file_path, max_length, format="mp3"):
    audio = AudioSegment.from_file(file_path, format=format)
    length_audio = len(audio)
    parts = int(length_audio / max_length) + 1
    audio_chunks = [audio[i * max_length : (i + 1) * max_length] for i in range(parts)]
    return audio_chunks


def get_bitrate(file_path):
    bitrate = int(mediainfo(file_path)["bit_rate"])
    return bitrate


def transcribe(audio_file_path: str, language="ru", format="mp3") -> str:
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
    print(f"Bitrate: {bitrate_kbps:.9f} kbps")
    max_length_seconds = ((MAX_FILE_SIZE * 1024 * 8) / bitrate_kbps) - 1  # -1 second to ensure
    max_length = int(max_length_seconds * 1000)  # measured in milliseconds
    audio_chunks = split_audio(audio_file_path, max_length, format)
    print(f"Number of chunks: {len(audio_chunks)}")

    transcripts = []
    for chunk_index, chunk in enumerate(audio_chunks):
        temp_audio_file_path = f"temp_chunk_{chunk_index}.{format}"
        chunk.export(temp_audio_file_path, format=format)
        try:
            with open(temp_audio_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", language=language, response_format="text"
                )
                transcripts.append(response)
        except Exception as e:
            print(f"Error transcribing audio chunk #{chunk_index}: {e}")
        finally:
            os.remove(temp_audio_file_path)

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
