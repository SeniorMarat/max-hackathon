#!/usr/bin/env python3
"""
Max Bot with GigaChat integration
Main entry point for the bot
"""

import asyncio
import logging

from dotenv import load_dotenv

from bot.main import create_bot

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    try:
        # Create bot with GigaChat integration
        bot = create_bot()
        logger.info("Starting bot with GigaChat integration...")

        # Start polling
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
