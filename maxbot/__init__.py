"""
MaxBot - A Python framework for Max Bot API (similar to aiogram for Telegram)
"""

from .bot import Bot
from .dispatcher import Dispatcher
from .filters import CommandFilter, F, Filter, TextFilter
from .types import (
    Attachment,
    Callback,
    Chat,
    ChatType,
    Message,
    MessageBody,
    Recipient,
    Update,
    UpdateType,
    User,
)

__version__ = "0.1.0"
__all__ = [
    "Bot",
    "Dispatcher",
    "Message",
    "Update",
    "User",
    "Chat",
    "Callback",
    "MessageBody",
    "Recipient",
    "Attachment",
    "UpdateType",
    "ChatType",
    "F",
    "Filter",
    "CommandFilter",
    "TextFilter",
]
