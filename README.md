# Max Bot with GigaChat 🤖

A production-ready Max Bot with GigaChat LLM integration, built using a clean modular architecture and the `maxbot` framework.

## ✨ Features

- 🤖 **GigaChat Integration** - Powered by Sber's GigaChat LLM
- 💬 **Session Management** - Maintains conversation context per user/chat
- 🎯 **Decorator-based Handlers** - Clean, intuitive `@dp.message()` syntax
- 🔍 **Smart Routing** - Filters for commands, text, callbacks, and more
- 📝 **Full Type Hints** - Type-safe code with autocomplete support
- 🔄 **Long Polling** - Efficient updates with automatic reconnection
- 🏗️ **Modular Architecture** - Clean separation of concerns:
  - `bot/` - Bot logic and handlers
  - `llm/` - GigaChat client and session management
  - `maxbot/` - Framework core (dispatcher, types, filters)
- 🛡️ **Modern Authentication** - Uses `Authorization` header (not query params)
- 🌐 **Multi-chat Support** - Works in private chats and groups
- 🔧 **Environment Configuration** - Easy setup with `.env` file

## 📋 Prerequisites

- Python 3.12+
- Max Bot token (get from [@MasterBot](https://tt.me/MasterBot))
- GigaChat API credentials (get from [developers.sber.ru](https://developers.sber.ru/))

## 🛠️ Installation

1. **Clone the repository**:

```bash
git clone https://github.com/SeniorMarat/max-hackathon.git
cd max-hackathon
```

2. **Install dependencies using `uv`** (recommended):

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

Or using pip:

```bash
pip install -e .
```

3. **Configure your credentials**:

```bash
cp .env.example .env
```

Then edit `.env` and add your tokens:

```env
# Max Bot token from @MasterBot
BOT_TOKEN=your_bot_token_here

# GigaChat credentials from developers.sber.ru
GIGACHAT_CREDENTIALS=your_gigachat_api_key

# GigaChat settings
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
```

⚠️ **Important**:

- The bot uses the `Authorization` header (not query parameters)
- GigaChat credentials must be valid for the selected scope
- Available models: `GigaChat`, `GigaChat-Pro`, `GigaChat-Max`

## 🏃 Running the Bot

### Main Bot (with GigaChat)

```bash
python bot.py
```

Or make it executable:

```bash
chmod +x bot.py
./bot.py
```

### Example Bot (framework demo, no LLM)

```bash
python example_bot.py
```

The bot will:

1. ✅ Initialize GigaChat client
2. ✅ Connect to Max Bot API
3. ✅ Display bot information
4. ✅ Start long polling for updates
5. ✅ Respond to messages using GigaChat
6. ✅ Maintain conversation context per session

## � Project Structure

```
max-hackathon/
├── bot/                    # Bot module
│   ├── __init__.py        # Module exports
│   └── main.py            # Bot logic with GigaChat integration
├── llm/                    # LLM module
│   ├── __init__.py        # Module exports
│   └── gigachat.py        # GigaChat client with session management
├── maxbot/                 # Framework package
│   ├── __init__.py        # Package exports
│   ├── bot.py             # Bot API client
│   ├── dispatcher.py      # Dispatcher with decorators
│   ├── types.py           # Type definitions (Message, Update, etc.)
│   └── filters.py         # Filter classes (F.text(), F.command(), etc.)
├── bot.py                  # Main entry point (GigaChat bot)
├── example_bot.py         # Example bot (framework demo)
├── pyproject.toml         # Project configuration and dependencies
├── .env                   # Your credentials (not in git)
├── .env.example          # Template for .env
└── README.md             # This file
```

## 🎯 Commands

The bot supports the following commands:

| Command           | Description                                    |
| ----------------- | ---------------------------------------------- |
| `/start`, `/help` | Show welcome message and available commands    |
| `/clear`          | Clear conversation history for current session |
| `/info`           | Show session information and statistics        |

## �📚 API Documentation

This bot implements the Max Bot API as described in the `swagger.json` file. Key endpoints used:

- **GET /me** - Get bot information
- **GET /updates** - Long polling for updates (with Authorization header)
- **POST /messages** - Send messages
- **POST /chats/{chatId}/actions** - Send chat actions (typing, etc.)

### Long Polling Parameters

The bot uses these parameters for long polling:

- `limit`: Maximum number of updates (default: 100, max: 1000)
- `timeout`: Long polling timeout in seconds (default: 30, max: 90)
- `marker`: Marker for pagination (auto-managed by the bot)
- `types`: Filter update types (optional)

### Authentication

**Important change**: Token authentication now uses the `Authorization` header:

```python
headers = {
    "Authorization": your_token_here,
    "Content-Type": "application/json"
}
```

The old method of passing `access_token` as a query parameter is **no longer supported**.

## 🎯 Update Types

The bot handles these update types:

| Update Type        | Description             |
| ------------------ | ----------------------- |
| `message_created`  | New message received    |
| `message_edited`   | Message was edited      |
| `message_removed`  | Message was deleted     |
| `message_callback` | Button was pressed      |
| `bot_started`      | User started the bot    |
| `bot_stopped`      | User stopped the bot    |
| `bot_added`        | Bot added to a chat     |
| `bot_removed`      | Bot removed from a chat |

## � Customization

### Changing GigaChat Model

Edit your `.env` file:

```env
# Use GigaChat-Pro for better responses
GIGACHAT_MODEL=GigaChat-Pro

# Or use GigaChat-Max for maximum capability
GIGACHAT_MODEL=GigaChat-Max
```

### Customizing System Prompt

Edit `bot/main.py`:

```python
self.system_prompt = """Your custom system prompt here.
Define the bot's personality and behavior."""
```

### Adjusting History Length

In `bot/main.py`:

```python
self.llm = GigaChatClient(
    credentials=gigachat_credentials,
    scope=gigachat_scope,
    model=gigachat_model,
    max_history=20  # Increase to keep more context
)
```

### Adding Custom Handlers

Edit `bot/main.py` in the `_register_handlers` method:

```python
@self.dp.message(commands="custom")
async def custom_command(message: Message):
    """Your custom command handler"""
    # Your logic here
    pass
```

### Modify Message Handler

Edit the `on_message_created` method in `bot.py`:

```python
def on_message_created(self, update: Dict[str, Any]):
    message = update.get("message", {})
    sender = message.get("sender", {})
    body = message.get("body", {})
    text = body.get("text", "")

    # Your custom logic here
    # Example: respond only to specific commands
    if text.startswith("/"):
        self.handle_command(text, sender, message)
```

### Filter Update Types

Modify the `_poll_updates` method to filter specific update types:

```python
result = self.api.get_updates(
    marker=self.marker,
    limit=100,
    timeout=30,
    types=["message_created", "message_callback"]  # Only get these types
)
```

## 🐛 Debugging

The bot includes detailed logging. To see debug messages, change the logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📝 Project Structure

```
max-hackathon/
├── bot.py              # Main bot script with long polling
├── requirements.txt    # Python dependencies
├── .env               # Your bot token (not in git)
├── .env.example       # Template for .env
├── .gitignore         # Git ignore rules
├── swagger.json       # Max Bot API specification
└── README.md          # This file
```

## 🔒 Security

- Never commit your `.env` file or expose your bot token
- The `.gitignore` file is configured to exclude sensitive files
- Use the `Authorization` header instead of query parameters for better security

## 📖 Additional Resources

- [Max Bot API Documentation](https://dev.max.ru/docs-api)
- Max Developer Portal: [https://dev.max.ru](https://dev.max.ru)
- Get your bot token from [@MasterBot](https://tt.me/MasterBot)

## 🤝 Contributing

Feel free to fork this project and customize it for your needs!

## 📄 License

This project is open source and available under the Apache 2.0 License.
