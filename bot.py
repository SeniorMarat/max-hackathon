"""
Example bot using the maxbot framework (aiogram-style)
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from maxbot import Bot, Dispatcher, F
from maxbot.types import Message

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


@dp.message(F.text())
async def handle_text_message(message: Message):
    """Handle any text message (that's not a command)"""
    if not message.from_user:
        return

    user_text = message.text or ""
    chat_id = str(message.chat_id) if message.chat_id else ""
    user_id = str(message.user_id) if message.user_id else ""

    # Create session ID (similar to your example)
    session_id = (
        f"{chat_id}:{user_id}"
        if message.recipient.chat_type in ["chat", "group"]
        else chat_id
    )

    user_name = (
        message.from_user.username or message.from_user.first_name or "Anonymous"
    )

    logger.info(f"Message from {user_name} in chat {chat_id}: {user_text}")

    # Send typing action
    if message.chat_id:
        bot.send_chat_action(message.chat_id, "typing_on")

    # Echo response (replace with your LLM call)
    response = f"You said: {user_text}\n\n(session_id: {session_id})"

    if message.chat_id:
        bot.send_message(chat_id=message.chat_id, text=response)
    elif message.user_id:
        bot.send_message(user_id=message.user_id, text=response)


async def main():
    """Main entry point"""
    token = os.getenv("BOT_TOKEN")

    if not token:
        logger.error("BOT_TOKEN not found in environment variables!")
        logger.error("Please create a .env file with your bot token:")
        logger.error("BOT_TOKEN=your_token_here")
        return

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
