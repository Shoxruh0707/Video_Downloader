# Integration Guide: User Tracking for Telegram Bot

## Files Created
- `user_tracker.py` - User tracking and bot description update module

## Step 1: Update imports in main.py

Add this import at the top of your `main.py` (after existing imports):

```python
from user_tracker import UserTracker
```

## Step 2: Initialize the tracker

Add this after your existing bot/dispatcher initialization (around line 32, after `dp = Dispatcher()`):

```python
# Initialize user tracker
user_tracker = UserTracker()
```

## Step 3: Update the /start command handler

Replace your existing `@dp.message(CommandStart())` handler with:

```python
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle /start command - track user and update bot description"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    # Track the user
    is_new_user = user_tracker.add_user(user_id, first_name, username)
    
    # Update bot description if it's a new user
    if is_new_user:
        await user_tracker.update_bot_description(bot)
    
    # Your existing welcome message
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
```

## Step 4: Add admin stats command (optional)

Add this new command handler to view user statistics:

```python
@dp.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Show user statistics (admin only)"""
    # Add your admin user ID check here if needed
    stats = user_tracker.get_user_stats()
    
    await message.answer(
        f"📊 Bot Statistics:\n\n"
        f"👥 Total Users: {stats['total_users']}\n"
        f"📅 Users Today: {stats['users_today']}\n"
        f"📆 First User: {stats['first_user_date']}"
    )
```

## Features

✅ **Persistent Storage**: Uses SQLite database (bot_users.db)
✅ **Unique User Tracking**: Only counts each user once
✅ **Rate Limited Updates**: Bot description updates max once per hour
✅ **User Statistics**: Track new users, first user date
✅ **CSV Export**: Export user list for analysis
✅ **Production Ready**: Comprehensive error handling and logging

## Database

- File: `bot_users.db` (created automatically)
- Tables:
  - `users`: Stores user_id, first_name, username, first_seen timestamp
  - `metadata`: Stores tracking metadata

## Bot Description Format

The bot description is automatically updated to show:
```
👥 Users: 123
```

This appears under your bot's name in Telegram.

## Rate Limiting

- Description updates: Once per 1 hour (configurable in user_tracker.py, line 11)
- Prevents Telegram API rate limiting
- Only updates when new users join

## Usage Example

```python
# Track a user from any handler
is_new = user_tracker.add_user(user_id, first_name, username)

# Get current count
count = user_tracker.get_user_count()

# Update description manually if needed
await user_tracker.update_bot_description(bot)

# Get stats
stats = user_tracker.get_user_stats()

# Export users
user_tracker.export_users_csv("users.csv")
```

## Troubleshooting

1. **Description not updating**: Check if update interval has passed (default 1 hour)
2. **Database locked**: Close any other connections to bot_users.db
3. **API errors**: Ensure bot token has necessary permissions (usually automatic)
