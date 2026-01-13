import os
import yt_dlp
import asyncio
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

async def download_instagram_video(url: str, user_id: int) -> str:
    """Download Instagram video"""
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'no_color': True,
    }

    def _do_download() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await asyncio.to_thread(_do_download)

async def download_instagram_audio(url: str, user_id: int) -> str:
    """Download Instagram video as MP3"""
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'no_color': True,
    }

    def _do_download_mp3() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path_local = ydl.prepare_filename(info)
            return os.path.splitext(file_path_local)[0] + '.mp3'

    return await asyncio.to_thread(_do_download_mp3)

async def get_instagram_title(url: str) -> str:
    """Get Instagram video title/caption"""
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
    }

    def _do_get_title() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            t = info.get('title', 'Instagram Video')
            return t if len(t) <= 100 else t[:97] + "..."

    return await asyncio.to_thread(_do_get_title)
