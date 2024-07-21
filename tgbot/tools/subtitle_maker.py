import os
from pydub import AudioSegment
from pydub.utils import mediainfo
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_FILE_SIZE = 15  # MEGABYTES


def make_subtitles(audio_file_path, language="ru", format="mp3"):
    client = OpenAI(api_key=OPENAI_API_KEY)

    file_size = os.path.getsize(audio_file_path)
    print(f"Audio file size required for subtitles is {file_size / 1024:.2f} kilobytes")

    if file_size < MAX_FILE_SIZE * 1024 * 1024:
        try:
            with open(audio_file_path, "rb") as audio_file:
                subtitles = client.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", language=language, response_format="srt"
                )
        except Exception as e:
            print("Error transcribing audio into .srt")
            raise e
        return subtitles
    
    bitrate_kbps = get_bitrate(audio_file_path) / 1024
    print(f"Bitrate: {bitrate_kbps:.9f} kbps")
    max_length_seconds = ((MAX_FILE_SIZE * 1024 * 8) / bitrate_kbps) - 1  # -1 second to ensure
    max_length = int(max_length_seconds * 1000)  # measured in milliseconds
    audio_chunks = split_audio(audio_file_path, max_length, format) # potential error here because pydub.AudioSegment requires a lot of RAM
    print(f"Number of chunks: {len(audio_chunks)}")

    subtitles_list = []
    cumulative_duration = 0
    for chunk_index, chunk in enumerate(audio_chunks):
        temp_audio_file_path = f"temp_chunk_{chunk_index}.{format}"
        chunk.export(temp_audio_file_path, format=format)
        try:
            with open(temp_audio_file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    file=audio_file, model="whisper-1", language=language, response_format="srt"
                )
                cumulative_duration = max_length_seconds * chunk_index
                response = adjust_chunk_timestamp(response, cumulative_duration)
                print(f"Audio chunk #{chunk_index} transcribed successfully")
        except Exception as e:
            print(f"Error transcribing audio chunk #{chunk_index}: {e}")
            raise Exception(f"Error transcribing audio chunk #{chunk_index}: {e}")
        finally:
            os.remove(temp_audio_file_path)

        subtitles_list.append(response)

    full_subtitles = merge_srt_responses(subtitles_list)

    return full_subtitles


def adjust_chunk_timestamp(subtitles, cumulative_duration):
    lines = subtitles.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            if ' --> ' in line:
                start, end = line.split(' --> ')
                start_time = adjust_time(start, cumulative_duration)
                end_time = adjust_time(end, cumulative_duration)
                lines[i] = f"{start_time} --> {end_time}"
    return '\n'.join(lines)


def adjust_time(time, duration):
    hms_time, milliseconds = time.split(',')
    hours, minutes, seconds = hms_time.split(':')
    
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(duration)
    
    new_hours, remaining_seconds = divmod(total_seconds, 3600)
    new_minutes, new_seconds = divmod(remaining_seconds, 60)
    
    return f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}.{milliseconds}"


def split_audio(file_path, max_length, format="mp3"):
    audio = AudioSegment.from_file(file_path, format=format)
    length_audio = len(audio)
    parts = int(length_audio / max_length) + 1
    audio_chunks = [audio[i * max_length : (i + 1) * max_length] for i in range(parts)]
    return audio_chunks


def get_bitrate(file_path):
    bitrate = int(mediainfo(file_path)["bit_rate"])
    return bitrate


def merge_srt_responses(srt_list):
    lines = []
    count = 1
    for srt in srt_list:
        fragments = srt.split("\n\n")
        for fragment in fragments[:-1]:
            for line in fragment.splitlines():
                if line.strip().isdigit():
                    lines.append(f"{count}\n")
                    count += 1
                else:
                    lines.append(line + "\n")
            lines.append("\n")
        
    return "".join(lines)



def srt_to_str(srt_file_path):
    with open(srt_file_path, 'r', encoding='utf-8') as srt_file:
        srt_text = srt_file.read()
    return srt_text


def str_to_srt(srt_text, file_name='full.srt'):
    with open('full.srt', 'w', encoding='utf-8') as srt_file:
        srt_file.write(srt_text)
    return 'full.srt'


def main():
    srt_1 = srt_to_str("1.srt")
    # srt_2 = srt_to_str("2.srt")
    # srt_list = [srt_1, srt_2]
    # full_srt = merge_srt_responses(srt_list)
    # str_to_srt(full_srt)
    response = adjust_chunk_timestamp(srt_1, 100)
    print(response)


if __name__ == "__main__":
    main()