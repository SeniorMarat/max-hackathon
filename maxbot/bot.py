"""
Bot client for Max Bot API
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from .types import BotInfo, Message

logger = logging.getLogger(__name__)


class Bot:
    """Max Bot API client"""

    BASE_URL = "https://platform-api.max.ru"

    def __init__(self, token: str):
        """
        Initialize the Bot client.

        Args:
            token: Bot token from @MasterBot
        """
        self.token = token
        self.headers = {"Authorization": token, "Content-Type": "application/json"}
        self._me: Optional[BotInfo] = None

    def get_me(self) -> Optional[BotInfo]:
        """
        Get information about the bot.

        Returns:
            Bot information or None on error
        """
        url = f"{self.BASE_URL}/me"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            self._me = BotInfo.from_dict(data)
            return self._me
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get bot info: {e}")
            return None

    @property
    def me(self) -> Optional[BotInfo]:
        """Get cached bot info"""
        return self._me

    def get_updates(
        self,
        marker: Optional[int] = None,
        limit: int = 100,
        timeout: int = 30,
        types: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get updates using long polling.

        Args:
            marker: Marker for getting next updates
            limit: Maximum number of updates to retrieve (1-1000)
            timeout: Timeout in seconds for long polling (0-90)
            types: List of update types to receive

        Returns:
            Dictionary with 'updates' and 'marker'
        """
        url = f"{self.BASE_URL}/updates"
        params = {"limit": limit, "timeout": timeout}

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
        disable_link_preview: bool = False,
        notify: bool = True,
    ) -> Optional[Message]:
        """
        Send a message to a chat or user.

        Args:
            chat_id: Chat ID to send message to
            user_id: User ID to send message to
            text: Message text
            attachments: List of attachments
            disable_link_preview: Disable link preview
            notify: Send notification

        Returns:
            Sent message or None on error
        """
        url = f"{self.BASE_URL}/messages"
        params = {"disable_link_preview": disable_link_preview}

        if chat_id:
            params["chat_id"] = chat_id
        if user_id:
            params["user_id"] = user_id

        body = {
            "text": text,
            "attachments": attachments or [],
            "link": None,
            "notify": notify,
        }

        try:
            response = requests.post(
                url, headers=self.headers, params=params, json=body
            )
            response.raise_for_status()
            result = response.json()
            message_data = result.get("message")
            if message_data:
                return Message.from_dict(message_data)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return None

    def send_chat_action(self, chat_id: int, action: str = "typing_on") -> bool:
        """
        Send a chat action (typing, sending photo, etc).

        Args:
            chat_id: Chat ID
            action: Action type (typing_on, sending_photo, etc)

        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/chats/{chat_id}/actions"
        body = {"action": action}

        try:
            response = requests.post(url, headers=self.headers, json=body)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send chat action: {e}")
            return False

    def edit_message(
        self,
        message_id: str,
        text: Optional[str] = None,
        attachments: Optional[List[Dict]] = None,
    ) -> bool:
        """
        Edit a message.

        Args:
            message_id: Message ID to edit
            text: New text
            attachments: New attachments

        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/messages"
        params = {"message_id": message_id}
        body = {"text": text, "attachments": attachments, "link": None}

        try:
            response = requests.put(url, headers=self.headers, params=params, json=body)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to edit message: {e}")
            return False

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.

        Args:
            message_id: Message ID to delete

        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/messages"
        params = {"message_id": message_id}

        try:
            response = requests.delete(url, headers=self.headers, params=params)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    def answer_callback(
        self,
        callback_id: str,
        text: Optional[str] = None,
        notification: Optional[str] = None,
    ) -> bool:
        """
        Answer a callback query.

        Args:
            callback_id: Callback ID
            text: Message text (to edit the message)
            notification: Notification text (one-time popup)

        Returns:
            True if successful
        """
        url = f"{self.BASE_URL}/answers"
        params = {"callback_id": callback_id}
        body = {}

        if text:
            body["message"] = {"text": text, "attachments": [], "link": None}
        if notification:
            body["notification"] = notification

        try:
            response = requests.post(
                url, headers=self.headers, params=params, json=body
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to answer callback: {e}")
            return False
