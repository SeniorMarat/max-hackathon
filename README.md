# Max Bot - Long Polling Example

This is a Python bot for the Max Bot API that uses **long polling** to detect and respond to messages sent to the bot.

## 🚀 Features

- ✅ **Long Polling** - Efficiently receives updates from the Max Bot API
- ✅ **Authorization Header** - Uses `Authorization` header for token (query parameters are deprecated)
- ✅ **Message Detection** - Detects when messages are sent to the bot
- ✅ **Echo Bot** - Responds to user messages
- ✅ **Event Handlers** - Handles various update types:
  - Message created/edited/removed
  - Button callbacks
  - Bot started/stopped
  - Bot added/removed from chats
- ✅ **Logging** - Comprehensive logging for debugging

## 📋 Prerequisites

- Python 3.7+
- Max Bot token (get from [@MasterBot](https://tt.me/MasterBot))

## 🛠️ Installation

1. **Clone the repository** (or create the project):
```bash
cd /Users/marat/projects/max-hackathon
```

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure your bot token**:
```bash
cp .env.example .env
```

Then edit `.env` and add your bot token:
```
BOT_TOKEN=your_actual_token_here
```

⚠️ **Important**: The bot now uses the `Authorization` header for authentication instead of query parameters. Make sure your token is properly set in the `.env` file.

## 🏃 Running the Bot

Start the bot with:
```bash
python bot.py
```

Or make it executable and run directly:
```bash
chmod +x bot.py
./bot.py
```

The bot will:
1. Connect to the Max Bot API
2. Display bot information
3. Start long polling for updates
4. Echo any messages sent to it
5. Respond to various events

## 📚 API Documentation

This bot implements the Max Bot API as described in the `swagger.json` file. Key endpoints used:

- **GET /me** - Get bot information
- **GET /updates** - Long polling for updates (with Authorization header)
- **POST /messages** - Send messages

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

| Update Type | Description |
|------------|-------------|
| `message_created` | New message received |
| `message_edited` | Message was edited |
| `message_removed` | Message was deleted |
| `message_callback` | Button was pressed |
| `bot_started` | User started the bot |
| `bot_stopped` | User stopped the bot |
| `bot_added` | Bot added to a chat |
| `bot_removed` | Bot removed from a chat |

## 💡 Customization

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

## Install using UV

This project can optionally use the `uv` package manager instead of `pip`.

#### 1. Install UV:
```bash
pip install uv
```

#### 2. Install all dependencies from pyproject.toml
```bash
uv sync
```

#### 3. Activate virtual env
```bash
source .venv/bin/activate
```

This will automatically:
- create a virtual environment (`.venv`)
- install all packages
- lock versions exactly as in `uv.lock`

### Running LightRAG server locally

After installing:

```bash
lightrag-server
```
