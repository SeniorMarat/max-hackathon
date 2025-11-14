#!/usr/bin/env python3
"""
Example bot using the maxbot framework (aiogram-style)
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from maxbot import Bot, Dispatcher, F
from maxbot.types import Callback, Message, Update, UpdateType

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


@dp.startup()
async def on_startup():
    """Called when bot starts"""
    logger.info("🚀 Bot is starting up...")


@dp.shutdown()
async def on_shutdown():
    """Called when bot stops"""
    logger.info("🛑 Bot is shutting down...")


@dp.message(commands=["start", "help"])
async def command_start(message: Message):
    """Handle /start and /help commands"""
    user_name = message.from_user.full_name if message.from_user else "Unknown"
    logger.info(f"Start command from {user_name}")

    welcome_text = f"""👋 Hello, {user_name}!

I'm an example bot built with maxbot framework.

Available commands:
/start, /help - Show this message
/echo <text> - Echo your text
/info - Show your user info

Just send me any text and I'll respond!"""

    if message.chat_id:
        bot.send_message(chat_id=message.chat_id, text=welcome_text)
    elif message.user_id:
        bot.send_message(user_id=message.user_id, text=welcome_text)


@dp.message(commands="echo")
async def command_echo(message: Message):
    """Handle /echo command"""
    if not message.text:
        return

    # Extract text after command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        reply = "Usage: /echo <text>"
    else:
        reply = f"🔊 {parts[1]}"

    if message.chat_id:
        bot.send_message(chat_id=message.chat_id, text=reply)
    elif message.user_id:
        bot.send_message(user_id=message.user_id, text=reply)


@dp.message(commands="info")
async def command_info(message: Message):
    """Handle /info command"""
    if not message.from_user:
        return

    user = message.from_user
    info_text = f"""ℹ️ Your Information:

👤 Name: {user.full_name}
🆔 User ID: {user.user_id}
🏷️ Username: {user.mention}
🤖 Is Bot: {user.is_bot}"""

    if message.chat_id:
        info_text += f"\n💬 Chat ID: {message.chat_id}"

    if message.chat_id:
        bot.send_message(chat_id=message.chat_id, text=info_text)
    elif message.user_id:
        bot.send_message(user_id=message.user_id, text=info_text)


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
    response = f"You said: {user_text}\n\n(This is where you would call your LLM with session_id: {session_id})"

    if message.chat_id:
        bot.send_message(chat_id=message.chat_id, text=response)
    elif message.user_id:
        bot.send_message(user_id=message.user_id, text=response)


@dp.callback_query()
async def handle_callback(callback: Callback):
    """Handle button callbacks"""
    user_name = callback.user.full_name
    payload = callback.payload or "no payload"

    logger.info(f"🔘 Callback from {user_name}: {payload}")

    # Answer the callback
    bot.answer_callback(
        callback_id=callback.callback_id, notification=f"Button pressed: {payload}"
    )


@dp.update(UpdateType.BOT_STARTED)
async def bot_started(update: Update):
    """Handle bot started by user"""
    if not update.user:
        return

    user_name = update.user.full_name
    logger.info(f"🚀 Bot started by {user_name}")

    welcome_text = f"👋 Welcome, {user_name}!\n\nThanks for starting the bot. Send /help to see available commands."

    if update.chat_id:
        bot.send_message(user_id=update.user.user_id, text=welcome_text)


@dp.update(UpdateType.BOT_STOPPED)
async def bot_stopped(update: Update):
    """Handle bot stopped by user"""
    if not update.user:
        return

    user_name = update.user.full_name
    logger.info(f"🛑 Bot stopped by {user_name}")


@dp.update(UpdateType.BOT_ADDED)
async def bot_added_to_chat(update: Update):
    """Handle bot added to chat"""
    if not update.user:
        return

    user_name = update.user.full_name
    chat_id = update.chat_id

    logger.info(f"➕ Bot added to chat {chat_id} by {user_name}")

    greeting = f"👋 Hello everyone! Thanks for adding me, {user_name}!\n\nSend /help to see what I can do."
    bot.send_message(chat_id=chat_id, text=greeting)


@dp.update(UpdateType.BOT_REMOVED)
async def bot_removed_from_chat(update: Update):
    """Handle bot removed from chat"""
    if not update.user:
        return

    user_name = update.user.full_name
    chat_id = update.chat_id

    logger.info(f"➖ Bot removed from chat {chat_id} by {user_name}")


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
