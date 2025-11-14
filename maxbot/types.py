"""
Type definitions for Max Bot API
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class UpdateType(str, Enum):
    """Update types from Max Bot API"""
    MESSAGE_CREATED = "message_created"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_REMOVED = "message_removed"
    MESSAGE_CALLBACK = "message_callback"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ADDED = "bot_added"
    BOT_REMOVED = "bot_removed"
    USER_ADDED = "user_added"
    USER_REMOVED = "user_removed"
    CHAT_TITLE_CHANGED = "chat_title_changed"
    MESSAGE_CHAT_CREATED = "message_chat_created"


class ChatType(str, Enum):
    """Chat types"""
    DIALOG = "dialog"
    CHAT = "chat"
    CHANNEL = "channel"


@dataclass
class User:
    """User object"""
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = False
    last_activity_time: Optional[int] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    full_avatar_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from API response"""
        return cls(
            user_id=data.get("user_id", 0),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name"),
            username=data.get("username"),
            is_bot=data.get("is_bot", False),
            last_activity_time=data.get("last_activity_time"),
            description=data.get("description"),
            avatar_url=data.get("avatar_url"),
            full_avatar_url=data.get("full_avatar_url"),
        )
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
    
    @property
    def mention(self) -> str:
        """Get mention string"""
        if self.username:
            return f"@{self.username}"
        return self.first_name


@dataclass
class Recipient:
    """Message recipient"""
    chat_id: Optional[int] = None
    chat_type: Optional[str] = None
    user_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recipient":
        """Create Recipient from API response"""
        return cls(
            chat_id=data.get("chat_id"),
            chat_type=data.get("chat_type"),
            user_id=data.get("user_id"),
        )


@dataclass
class Attachment:
    """Message attachment"""
    type: str
    payload: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attachment":
        """Create Attachment from API response"""
        return cls(
            type=data.get("type", ""),
            payload=data.get("payload"),
        )


@dataclass
class MessageBody:
    """Message body"""
    mid: str
    seq: int
    text: Optional[str] = None
    attachments: List[Attachment] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageBody":
        """Create MessageBody from API response"""
        attachments_data = data.get("attachments", [])
        attachments = [Attachment.from_dict(a) for a in attachments_data] if attachments_data else []
        
        return cls(
            mid=data.get("mid", ""),
            seq=data.get("seq", 0),
            text=data.get("text"),
            attachments=attachments,
        )


@dataclass
class Chat:
    """Chat object"""
    chat_id: int
    type: str
    title: Optional[str] = None
    status: Optional[str] = None
    participants_count: Optional[int] = None
    is_public: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chat":
        """Create Chat from API response"""
        return cls(
            chat_id=data.get("chat_id", 0),
            type=data.get("type", "chat"),
            title=data.get("title"),
            status=data.get("status"),
            participants_count=data.get("participants_count"),
            is_public=data.get("is_public", False),
        )


@dataclass
class Message:
    """Message object"""
    body: MessageBody
    recipient: Recipient
    timestamp: int
    sender: Optional[User] = None
    link: Optional[Dict[str, Any]] = None
    stat: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    
    # Convenience properties
    _chat: Optional[Chat] = field(default=None, repr=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create Message from API response"""
        sender_data = data.get("sender")
        sender = User.from_dict(sender_data) if sender_data else None
        
        recipient_data = data.get("recipient", {})
        recipient = Recipient.from_dict(recipient_data)
        
        body_data = data.get("body", {})
        body = MessageBody.from_dict(body_data)
        
        return cls(
            sender=sender,
            recipient=recipient,
            body=body,
            timestamp=data.get("timestamp", 0),
            link=data.get("link"),
            stat=data.get("stat"),
            url=data.get("url"),
        )
    
    @property
    def text(self) -> Optional[str]:
        """Get message text"""
        return self.body.text
    
    @property
    def message_id(self) -> str:
        """Get message ID"""
        return self.body.mid
    
    @property
    def chat_id(self) -> Optional[int]:
        """Get chat ID"""
        return self.recipient.chat_id
    
    @property
    def user_id(self) -> Optional[int]:
        """Get sender user ID"""
        return self.sender.user_id if self.sender else None
    
    @property
    def from_user(self) -> Optional[User]:
        """Alias for sender (aiogram compatibility)"""
        return self.sender
    
    @property
    def chat(self) -> Optional[Chat]:
        """Get chat object (if set)"""
        return self._chat


@dataclass
class Callback:
    """Callback from button press"""
    timestamp: int
    callback_id: str
    user: User
    payload: Optional[str] = None
    message: Optional[Message] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], message: Optional[Message] = None) -> "Callback":
        """Create Callback from API response"""
        user_data = data.get("user", {})
        user = User.from_dict(user_data)
        
        return cls(
            timestamp=data.get("timestamp", 0),
            callback_id=data.get("callback_id", ""),
            user=user,
            payload=data.get("payload"),
            message=message,
        )


@dataclass
class Update:
    """Update object"""
    update_type: UpdateType
    timestamp: int
    raw_data: Dict[str, Any]
    
    # Optional fields based on update type
    message: Optional[Message] = None
    callback: Optional[Callback] = None
    user: Optional[User] = None
    chat_id: Optional[int] = None
    payload: Optional[str] = None
    user_locale: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Update":
        """Create Update from API response"""
        update_type_str = data.get("update_type", "")
        try:
            update_type = UpdateType(update_type_str)
        except ValueError:
            update_type = update_type_str  # type: ignore
        
        # Parse message if present
        message = None
        message_data = data.get("message")
        if message_data:
            message = Message.from_dict(message_data)
        
        # Parse callback if present
        callback = None
        callback_data = data.get("callback")
        if callback_data:
            callback = Callback.from_dict(callback_data, message)
        
        # Parse user if present
        user = None
        user_data = data.get("user")
        if user_data:
            user = User.from_dict(user_data)
        
        return cls(
            update_type=update_type,
            timestamp=data.get("timestamp", 0),
            raw_data=data,
            message=message,
            callback=callback,
            user=user,
            chat_id=data.get("chat_id"),
            payload=data.get("payload"),
            user_locale=data.get("user_locale"),
        )


@dataclass
class BotInfo:
    """Bot information"""
    user_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = True
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BotInfo":
        """Create BotInfo from API response"""
        return cls(
            user_id=data.get("user_id", 0),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name"),
            username=data.get("username"),
            is_bot=data.get("is_bot", True),
            description=data.get("description"),
            avatar_url=data.get("avatar_url"),
        )
