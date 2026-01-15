import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import yt_dlp
from pathlib import Path
import instagram_downloader
import social_downloader
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

# Create downloads directory
DOWNLOAD_DIR = "downloads"
Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

# Bot token (from environment)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Define states for FSM
class DownloadStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_quality = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle /start command"""
    await message.answer(
        "👋 Welcome to Video Downloader Bot!\n\n"
        "Just send me a video link and I'll download it for you!\n\n"
        "📱 Supported platforms:\n"
        "• YouTube\n"
        "• Instagram\n"
        "• TikTok\n"
        "• Twitter/X\n"
        "• Facebook\n"
        "• Vimeo\n"
        "• Pinterest\n"
        "• Reddit\n\n"
        "For YouTube: Choose quality (480p, 720p, 1080p, MP3)\n"
        "For other platforms: Auto downloads best quality\n\n"
        "Just paste the link!"
    )

@dp.message(F.text.contains("http"))
async def handle_link(message: Message, state: FSMContext) -> None:
    """Handle video link from multiple platforms"""
    url = message.text.strip()
    
    # Detect platform
    platform = None
    platform_name = ""
    platform_emoji = "📱"
    
    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"
        platform_name = "YouTube"
        platform_emoji = "📺"
    elif "instagram.com" in url:
        platform = "instagram"
        platform_name = "Instagram"
        platform_emoji = "📱"
    elif "tiktok.com" in url:
        platform = "tiktok"
        platform_name = "TikTok"
        platform_emoji = "🎵"
    elif "twitter.com" in url or "x.com" in url:
        platform = "twitter"
        platform_name = "Twitter/X"
        platform_emoji = "🐦"
    elif "facebook.com" in url or "fb.watch" in url:
        platform = "facebook"
        platform_name = "Facebook"
        platform_emoji = "👥"
    elif "vimeo.com" in url:
        platform = "vimeo"
        platform_name = "Vimeo"
        platform_emoji = "🎬"
    elif "pinterest.com" in url:
        platform = "pinterest"
        platform_name = "Pinterest"
        platform_emoji = "📌"
    elif "reddit.com" in url or "redd.it" in url:
        platform = "reddit"
        platform_name = "Reddit"
        platform_emoji = "🤖"
    else:
        await message.answer("❌ Please send a valid link from supported platforms!\n\n"
                           "Supported: YouTube, Instagram, TikTok, Twitter/X, Facebook, Vimeo, Pinterest, Reddit")
        return
    
    # For social media platforms (not YouTube), download directly without quality selection
    if platform != "youtube":
        downloading_msg = await message.answer(f"{platform_emoji} Downloading from {platform_name}... Please wait!")
        
        try:
            if platform == "instagram":
                file_path = await instagram_downloader.download_instagram_video(url, message.from_user.id)
                title = await instagram_downloader.get_instagram_title(url)
            else:
                file_path = await social_downloader.download_social_video(url, message.from_user.id, platform)
                title = await social_downloader.get_social_title(url)
            
            await downloading_msg.edit_text("📤 Uploading to Telegram...")
            
            await bot.send_video(
                chat_id=message.chat.id,
                video=types.FSInputFile(file_path),
                caption=f"🎬 <b>{title}</b>\n\n📱 From: {platform_name}",
                parse_mode="HTML"
            )
            
            await downloading_msg.delete()
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            
            await message.answer("✅ Done! Send another link to download more videos.")
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            await downloading_msg.edit_text(f"❌ Error: {str(e)}\n\nTry another video.")
        
        return
    
    # For YouTube, show quality selection
    await state.update_data(video_url=url, platform=platform)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="480p", callback_data="quality_480")],
            [InlineKeyboardButton(text="720p", callback_data="quality_720")],
            [InlineKeyboardButton(text="1080p", callback_data="quality_1080")],
            [InlineKeyboardButton(text="🎵 MP3", callback_data="quality_mp3")],
        ]
    )
    
    await message.answer(
        "🎥 Please select the quality you want to download:",
        reply_markup=keyboard
    )
    await state.set_state(DownloadStates.waiting_for_quality)

@dp.callback_query(F.data.startswith("quality_"))
async def handle_quality_selection(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Handle quality selection"""
    await callback_query.answer()
    
    quality = callback_query.data.replace("quality_", "")
    data = await state.get_data()
    video_url = data.get('video_url')
    platform = data.get('platform', 'youtube')
    
    if not video_url:
        await callback_query.message.edit_text("❌ Error: No video URL found. Please send a link again.")
        return
    
    # Show downloading message
    platform_emoji = "📺" if platform == "youtube" else "📱"
    downloading_msg = await callback_query.message.edit_text(f"{platform_emoji} Downloading... Please wait!")
    
    try:
        # Download video based on platform and quality selection
        if platform == "youtube":
            if quality == "mp3":
                file_path = await download_mp3(video_url, callback_query.from_user.id)
                format_type = "MP3"
            else:
                file_path = await download_video(video_url, quality, callback_query.from_user.id)
                format_type = f"{quality} Video"
            title = await get_video_title(video_url)
        else:  # Instagram
            if quality == "mp3":
                file_path = await instagram_downloader.download_instagram_audio(video_url, callback_query.from_user.id)
                format_type = "MP3"
            else:
                file_path = await instagram_downloader.download_instagram_video(video_url, callback_query.from_user.id)
                format_type = "Video"
            title = await instagram_downloader.get_instagram_title(video_url)
        
        # Update downloading message
        await downloading_msg.edit_text("📤 Uploading to Telegram...")
        
        # Send file to user
        if quality == "mp3":
            await bot.send_audio(
                chat_id=callback_query.message.chat.id,
                audio=types.FSInputFile(file_path),
                caption=f"🎵 <b>{title}</b>",
                parse_mode="HTML"
            )
        else:
            await bot.send_video(
                chat_id=callback_query.message.chat.id,
                video=types.FSInputFile(file_path),
                caption=f"🎬 <b>{title}</b>\n\n📊 Quality: {format_type}",
                parse_mode="HTML"
            )
        
        # Delete downloading message
        await downloading_msg.delete()
        
        # Delete the downloaded file after sending
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted file: {file_path}")
        
        platform_name = "YouTube" if platform == "youtube" else "Instagram"
        await callback_query.message.answer(f"✅ Done! Send another {platform_name}, YouTube, or Instagram link to download more videos.")
        await state.set_state(DownloadStates.waiting_for_url)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await downloading_msg.edit_text(f"❌ Error: {str(e)}\n\nTry another video.")
        await state.set_state(DownloadStates.waiting_for_url)

async def download_video(url: str, quality: str, user_id: int) -> str:
    """Download video with specified quality"""
    
    quality_map = {
        "480": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
        "720": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "1080": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
}
    }
    
    format_str = quality_map.get(quality, "best[ext=mp4]/best")
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(DOWNLOAD_DIR, f'{user_id}_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'no_color': True,
        'noplaylist': True,
        'retries': 10,
        'fragment_retries': 10,
    }

    def _do_download() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await asyncio.to_thread(_do_download)

async def download_mp3(url: str, user_id: int) -> str:
    """Download video as MP3"""
    
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
        'noplaylist': True,
    }

    def _do_download_mp3() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path_local = ydl.prepare_filename(info)
            return os.path.splitext(file_path_local)[0] + '.mp3'

    return await asyncio.to_thread(_do_download_mp3)

async def get_video_title(url: str) -> str:
    """Get video title"""
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'noplaylist': True,
    }

    def _do_get_title() -> str:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown Title')

    return await asyncio.to_thread(_do_get_title)

@dp.message()
async def echo_message(message: Message) -> None:
    """Handle any other message"""
    await message.answer(
        "👋 Just send me a video link and I'll download it!\n\n"
        "📱 Supported platforms:\n"
        "• YouTube\n"
        "• Instagram\n"
        "• TikTok\n"
        "• Twitter/X\n"
        "• Facebook\n"
        "• Vimeo\n"
        "• Pinterest\n"
        "• Reddit"
    )

async def main() -> None:
    """Start the bot"""
    print("🤖 Bot started! Press Ctrl+C to stop.")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Create a .env file with BOT_TOKEN=your_telegram_bot_token")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
