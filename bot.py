#!/usr/bin/env python3
"""
Max Bot API - Long Polling Example
Detects when messages are sent to the bot using long polling mechanism.
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class MaxBotAPI:
    """Max Bot API client with long polling support."""
    
    BASE_URL = "https://platform-api.max.ru"
    
    def __init__(self, token: str):
        """
        Initialize the Max Bot API client.
        
        Args:
            token: Bot token from @MasterBot
        """
        self.token = token
        self.headers = {
            "Authorization": token,  # Using Authorization header instead of query param
            "Content-Type": "application/json"
        }
        
    def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the bot.
        
        Returns:
            Bot information or None on error
        """
        url = f"{self.BASE_URL}/me"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get bot info: {e}")
            return None
    
    def get_updates(
        self,
        marker: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        types: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get updates using long polling.
        
        Args:
            marker: Marker for getting next updates (if None, gets all new updates)
            limit: Maximum number of updates to retrieve (1-1000, default 100)
            timeout: Timeout in seconds for long polling (0-90, default 30)
            types: List of update types to receive (e.g., ['message_created', 'message_callback'])
        
        Returns:
            Dictionary with 'updates' list and 'marker' for next request, or None on error
        """
        url = f"{self.BASE_URL}/updates"
        params = {
            "limit": limit,
            "timeout": timeout
        }
        
        if marker is not None:
            params["marker"] = marker
            
        if types:
            params["types"] = ",".join(types)
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get updates: {e}")
            return None
    
    def send_message(
        self,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        text: str = "",
        attachments: Optional[List[Dict]] = None,
        disable_link_preview: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to a chat or user.
        
        Args:
            chat_id: Chat ID to send message to
            user_id: User ID to send message to (for direct messages)
            text: Message text (max 4000 characters)
            attachments: List of attachments
            disable_link_preview: If True, disable link preview
        
        Returns:
            Sent message information or None on error
        """
        url = f"{self.BASE_URL}/messages"
        params = {
            "disable_link_preview": disable_link_preview
        }
        
        if chat_id:
            params["chat_id"] = chat_id
        if user_id:
            params["user_id"] = user_id
            
        body = {
            "text": text,
            "attachments": attachments or [],
            "link": None
        }
        
        try:
            response = requests.post(url, headers=self.headers, params=params, json=body)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return None


class MaxBot:
    """Max Bot with long polling support."""
    
    def __init__(self, token: str):
        """
        Initialize the bot.
        
        Args:
            token: Bot token from @MasterBot
        """
        self.api = MaxBotAPI(token)
        self.marker: Optional[int] = None
        self.running = False
        
    def start(self):
        """Start the bot with long polling."""
        # Get bot info
        bot_info = self.api.get_me()
        if not bot_info:
            logger.error("Failed to get bot information. Check your token.")
            return
            
        logger.info(f"Bot started: {bot_info.get('first_name', 'Unknown')} (@{bot_info.get('username', 'unknown')})")
        logger.info(f"Bot ID: {bot_info.get('user_id')}")
        
        self.running = True
        logger.info("Starting long polling...")
        
        try:
            while self.running:
                self._poll_updates()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.running = False
            
    def stop(self):
        """Stop the bot."""
        self.running = False
        
    def _poll_updates(self):
        """Poll for updates from the API."""
        result = self.api.get_updates(
            marker=self.marker,
            limit=100,
            timeout=30,
            types=None  # Get all update types; you can filter: ['message_created', 'message_callback', etc.]
        )
        
        if not result:
            # Error occurred, wait a bit before retrying
            time.sleep(5)
            return
            
        updates = result.get("updates", [])
        new_marker = result.get("marker")
        
        # Process updates
        for update in updates:
            self.handle_update(update)
        
        # Update marker for next request
        if new_marker is not None:
            self.marker = new_marker
            
    def handle_update(self, update: Dict[str, Any]):
        """
        Handle incoming update.
        
        Args:
            update: Update object from the API
        """
        update_type = update.get("update_type")
        timestamp = update.get("timestamp")
        
        logger.info(f"Received update: {update_type} at {timestamp}")
        
        # Handle different update types
        if update_type == "message_created":
            self.on_message_created(update)
        elif update_type == "message_callback":
            self.on_callback(update)
        elif update_type == "message_edited":
            self.on_message_edited(update)
        elif update_type == "message_removed":
            self.on_message_removed(update)
        elif update_type == "bot_started":
            self.on_bot_started(update)
        elif update_type == "bot_stopped":
            self.on_bot_stopped(update)
        elif update_type == "bot_added":
            self.on_bot_added_to_chat(update)
        elif update_type == "bot_removed":
            self.on_bot_removed_from_chat(update)
        else:
            logger.debug(f"Unhandled update type: {update_type}")
            
    def on_message_created(self, update: Dict[str, Any]):
        """
        Handle new message.
        
        Args:
            update: Update object with message_created type
        """
        message = update.get("message", {})
        sender = message.get("sender", {})
        body = message.get("body", {})
        recipient = message.get("recipient", {})
        
        user_name = sender.get("first_name", "Unknown")
        user_id = sender.get("user_id")
        text = body.get("text", "")
        chat_id = recipient.get("chat_id")
        
        logger.info(f"💬 New message from {user_name} (ID: {user_id}): {text}")
        
        # Echo example - reply to the user
        if text and not sender.get("is_bot", False):
            reply_text = f"You said: {text}"
            
            # Send reply
            if chat_id:
                self.api.send_message(chat_id=chat_id, text=reply_text)
            elif user_id:
                self.api.send_message(user_id=user_id, text=reply_text)
                
    def on_callback(self, update: Dict[str, Any]):
        """
        Handle button callback.
        
        Args:
            update: Update object with message_callback type
        """
        callback = update.get("callback", {})
        user = callback.get("user", {})
        payload = callback.get("payload", "")
        
        user_name = user.get("first_name", "Unknown")
        logger.info(f"🔘 Button pressed by {user_name}, payload: {payload}")
        
    def on_message_edited(self, update: Dict[str, Any]):
        """Handle edited message."""
        message = update.get("message", {})
        body = message.get("body", {})
        text = body.get("text", "")
        logger.info(f"✏️  Message edited: {text}")
        
    def on_message_removed(self, update: Dict[str, Any]):
        """Handle removed message."""
        message_id = update.get("message_id", "")
        logger.info(f"🗑️  Message removed: {message_id}")
        
    def on_bot_started(self, update: Dict[str, Any]):
        """Handle bot started by user."""
        user = update.get("user", {})
        user_name = user.get("first_name", "Unknown")
        user_id = user.get("user_id")
        payload = update.get("payload")
        
        logger.info(f"🚀 Bot started by {user_name} (ID: {user_id})")
        
        # Send welcome message
        welcome_text = f"Hello {user_name}! 👋\n\nI'm a bot that echoes your messages."
        if payload:
            welcome_text += f"\n\nStart payload: {payload}"
            
        self.api.send_message(user_id=user_id, text=welcome_text)
        
    def on_bot_stopped(self, update: Dict[str, Any]):
        """Handle bot stopped by user."""
        user = update.get("user", {})
        user_name = user.get("first_name", "Unknown")
        logger.info(f"🛑 Bot stopped by {user_name}")
        
    def on_bot_added_to_chat(self, update: Dict[str, Any]):
        """Handle bot added to chat."""
        chat_id = update.get("chat_id")
        user = update.get("user", {})
        user_name = user.get("first_name", "Unknown")
        
        logger.info(f"➕ Bot added to chat {chat_id} by {user_name}")
        
        # Send greeting to chat
        self.api.send_message(
            chat_id=chat_id,
            text=f"Hello everyone! Thanks for adding me, {user_name}! 👋"
        )
        
    def on_bot_removed_from_chat(self, update: Dict[str, Any]):
        """Handle bot removed from chat."""
        chat_id = update.get("chat_id")
        user = update.get("user", {})
        user_name = user.get("first_name", "Unknown")
        
        logger.info(f"➖ Bot removed from chat {chat_id} by {user_name}")


def main():
    """Main entry point."""
    # Get bot token from environment
    token = os.getenv("BOT_TOKEN")
    
    if not token:
        logger.error("BOT_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token:")
        logger.error("BOT_TOKEN=your_token_here")
        sys.exit(1)
    
    # Create and start bot
    bot = MaxBot(token)
    bot.start()


if __name__ == "__main__":
    main()
