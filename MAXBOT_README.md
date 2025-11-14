# maxbot - Max Bot API Framework 🤖

A Python framework for building Max bots with a clean, decorator-based API similar to aiogram.

## ✨ Features

- 🎯 **Decorator-based handlers** - Clean, intuitive `@dp.message()` syntax
- 🔍 **Powerful filters** - Filter messages by text, commands, chat type, and more
- 📝 **Type hints** - Full type annotation support
- 🔄 **Long polling** - Built-in long polling with automatic reconnection
- 🎨 **Aiogram-style API** - Familiar syntax if you've used aiogram
- ⚡ **Async support** - Async/await for handlers
- 🛡️ **Authorization header** - Uses modern `Authorization` header (not query params)

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd max-hackathon

# Install dependencies
pip install -r requirements.txt

# Set up your bot token
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

## 🚀 Quick Start

```python
import asyncio
import os
from maxbot import Bot, Dispatcher, F
from maxbot.types import Message

# Initialize bot and dispatcher
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# Handle /start command
@dp.message(commands="start")
async def start_handler(message: Message):
    await bot.send_message(
        chat_id=message.chat_id,
        text=f"Hello, {message.from_user.full_name}!"
    )

# Handle any text message
@dp.message(F.text())
async def text_handler(message: Message):
    await bot.send_message(
        chat_id=message.chat_id,
        text=f"You said: {message.text}"
    )

# Start polling
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📚 Documentation

### Message Handlers

#### Basic Message Handler

```python
@dp.message()
async def handle_all_messages(message: Message):
    """Handle all messages"""
    print(f"Message from {message.from_user.full_name}: {message.text}")
```

#### Command Filters

```python
# Single command
@dp.message(commands="start")
async def start(message: Message):
    pass

# Multiple commands
@dp.message(commands=["start", "help"])
async def start_help(message: Message):
    pass

# Using F filter
@dp.message(F.command("start"))
async def start(message: Message):
    pass
```

#### Text Filters

```python
# Exact text match
@dp.message(text="hello")
async def hello(message: Message):
    pass

# Multiple text options
@dp.message(text=["hi", "hello", "hey"])
async def greetings(message: Message):
    pass

# Text contains
@dp.message(F.text(contains="python"))
async def python_mention(message: Message):
    pass

# Any text message
@dp.message(F.text())
async def any_text(message: Message):
    pass
```

#### Chat Type Filters

```python
# Only in private chats
@dp.message(F.chat_type("dialog"))
async def private_only(message: Message):
    pass

# Only in groups
@dp.message(F.chat_type(["chat", "group"]))
async def group_only(message: Message):
    pass
```

#### Combining Filters

```python
# AND combination
@dp.message(F.text() & F.chat_type("dialog"))
async def private_text(message: Message):
    """Only text messages in private chats"""
    pass

# OR combination
@dp.message(F.command("start") | F.command("help"))
async def start_or_help(message: Message):
    pass
```

### Callback Handlers

```python
@dp.callback_query(data="button_1")
async def handle_button(callback: Callback):
    """Handle button click"""
    await bot.answer_callback(
        callback_id=callback.callback_id,
        notification="Button clicked!"
    )
```

### Update Handlers

```python
from maxbot.types import UpdateType

@dp.update(UpdateType.BOT_STARTED)
async def bot_started(update: Update):
    """Handle bot started by user"""
    await bot.send_message(
        user_id=update.user.user_id,
        text=f"Welcome, {update.user.full_name}!"
    )

@dp.update(UpdateType.BOT_ADDED)
async def bot_added_to_chat(update: Update):
    """Handle bot added to chat"""
    await bot.send_message(
        chat_id=update.chat_id,
        text="Thanks for adding me!"
    )
```

### Startup & Shutdown

```python
@dp.startup()
async def on_startup():
    """Called when bot starts"""
    print("Bot is starting up...")

@dp.shutdown()
async def on_shutdown():
    """Called when bot stops"""
    print("Bot is shutting down...")
```

## 🎯 Available Filters

### Built-in Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `F.text()` | Match text messages | `F.text("hello")` |
| `F.command()` | Match commands | `F.command("start")` |
| `F.chat_type()` | Match chat type | `F.chat_type("dialog")` |
| `F.user()` | Match user ID | `F.user(123456)` |
| `F.callback_data()` | Match callback data | `F.callback_data("btn_1")` |

### Filter Operators

```python
# AND
F.text() & F.chat_type("dialog")

# OR
F.command("start") | F.command("help")

# NOT
~F.user(123456)
```

## 📋 Message Object

```python
@dp.message()
async def handler(message: Message):
    # Accessing message data
    message.text               # Message text
    message.message_id         # Message ID
    message.chat_id            # Chat ID
    message.user_id            # Sender user ID
    message.from_user          # User object (sender)
    message.timestamp          # Unix timestamp
    
    # User information
    message.from_user.user_id
    message.from_user.first_name
    message.from_user.last_name
    message.from_user.username
    message.from_user.full_name   # Computed property
    message.from_user.mention      # @username or first_name
```

## 🤖 Bot Methods

```python
# Send message
await bot.send_message(
    chat_id=123456,
    text="Hello!",
    attachments=[...],
    disable_link_preview=False
)

# Send chat action
await bot.send_chat_action(chat_id=123456, action="typing_on")

# Edit message
await bot.edit_message(
    message_id="mid_123",
    text="Updated text"
)

# Delete message
await bot.delete_message(message_id="mid_123")

# Answer callback
await bot.answer_callback(
    callback_id="callback_123",
    notification="Done!"
)

# Get bot info
bot_info = await bot.get_me()
```

## 🔧 Advanced Usage

### Working with LLMs (like in your example)

```python
@dp.message(F.text())
async def handle_message(message: Message):
    if not message.from_user:
        return

    user_text = message.text or ""
    chat_id = str(message.chat_id) if message.chat_id else ""
    user_id = str(message.user_id) if message.user_id else ""
    
    # Create session ID
    session_id = (
        f"{chat_id}:{user_id}"
        if message.recipient.chat_type in ["group", "chat"]
        else chat_id
    )
    
    user_name = message.from_user.username or message.from_user.first_name or "Anonymous"
    
    # Send typing indicator
    await bot.send_chat_action(message.chat_id, "typing_on")
    
    # Call your LLM
    response = await ask_local_llm(user_text, session_id=session_id)
    
    if response:
        await bot.send_message(chat_id=message.chat_id, text=response)
```

### Custom Filters

```python
from maxbot.filters import Filter
from maxbot.types import Update

class AdminFilter(Filter):
    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids
    
    def check(self, update: Update) -> bool:
        if not update.message or not update.message.from_user:
            return False
        return update.message.from_user.user_id in self.admin_ids

# Usage
admin_filter = AdminFilter([123456, 789012])

@dp.message(admin_filter)
async def admin_only(message: Message):
    await bot.send_message(
        chat_id=message.chat_id,
        text="Admin command executed!"
    )
```

## 🎨 Update Types

| Update Type | Description |
|-------------|-------------|
| `MESSAGE_CREATED` | New message created |
| `MESSAGE_EDITED` | Message was edited |
| `MESSAGE_REMOVED` | Message was deleted |
| `MESSAGE_CALLBACK` | Button was pressed |
| `BOT_STARTED` | User started the bot |
| `BOT_STOPPED` | User stopped the bot |
| `BOT_ADDED` | Bot added to chat |
| `BOT_REMOVED` | Bot removed from chat |
| `USER_ADDED` | User added to chat |
| `USER_REMOVED` | User removed from chat |
| `CHAT_TITLE_CHANGED` | Chat title changed |
| `MESSAGE_CHAT_CREATED` | Chat created via button |

## 🔐 Security

- ✅ Uses `Authorization` header (not query parameters)
- ✅ `.env` file for token management
- ✅ `.gitignore` configured to exclude sensitive files

## 📁 Project Structure

```
max-hackathon/
├── maxbot/                 # Framework package
│   ├── __init__.py        # Package exports
│   ├── bot.py             # Bot client
│   ├── dispatcher.py      # Dispatcher with decorators
│   ├── types.py           # Type definitions
│   └── filters.py         # Filter classes
├── example_bot.py         # Example bot using the framework
├── bot.py                 # Original simple bot (legacy)
├── requirements.txt       # Dependencies
├── .env                   # Your bot token (not in git)
├── .env.example          # Template for .env
└── README.md             # This file
```

## 🤝 Comparison with aiogram

If you're familiar with aiogram for Telegram, maxbot follows similar patterns:

| aiogram | maxbot |
|---------|---------|
| `@dp.message()` | `@dp.message()` ✅ |
| `@dp.callback_query()` | `@dp.callback_query()` ✅ |
| `F.text` | `F.text()` ✅ |
| `F.command` | `F.command()` ✅ |
| `message.from_user` | `message.from_user` ✅ |
| `bot.send_message()` | `bot.send_message()` ✅ |

## 📝 Examples

See `example_bot.py` for a complete example with:
- Command handlers (`/start`, `/help`, `/echo`, `/info`)
- Text message handlers
- Callback handlers
- Update handlers (bot started, bot added to chat, etc.)
- Startup/shutdown handlers

## 🐛 Debugging

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🎓 Learning Resources

- [Max Bot API Documentation](https://dev.max.ru/docs-api)
- [API Swagger Specification](./swagger.json)
- [Get Bot Token from @MasterBot](https://tt.me/MasterBot)

## 📄 License

Apache 2.0

## 🙏 Credits

Inspired by [aiogram](https://github.com/aiogram/aiogram) - the most popular Telegram Bot API framework.
