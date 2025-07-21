from sys import version_info

# 파이썬 버전 확인
if not version_info >= (3, 11):
    raise ImportError("Only Python versions 3.11 and above are supported")

# yt-dlp 확인


__version__ = "1.0.0"
