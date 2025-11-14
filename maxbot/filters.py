"""
Filters for message handlers
"""

from typing import Optional, Any, Union, List
from abc import ABC, abstractmethod

from .types import Update


class Filter(ABC):
    """Base filter class"""
    
    @abstractmethod
    def check(self, update: Update) -> bool:
        """Check if update matches the filter"""
        pass
    
    def __call__(self, update: Update) -> bool:
        return self.check(update)
    
    def __and__(self, other: "Filter") -> "AndFilter":
        """Combine filters with AND"""
        return AndFilter(self, other)
    
    def __or__(self, other: "Filter") -> "OrFilter":
        """Combine filters with OR"""
        return OrFilter(self, other)
    
    def __invert__(self) -> "NotFilter":
        """Invert filter"""
        return NotFilter(self)


class AndFilter(Filter):
    """AND combination of filters"""
    
    def __init__(self, *filters: Filter):
        self.filters = filters
    
    def check(self, update: Update) -> bool:
        return all(f.check(update) for f in self.filters)


class OrFilter(Filter):
    """OR combination of filters"""
    
    def __init__(self, *filters: Filter):
        self.filters = filters
    
    def check(self, update: Update) -> bool:
        return any(f.check(update) for f in self.filters)


class NotFilter(Filter):
    """NOT filter"""
    
    def __init__(self, filter: Filter):
        self.filter = filter
    
    def check(self, update: Update) -> bool:
        return not self.filter.check(update)


class TextFilter(Filter):
    """Filter for text messages"""
    
    def __init__(self, text: Optional[Union[str, List[str]]] = None, contains: Optional[str] = None):
        self.text = [text] if isinstance(text, str) else text
        self.contains = contains
    
    def check(self, update: Update) -> bool:
        if not update.message or not update.message.text:
            return False
        
        msg_text = update.message.text
        
        if self.text:
            return msg_text in self.text
        
        if self.contains:
            return self.contains in msg_text
        
        return True  # Any text


class CommandFilter(Filter):
    """Filter for command messages"""
    
    def __init__(self, commands: Optional[Union[str, List[str]]] = None):
        if commands:
            self.commands = [commands] if isinstance(commands, str) else commands
            # Ensure commands start with /
            self.commands = [cmd if cmd.startswith('/') else f'/{cmd}' for cmd in self.commands]
        else:
            self.commands = None
    
    def check(self, update: Update) -> bool:
        if not update.message or not update.message.text:
            return False
        
        text = update.message.text.strip()
        if not text.startswith('/'):
            return False
        
        # Extract command (without @botname)
        command = text.split()[0].split('@')[0]
        
        if self.commands:
            return command in self.commands
        
        return True  # Any command


class ChatTypeFilter(Filter):
    """Filter by chat type"""
    
    def __init__(self, chat_type: Union[str, List[str]]):
        self.chat_types = [chat_type] if isinstance(chat_type, str) else chat_type
    
    def check(self, update: Update) -> bool:
        if not update.message:
            return False
        
        chat_type = update.message.recipient.chat_type
        return chat_type in self.chat_types if chat_type else False


class UserFilter(Filter):
    """Filter by user ID"""
    
    def __init__(self, user_ids: Union[int, List[int]]):
        self.user_ids = [user_ids] if isinstance(user_ids, int) else user_ids
    
    def check(self, update: Update) -> bool:
        user_id = None
        
        if update.message and update.message.sender:
            user_id = update.message.sender.user_id
        elif update.callback:
            user_id = update.callback.user.user_id
        elif update.user:
            user_id = update.user.user_id
        
        return user_id in self.user_ids if user_id else False


class CallbackDataFilter(Filter):
    """Filter for callback data"""
    
    def __init__(self, data: Optional[Union[str, List[str]]] = None, startswith: Optional[str] = None):
        self.data = [data] if isinstance(data, str) else data
        self.startswith = startswith
    
    def check(self, update: Update) -> bool:
        if not update.callback or not update.callback.payload:
            return False
        
        payload = update.callback.payload
        
        if self.data:
            return payload in self.data
        
        if self.startswith:
            return payload.startswith(self.startswith)
        
        return True  # Any callback


class StateFilter(Filter):
    """Filter by FSM state (placeholder for future implementation)"""
    
    def __init__(self, state: Any):
        self.state = state
    
    def check(self, update: Update) -> bool:
        # TODO: Implement FSM
        return True


class F:
    """Magic filter factory (aiogram-style)"""
    
    @staticmethod
    def text(text: Optional[Union[str, List[str]]] = None, contains: Optional[str] = None) -> TextFilter:
        """Filter by text"""
        return TextFilter(text=text, contains=contains)
    
    @staticmethod
    def command(commands: Optional[Union[str, List[str]]] = None) -> CommandFilter:
        """Filter by command"""
        return CommandFilter(commands=commands)
    
    @staticmethod
    def chat_type(chat_type: Union[str, List[str]]) -> ChatTypeFilter:
        """Filter by chat type"""
        return ChatTypeFilter(chat_type=chat_type)
    
    @staticmethod
    def user(user_ids: Union[int, List[int]]) -> UserFilter:
        """Filter by user ID"""
        return UserFilter(user_ids=user_ids)
    
    @staticmethod
    def callback_data(data: Optional[Union[str, List[str]]] = None, startswith: Optional[str] = None) -> CallbackDataFilter:
        """Filter by callback data"""
        return CallbackDataFilter(data=data, startswith=startswith)
