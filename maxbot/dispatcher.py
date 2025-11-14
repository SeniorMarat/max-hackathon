"""
Dispatcher with decorator-based handlers (aiogram-style)
"""

import logging
import time
from typing import Any, Awaitable, Callable, List, Optional, Union

from .bot import Bot
from .filters import CallbackDataFilter, CommandFilter, Filter, TextFilter
from .types import Callback, Message, Update, UpdateType

logger = logging.getLogger(__name__)


class Handler:
    """Handler for updates"""

    def __init__(
        self,
        callback: Callable[[Any], Awaitable[Any]],
        filters: Optional[List[Filter]] = None,
        update_types: Optional[List[UpdateType]] = None,
    ):
        self.callback = callback
        self.filters = filters or []
        self.update_types = update_types or []

    def check(self, update: Update) -> bool:
        """Check if handler matches the update"""
        # Check update type
        if self.update_types and update.update_type not in self.update_types:
            return False

        # Check filters
        for filter_obj in self.filters:
            if not filter_obj.check(update):
                return False

        return True

    async def handle(self, update: Update, bot: Bot) -> Any:
        """Handle the update"""
        # Determine what to pass based on update type
        if update.update_type in [
            UpdateType.MESSAGE_CREATED,
            UpdateType.MESSAGE_EDITED,
        ]:
            return await self.callback(update.message)
        elif update.update_type == UpdateType.MESSAGE_CALLBACK:
            return await self.callback(update.callback)
        else:
            return await self.callback(update)


class Dispatcher:
    """
    Dispatcher for handling updates (aiogram-style).

    Example:
        dp = Dispatcher()

        @dp.message(F.command("start"))
        async def start_handler(message: Message):
            print(f"Start command from {message.from_user.full_name}")

        @dp.message(F.text())
        async def text_handler(message: Message):
            print(f"Text: {message.text}")
    """

    def __init__(self):
        self.handlers: List[Handler] = []
        self.bot: Optional[Bot] = None
        self.marker: Optional[int] = None
        self.running = False

    def message(
        self,
        *filters: Union[Filter, Callable],
        commands: Optional[Union[str, List[str]]] = None,
        text: Optional[Union[str, List[str]]] = None,
    ) -> Callable:
        """
        Decorator for message handlers.

        Args:
            *filters: Filters to apply
            commands: Command filter (shorthand)
            text: Text filter (shorthand)

        Example:
            @dp.message(F.command("start"))
            async def start(message: Message):
                pass

            @dp.message(commands=["start", "help"])
            async def commands(message: Message):
                pass

            @dp.message(text="Hello")
            async def hello(message: Message):
                pass
        """

        def decorator(func: Callable[[Message], Awaitable[Any]]) -> Callable:
            filter_list = list(filters) if filters else []

            # Add shorthand filters
            if commands:
                filter_list.append(CommandFilter(commands))
            if text:
                filter_list.append(TextFilter(text))

            handler = Handler(
                callback=func,
                filters=filter_list,
                update_types=[UpdateType.MESSAGE_CREATED, UpdateType.MESSAGE_EDITED],
            )
            self.handlers.append(handler)
            return func

        return decorator

    def callback_query(
        self,
        *filters: Union[Filter, Callable],
        data: Optional[Union[str, List[str]]] = None,
    ) -> Callable:
        """
        Decorator for callback query handlers.

        Args:
            *filters: Filters to apply
            data: Callback data filter (shorthand)

        Example:
            @dp.callback_query(F.callback_data("button_1"))
            async def button_handler(callback: Callback):
                pass

            @dp.callback_query(data="button_1")
            async def button_handler(callback: Callback):
                pass
        """

        def decorator(func: Callable[[Callback], Awaitable[Any]]) -> Callable:
            filter_list = list(filters) if filters else []

            # Add shorthand filter
            if data:
                filter_list.append(CallbackDataFilter(data))

            handler = Handler(
                callback=func,
                filters=filter_list,
                update_types=[UpdateType.MESSAGE_CALLBACK],
            )
            self.handlers.append(handler)
            return func

        return decorator

    def startup(self) -> Callable:
        """
        Decorator for startup handler.

        Example:
            @dp.startup()
            async def on_startup():
                print("Bot started!")
        """

        def decorator(func: Callable[[], Awaitable[Any]]) -> Callable:
            self._startup_handler = func
            return func

        return decorator

    def shutdown(self) -> Callable:
        """
        Decorator for shutdown handler.

        Example:
            @dp.shutdown()
            async def on_shutdown():
                print("Bot stopped!")
        """

        def decorator(func: Callable[[], Awaitable[Any]]) -> Callable:
            self._shutdown_handler = func
            return func

        return decorator

    def update(self, *update_types: UpdateType) -> Callable:
        """
        Decorator for custom update handlers.

        Args:
            *update_types: Update types to handle

        Example:
            @dp.update(UpdateType.BOT_STARTED)
            async def bot_started(update: Update):
                print(f"Bot started by {update.user.full_name}")
        """

        def decorator(func: Callable[[Update], Awaitable[Any]]) -> Callable:
            handler = Handler(
                callback=func,
                filters=[],
                update_types=list(update_types) if update_types else [],
            )
            self.handlers.append(handler)
            return func

        return decorator

    async def process_update(self, update: Update) -> None:
        """Process a single update"""
        logger.debug(f"Processing update: {update.update_type}")

        for handler in self.handlers:
            if handler.check(update):
                try:
                    await handler.handle(update, self.bot)
                    break  # Stop after first matching handler
                except Exception as e:
                    logger.error(f"Error in handler: {e}", exc_info=True)

    async def start_polling(
        self,
        bot: Bot,
        limit: int = 100,
        timeout: int = 30,
        allowed_updates: Optional[List[str]] = None,
    ) -> None:
        """
        Start long polling.

        Args:
            bot: Bot instance
            limit: Maximum updates per request
            timeout: Long polling timeout
            allowed_updates: List of update types to receive
        """
        self.bot = bot

        # Get bot info
        bot_info = bot.get_me()
        if not bot_info:
            logger.error("Failed to get bot information")
            return

        logger.info(f"Bot started: {bot_info.first_name} (@{bot_info.username})")
        logger.info(f"Bot ID: {bot_info.user_id}")

        # Call startup handler
        if hasattr(self, "_startup_handler"):
            try:
                await self._startup_handler()
            except Exception as e:
                logger.error(f"Error in startup handler: {e}", exc_info=True)

        self.running = True
        logger.info("Starting long polling...")

        try:
            while self.running:
                await self._poll_updates(limit, timeout, allowed_updates)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.running = False

            # Call shutdown handler
            if hasattr(self, "_shutdown_handler"):
                try:
                    await self._shutdown_handler()
                except Exception as e:
                    logger.error(f"Error in shutdown handler: {e}", exc_info=True)

    async def _poll_updates(
        self, limit: int, timeout: int, allowed_updates: Optional[List[str]]
    ) -> None:
        """Poll for updates"""
        result = self.bot.get_updates(
            marker=self.marker, limit=limit, timeout=timeout, types=allowed_updates
        )

        if not result:
            # Error occurred, wait before retrying
            time.sleep(5)
            return

        updates = result.get("updates", [])
        new_marker = result.get("marker")

        # Process updates
        for update_data in updates:
            try:
                update = Update.from_dict(update_data)
                await self.process_update(update)
            except Exception as e:
                logger.error(f"Error processing update: {e}", exc_info=True)

        # Update marker
        if new_marker is not None:
            self.marker = new_marker

    def stop(self) -> None:
        """Stop polling"""
        self.running = False
