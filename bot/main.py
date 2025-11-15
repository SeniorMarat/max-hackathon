"""Основной модуль бота с интеграцией GigaChat"""

import logging
import os

from llm import GigaChatClient
from maxbot_api import Bot, Dispatcher, F
from maxbot_api.types import Message

logger = logging.getLogger(__name__)


class MaxBotAI:
    """Max Bot с интеграцией GigaChat LLM"""

    def __init__(
        self,
        bot_token: str,
        gigachat_credentials: str,
        gigachat_scope: str = "GIGACHAT_API_PERS",
        gigachat_model: str = "GigaChat",
    ):
        """
        Инициализация бота с GigaChat.

        Args:
            bot_token: Max Bot token
            gigachat_credentials: GigaChat API key
            gigachat_scope: GigaChat scope
            gigachat_model: GigaChat model name
        """
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()

        self.llm = GigaChatClient(
            credentials=gigachat_credentials,
            scope=gigachat_scope,
            model=gigachat_model,
            max_history=10,
        )

        # Системный промпт.
        self.system_prompt = """
            Ты — ИИ-ассистент для абитуриентов и 
            студентов Новосибирского государственного университета (НГУ).
            Отвечай кратко, по делу и только на вопросы, касающиеся НГУ:
            поступление, факультеты, общежития, мероприятия, внеучебная
            деятельность и инфраструктура.
            Если вопрос не относится к НГУ,
            вежливо откажись и предложи задать вопрос по теме НГУ.
            Опирайся только на то, что тебе будет передано в качестве
            справочной информации.
            Не придумывай информацию сам.
        """

        self._register_handlers()

        logger.info("Bot initialized with GigaChat integration")

    def _register_handlers(self):
        """Регистрация всех обработчиков сообщений"""

        @self.dp.message(F.text())
        async def handle_text_message(message: Message):
            """Обработка текстовых сообщений с помощью GigaChat"""
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

            # Индикатор отправки сообщения.
            if chat_id:
                self.bot.send_chat_action(chat_id, "typing_on")

            # Получение ответа от LLM.
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
                error_msg = "Извините, произошла ошибка при обработке вашего запроса"
                if chat_id:
                    self.bot.send_message(chat_id=chat_id, text=error_msg)
                elif user_id:
                    self.bot.send_message(user_id=user_id, text=error_msg)

    def _get_session_id(self, message: Message) -> str:
        """
        Получение идентификатора сессии для сообщения.

        For group chats: chat_id:user_id
        For private chats: chat_id

        Args:
            message: Message object

        Returns:
            Session ID string
        """
        chat_id = str(message.chat_id) if message.chat_id else ""
        user_id = str(message.user_id) if message.user_id else ""

        # В групповых чатах создаются отдельные сессии для каждого пользователя.
        if message.recipient.chat_type in ["chat", "group", "supergroup"]:
            return f"{chat_id}:{user_id}"

        # В личных чатах используется одна сессия на чат.
        return chat_id

    async def start(self):
        """Запуск бота"""
        await self.dp.start_polling(self.bot)


def create_bot() -> MaxBotAI:
    """Создание и настройка экземпляра бота"""
    bot_token = os.getenv("BOT_TOKEN")
    gigachat_credentials = os.getenv("GIGACHAT_CREDENTIALS")
    gigachat_scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    gigachat_model = os.getenv("GIGACHAT_MODEL", "GigaChat")

    if not bot_token:
        raise ValueError("BOT_TOKEN not found in environment variables")

    if not gigachat_credentials:
        raise ValueError("GIGACHAT_CREDENTIALS not found in environment variables")

    return MaxBotAI(
        bot_token=bot_token,
        gigachat_credentials=gigachat_credentials,
        gigachat_scope=gigachat_scope,
        gigachat_model=gigachat_model,
    )
