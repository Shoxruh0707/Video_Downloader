import os
import yt_dlp
import asyncio
import logging

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"

async def download_social_video(url: str, user_id: int, platform: str = "social") -> str:
    """Download video from social media platforms (TikTok, Twitter, Facebook, Vimeo, Pinterest, Reddit)"""
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'no_color': True,
    }
    
    # Platform-specific options
    if platform == "tiktok":
        # TikTok sometimes needs special handling
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def _do_download() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await asyncio.to_thread(_do_download)

async def get_social_title(url: str) -> str:
    """Get video title from social media platforms"""
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
    }

    def _do_get_title() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            t = info.get('title', 'Video')
            return t if len(t) <= 100 else t[:97] + "..."

    return await asyncio.to_thread(_do_get_title)
