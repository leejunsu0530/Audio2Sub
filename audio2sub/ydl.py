import yt_dlp  # type: ignore
from typing import Any
import os


def format_filename(input_string: str) -> str:
    invalid_to_fullwidth: dict[str, str] = {
        '<': '＜',  # U+FF1C
        '>': '＞',  # U+FF1E
        ':': '：',  # U+FF1A
        '"': '＂',  # U+FF02
        '/': '／',  # U+FF0F
        '\\': '＼',  # U+FF3C
        '|': '｜',  # U+FF5C
        '?': '？',  # U+FF1F
        '*': '＊',  # U+FF0A
    }

    # Replace each invalid character with its fullwidth equivalent
    for char, fullwidth_char in invalid_to_fullwidth.items():
        input_string = input_string.replace(char, fullwidth_char)

    return input_string


def download_audio(url: str, dirname: str, concurrent_fragments: int = min(32, (os.cpu_count() or 1) + 4)) -> None:
    """
    python cli_to_api.py yt-dlp --format "bestaudio/best" --concurrent-fragments 3 --extract-audio --audio-quality 0 --remux-video m4a --output "[%(id)s]%(title)s_audio.%(ext)s" --paths "dirname" "youtube:skip=translated_subs"
    """
    ydl_opts = {
        'concurrent_fragment_downloads': concurrent_fragments,
        'final_ext': 'm4a',
        'format': 'bestaudio/best',
        'outtmpl': {'default': '[%(id)s]%(title)s_audio.%(ext)s'},
        'paths': {'home': dirname},
        'postprocessors': [{'key': 'FFmpegExtractAudio',
                            'nopostoverwrites': False,
                            'preferredcodec': 'best',
                            'preferredquality': '0'},
                           {'key': 'FFmpegVideoRemuxer', 'preferedformat': 'm4a'}]

    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def bring_data(url: str) -> list[dict]:
    """    
    yt-dlp --flat-playlist --quiet --skip-download
    --extractor-args "youtube:lang=ko;skip=translated_subs" --format "bestvideo[height<=720]+bestaudio/best[height<=720]"
    포멧 파일네임은 파일명에 적을 때 사용
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'extractor_args': {'youtube': {'lang': ['ko'], 'skip': ['translated_subs']}},
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        'noprogress': False,
        'quiet': False,
        'skip_download': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        info_dict = ydl.sanitize_info(info_dict)

        if "entries" in info_dict:
            return info_dict["entries"]
        else:
            return [info_dict]
    # 이제 이게 비디오/플리 모두 되는지 확인
