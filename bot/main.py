"""
Main bot module with GigaChat integration
"""

import logging
import os

from llm import GigaChatClient
from maxbot import Bot, Dispatcher, F
from maxbot.types import Callback, Message, Update, UpdateType

logger = logging.getLogger(__name__)


class MaxBotWithGigaChat:
    """Max Bot with GigaChat LLM integration"""

    def __init__(
        self,
        bot_token: str,
        gigachat_credentials: str,
        gigachat_scope: str = "GIGACHAT_API_PERS",
        gigachat_model: str = "GigaChat",
    ):
        """
        Initialize bot with GigaChat.

        Args:
            bot_token: Max Bot token
            gigachat_credentials: GigaChat API key
            gigachat_scope: GigaChat scope
            gigachat_model: GigaChat model name
        """
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()

        # Initialize GigaChat client
        self.llm = GigaChatClient(
            credentials=gigachat_credentials,
            scope=gigachat_scope,
            model=gigachat_model,
            max_history=10,
        )

        # System prompt for the bot
        self.system_prompt = """Ты — дружелюбный ассистент в Max Messenger.
Отвечай кратко и по делу. Будь вежливым и помогай пользователям."""

        # Register handlers
        self._register_handlers()

        logger.info("Bot initialized with GigaChat integration")

    def _register_handlers(self):
        """Register all message handlers"""

        @self.dp.startup()
        async def on_startup():
            """Called when bot starts"""
            logger.info("🚀 Bot with GigaChat is starting up...")

        @self.dp.shutdown()
        async def on_shutdown():
            """Called when bot stops"""
            logger.info("🛑 Bot with GigaChat is shutting down...")

        @self.dp.message(commands=["start", "help"])
        async def command_start(message: Message):
            """Handle /start and /help commands"""
            user_name = message.from_user.full_name if message.from_user else "Unknown"
            logger.info(f"Start command from {user_name}")

            welcome_text = f"""👋 Привет, {user_name}!

Я бот на базе GigaChat. Могу отвечать на твои вопросы и поддерживать беседу.

Доступные команды:
/start, /help - Показать это сообщение
/clear - Очистить историю диалога
/info - Показать информацию о сеансе

Просто напиши мне что-нибудь, и я отвечу! 💬"""

            if message.chat_id:
                self.bot.send_message(chat_id=message.chat_id, text=welcome_text)
            elif message.user_id:
                self.bot.send_message(user_id=message.user_id, text=welcome_text)

        @self.dp.message(commands="clear")
        async def command_clear(message: Message):
            """Clear chat history"""
            if not message.from_user:
                return

            session_id = self._get_session_id(message)
            self.llm.clear_session(session_id)

            reply = "✅ История диалога очищена!"

            if message.chat_id:
                self.bot.send_message(chat_id=message.chat_id, text=reply)
            elif message.user_id:
                self.bot.send_message(user_id=message.user_id, text=reply)

        @self.dp.message(commands="info")
        async def command_info(message: Message):
            """Show session info"""
            if not message.from_user:
                return

            session_id = self._get_session_id(message)
            history = self.llm.get_session_history(session_id)

            user = message.from_user
            info_text = f"""ℹ️ Информация о сеансе:

👤 Пользователь: {user.full_name}
🆔 ID: {user.user_id}
💬 Сообщений в истории: {len(history)}
🔑 ID сеанса: {session_id}

Всего активных сеансов: {self.llm.get_session_count()}"""

            if message.chat_id:
                self.bot.send_message(chat_id=message.chat_id, text=info_text)
            elif message.user_id:
                self.bot.send_message(user_id=message.user_id, text=info_text)

        @self.dp.message(F.text())
        async def handle_text_message(message: Message):
            """Handle text messages with GigaChat"""
            if not message.from_user:
                return

            user_text = message.text or ""
            if not user_text:
                return

            chat_id = message.chat_id
            user_id = message.user_id
            session_id = self._get_session_id(message)

            user_name = (
                message.from_user.username or message.from_user.first_name or "Аноним"
            )

            log_msg = f"Message from {user_name} (session: {session_id}): {user_text}"
            logger.info(log_msg)

            # Send typing indicator
            if chat_id:
                self.bot.send_chat_action(chat_id, "typing_on")

            # Get response from GigaChat
            response = await self.llm.chat_async(
                message=user_text,
                session_id=session_id,
                system_prompt=self.system_prompt,
            )

            if response:
                logger.info(f"GigaChat response: {response[:100]}...")

                if chat_id:
                    self.bot.send_message(chat_id=chat_id, text=response)
                elif user_id:
                    self.bot.send_message(user_id=user_id, text=response)
            else:
                error_msg = (
                    "😔 Извините, произошла ошибка при обработке вашего запроса."
                )
                if chat_id:
                    self.bot.send_message(chat_id=chat_id, text=error_msg)
                elif user_id:
                    self.bot.send_message(user_id=user_id, text=error_msg)

        @self.dp.callback_query()
        async def handle_callback(callback: Callback):
            """Handle button callbacks"""
            user_name = callback.user.full_name
            payload = callback.payload or "no payload"

            logger.info(f"🔘 Callback from {user_name}: {payload}")

            self.bot.answer_callback(
                callback_id=callback.callback_id,
                notification=f"Кнопка нажата: {payload}",
            )

        @self.dp.update(UpdateType.BOT_STARTED)
        async def bot_started(update: Update):
            """Handle bot started by user"""
            if not update.user:
                return

            user_name = update.user.full_name
            logger.info(f"🚀 Bot started by {user_name}")

            welcome_text = f"""👋 Добро пожаловать, {user_name}!

Спасибо, что запустили бота. Я работаю на базе GigaChat и готов помочь вам.

Отправьте /help чтобы увидеть доступные команды."""

            if update.user.user_id:
                self.bot.send_message(user_id=update.user.user_id, text=welcome_text)

        @self.dp.update(UpdateType.BOT_STOPPED)
        async def bot_stopped(update: Update):
            """Handle bot stopped by user"""
            if not update.user:
                return

            user_name = update.user.full_name
            logger.info(f"🛑 Bot stopped by {user_name}")

        @self.dp.update(UpdateType.BOT_ADDED)
        async def bot_added_to_chat(update: Update):
            """Handle bot added to chat"""
            if not update.user:
                return

            user_name = update.user.full_name
            chat_id = update.chat_id

            logger.info(f"➕ Bot added to chat {chat_id} by {user_name}")

            greeting = f"""👋 Привет всем! Спасибо, что добавили меня, {user_name}!

Я работаю на базе GigaChat и могу отвечать на ваши вопросы.
Отправьте /help чтобы узнать, что я умею."""

            self.bot.send_message(chat_id=chat_id, text=greeting)

        @self.dp.update(UpdateType.BOT_REMOVED)
        async def bot_removed_from_chat(update: Update):
            """Handle bot removed from chat"""
            if not update.user:
                return

            user_name = update.user.full_name
            chat_id = update.chat_id

            logger.info(f"➖ Bot removed from chat {chat_id} by {user_name}")

    def _get_session_id(self, message: Message) -> str:
        """
        Get session ID for message.

        For group chats: chat_id:user_id
        For private chats: chat_id

        Args:
            message: Message object

        Returns:
            Session ID string
        """
        chat_id = str(message.chat_id) if message.chat_id else ""
        user_id = str(message.user_id) if message.user_id else ""

        # In group chats, separate sessions per user
        if message.recipient.chat_type in ["chat", "group", "supergroup"]:
            return f"{chat_id}:{user_id}"

        # In private chats, one session per chat
        return chat_id

    async def start(self):
        """Start the bot"""
        await self.dp.start_polling(self.bot)


def create_bot() -> MaxBotWithGigaChat:
    """Create and configure bot instance"""
    bot_token = os.getenv("BOT_TOKEN")
    gigachat_credentials = os.getenv("GIGACHAT_CREDENTIALS")
    gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    gigachat_model = os.getenv("GIGACHAT_MODEL", "GigaChat")

    if not bot_token:
        raise ValueError("BOT_TOKEN not found in environment variables")

    if not gigachat_credentials:
        raise ValueError("GIGACHAT_CREDENTIALS not found in environment variables")

    return MaxBotWithGigaChat(
        bot_token=bot_token,
        gigachat_credentials=gigachat_credentials,
        gigachat_scope=gigachat_scope,
        gigachat_model=gigachat_model,
    )
