from youtube_transcript_api import YouTubeTranscriptApi

import os


def fetch_subtitles(video_id, languages=['ru']) -> list:
    transcript_api = YouTubeTranscriptApi()
    output = transcript_api.get_transcript(video_id, languages=languages)
    return output


def write_subtitles_to_file(subtitles, folder_path='subtitles', file_name='Встреча.txt') -> str:
    os.makedirs(folder_path, exist_ok=True)
    subtitles_file_path = os.path.join(folder_path, file_name)
    with open(subtitles_file_path, 'w', encoding='utf-8') as subtitles_file:
        for sub in subtitles:
            subtitles_file.write(f"{sub['text']}, {sub['start']}\n")
    return subtitles_file_path



if __name__ == '__main__':
    video_id = 'Lm9y9esLAXg'
    output = fetch_subtitles(video_id)
    subtitles_file_path = write_subtitles_to_file(output, 'subtitles', 'Встреча.txt')