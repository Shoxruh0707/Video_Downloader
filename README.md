# YouTube Video Downloader Telegram Bot

A Telegram bot that downloads YouTube videos in different qualities and sends them to users.

## Features

✅ Download YouTube videos in multiple qualities (480p, 720p, 1080p)
✅ Download audio only as MP3
✅ User-friendly quality selection menu
✅ Shows "Downloading..." status while processing
✅ Displays video title below sent content
✅ Automatically deletes downloaded files after sending
✅ Handles errors gracefully

## Installation

### 1. Get Your Bot Token

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot
3. Copy the token provided

### 2. Install Dependencies

Make sure your virtual environment is activated, then run:

```bash
pip install -r requirements.txt
```

You also need FFmpeg for MP3 conversion:

**On Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**On macOS:**
```bash
brew install ffmpeg
```

**On Windows:**
Download from: https://ffmpeg.org/download.html

### 3. Configure the Bot

Create an `.env` file from the example and set your bot token:

```bash
cp .env.example .env
# then edit .env and set BOT_TOKEN
```

In `.env`:

```env
BOT_TOKEN=your-telegram-bot-token-here
```

## Running the Bot

1. Activate the virtual environment:
```bash
source venv/bin/activate
```

2. Run the bot:
```bash
python main.py
```

## How It Works

1. User sends `/start` to begin
2. User sends a YouTube link
3. Bot displays quality selection buttons (480p, 720p, 1080p, MP3)
4. User selects desired quality
5. Bot shows "⏳ Downloading..." message
6. Bot downloads the video
7. Bot sends the video/audio with the title
8. Downloaded file is automatically deleted

## Limitations

- Telegram has a maximum file size limit (usually around 50-100 MB for videos and 50 MB for audio)
- Some videos may not be available for download due to YouTube restrictions
- MP3 download requires FFmpeg

## Troubleshooting

**"Bot token not found"** → Make sure you've replaced `YOUR_BOT_TOKEN_HERE` with your actual token

**"FFmpeg not found"** → Install FFmpeg on your system

**"Video too large"** → Some videos exceed Telegram's file size limit. Try a lower quality

**"video not available"** → YouTube may restrict the video. Try another video

## Security Note

Keep your bot token secret! Never share it publicly.
