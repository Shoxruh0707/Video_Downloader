"""
User tracking and bot description updater for Telegram bot.
Tracks unique users and automatically updates bot description with user count.
"""

import sqlite3
import os
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from aiogram import Bot

logger = logging.getLogger(__name__)

# Database file location
DB_FILE = "bot_users.db"
DESCRIPTION_UPDATE_INTERVAL = 3600  # Update every 1 hour (prevent rate limiting)


class UserTracker:
    """Manages user tracking and bot description updates."""

    def __init__(self, db_file: str = DB_FILE):
        """Initialize the user tracker with SQLite database."""
        self.db_file = db_file
        self.last_update_time: Optional[datetime] = None
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with users table."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Create users table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Create metadata table for tracking last update
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_file}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def add_user(self, user_id: int, first_name: Optional[str] = None, 
                 username: Optional[str] = None) -> bool:
        """
        Add a user to the database (only if new).
        
        Args:
            user_id: Telegram user ID
            first_name: User's first name
            username: User's username
            
        Returns:
            True if user was newly added, False if already existed
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                logger.debug(f"User {user_id} already tracked")
                conn.close()
                return False

            # Add new user
            cursor.execute(
                """
                INSERT INTO users (user_id, first_name, username)
                VALUES (?, ?, ?)
                """,
                (user_id, first_name, username),
            )
            conn.commit()
            conn.close()
            logger.info(f"New user added: {user_id} (@{username})")
            return True

        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            return False

    def get_user_count(self) -> int:
        """
        Get total number of unique users.
        
        Returns:
            Count of unique users in database
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get user count: {e}")
            return 0

    def should_update_description(self) -> bool:
        """
        Check if enough time has passed to update description again.
        
        Returns:
            True if update is allowed (respects rate limiting)
        """
        now = datetime.now()

        if self.last_update_time is None:
            return True

        time_since_update = now - self.last_update_time
        if time_since_update >= timedelta(seconds=DESCRIPTION_UPDATE_INTERVAL):
            return True

        return False

    async def update_bot_description(self, bot: Bot) -> bool:
        """
        Update bot's description with current user count.
        Uses setMyDescription Telegram Bot API method.
        
        Args:
            bot: aiogram Bot instance
            
        Returns:
            True if update was successful, False otherwise
        """
        # Rate limiting check
        if not self.should_update_description():
            logger.debug("Description update skipped (rate limit)")
            return False

        try:
            user_count = self.get_user_count()
            description = f"👥 Users: {user_count}"

            # Call Telegram Bot API to set description
            await bot.set_my_description(description=description)

            self.last_update_time = datetime.now()
            logger.info(f"Bot description updated: '{description}'")
            return True

        except Exception as e:
            logger.error(f"Failed to update bot description: {e}")
            return False

    def get_user_stats(self) -> dict:
        """
        Get detailed user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(first_seen) FROM users")
            first_user_date = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE first_seen > datetime('now', '-1 day')")
            users_today = cursor.fetchone()[0]

            conn.close()

            return {
                "total_users": total_users,
                "users_today": users_today,
                "first_user_date": first_user_date,
            }

        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {
                "total_users": 0,
                "users_today": 0,
                "first_user_date": None,
            }

    def export_users_csv(self, filepath: str = "users_export.csv") -> bool:
        """
        Export user list to CSV file.
        
        Args:
            filepath: Path to save CSV file
            
        Returns:
            True if export was successful
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT user_id, first_name, username, first_seen FROM users ORDER BY first_seen DESC"
            )
            users = cursor.fetchall()
            conn.close()

            with open(filepath, "w") as f:
                f.write("user_id,first_name,username,first_seen\n")
                for user in users:
                    user_id, first_name, username, first_seen = user
                    f.write(
                        f"{user_id},{first_name or ''},"
                        f"{username or ''},\"({first_seen})\"\n"
                    )

            logger.info(f"Users exported to {filepath} ({len(users)} users)")
            return True

        except Exception as e:
            logger.error(f"Failed to export users: {e}")
            return False
