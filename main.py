#!/usr/bin/env python3
"""
Max Bot with GigaChat integration
Main entry point for the bot
"""

import asyncio
import logging

from dotenv import load_dotenv

from bot.main import create_bot

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    try:
        bot = create_bot()
        logger.info("Starting bot with GigaChat integration...")

        await bot.start()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
