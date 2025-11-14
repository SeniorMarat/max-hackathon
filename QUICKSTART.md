# Quick Start Guide

## Setup

1. **Install dependencies**:

```bash
uv sync
# or
pip install -e .
```

2. **Configure environment**:

```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run the bot**:

```bash
python bot.py
```

## Environment Variables

```env
# Required
BOT_TOKEN=your_bot_token_from_masterbot
GIGACHAT_CREDENTIALS=your_gigachat_api_key

# Optional
GIGACHAT_SCOPE=GIGACHAT_API_PERS  # or GIGACHAT_API_CORP
GIGACHAT_MODEL=GigaChat            # or GigaChat-Pro, GigaChat-Max
```

## Bot Commands

- `/start` or `/help` - Show welcome message
- `/clear` - Clear conversation history
- `/info` - Show session statistics

## Architecture

```
┌─────────────────┐
│    bot.py       │  Entry point
│  (main script) │
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │  bot/main.py         │  Bot logic
    │  MaxBotWithGigaChat  │  - Handlers
    │                      │  - Session management
    └────┬────────┬────────┘
         │        │
    ┌────▼────┐  ┌▼──────────────┐
    │ maxbot/ │  │  llm/         │
    │ Dispatcher│  GigaChatClient│
    │ Types   │  │  - Sessions   │
    │ Filters │  │  - History    │
    └─────────┘  └───────────────┘
```

## Session Management

### Private Chats

- Session ID: `chat_id`
- One conversation per user

### Group Chats

- Session ID: `chat_id:user_id`
- Separate conversation per user in the group

## Customization Examples

### Change Model

```python
# In .env
GIGACHAT_MODEL=GigaChat-Pro
```

### Add Custom Command

```python
# In bot/main.py, inside _register_handlers()
@self.dp.message(commands="joke")
async def tell_joke(message: Message):
    response = await self.llm.chat_async(
        message="Tell me a joke",
        session_id=self._get_session_id(message)
    )
    if response and message.chat_id:
        self.bot.send_message(chat_id=message.chat_id, text=response)
```

### Filter by Chat Type

```python
# Only respond in private chats
@self.dp.message(F.text() & F.chat_type("dialog"))
async def private_only(message: Message):
    # Your logic here
    pass
```

## Troubleshooting

### Bot doesn't respond

1. Check `.env` file exists with correct tokens
2. Verify GigaChat credentials are valid
3. Check logs for errors: `level=logging.DEBUG`

### "Import Error" when running

```bash
# Make sure you're in the project root
cd /path/to/max-hackathon

# Install in editable mode
pip install -e .
```

### GigaChat API errors

1. Verify credentials: `GIGACHAT_CREDENTIALS`
2. Check scope matches your account: `GIGACHAT_API_PERS` or `GIGACHAT_API_CORP`
3. Ensure SSL certificates are configured (uses `verify_ssl_certs=False` for dev)

## Development

### Enable Debug Logging

```python
# In bot.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Test Without GigaChat

Use `example_bot.py` to test the framework without LLM integration:

```bash
python example_bot.py
```

## Next Steps

1. Customize system prompt in `bot/main.py`
2. Add custom commands for your use case
3. Implement filters for specific chat types or users
4. Add error handling and retries
5. Deploy to a server for 24/7 operation

## Resources

- [Max Bot API Docs](https://dev.max.ru/docs-api)
- [GigaChat Docs](https://developers.sber.ru/)
- [maxbot Framework Guide](./MAXBOT_README.md)
- [Swagger API Spec](./swagger.json)
