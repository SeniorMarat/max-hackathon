"""
LLM module for GigaChat integration with session management and LightRAG support
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional

from gigachat import GigaChat
from gigachat.exceptions import ResponseError
from gigachat.models import Chat, Messages

logger = logging.getLogger(__name__)


# Global rate limiter for all GigaChat API calls
class RateLimiter:
    """Simple rate limiter to prevent API overload"""

    def __init__(self, calls_per_minute: int = 20):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Wait until we can make another API call"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            self.last_call = time.time()


# Get rate limit from environment, default to 20 calls per minute
_calls_per_minute = int(os.getenv("GIGACHAT_CALLS_PER_MINUTE", "20"))
_rate_limiter = RateLimiter(calls_per_minute=_calls_per_minute)
logger.info(f"GigaChat rate limiter initialized: {_calls_per_minute} calls/min")


async def retry_with_backoff(
    func,
    max_retries: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    backoff_factor: float = 2.0,
):
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (from env or default 5)
        initial_delay: Initial delay in seconds (from env or default 1.0)
        max_delay: Maximum delay in seconds (from env or default 60.0)
        backoff_factor: Multiplier for delay after each retry

    Returns:
        Result from func

    Raises:
        Last exception if all retries fail
    """
    # Get defaults from environment variables
    if max_retries is None:
        max_retries = int(os.getenv("GIGACHAT_MAX_RETRIES", "5"))
    if initial_delay is None:
        initial_delay = float(os.getenv("GIGACHAT_INITIAL_RETRY_DELAY", "1.0"))
    if max_delay is None:
        max_delay = float(os.getenv("GIGACHAT_MAX_RETRY_DELAY", "60.0"))

    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Apply rate limiting before each attempt
            await _rate_limiter.acquire()
            return await func()
        except ResponseError as e:
            last_exception = e
            # Check if it's a rate limit error (429)
            if e.status_code == 429:
                if attempt < max_retries:
                    wait_time = min(delay, max_delay)
                    logger.warning(
                        f"Rate limit hit (429). Retry {attempt + 1}/{max_retries} "
                        f"after {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
                    delay *= backoff_factor
                else:
                    logger.error(
                        f"Rate limit exceeded after {max_retries} retries. "
                        "Consider reducing concurrent workers or request rate."
                    )
                    raise
            else:
                # Not a rate limit error, don't retry
                raise
        except Exception as e:
            last_exception = e
            # For other errors, retry with shorter backoff
            if attempt < max_retries:
                wait_time = min(delay / 2, max_delay / 2)
                logger.warning(
                    f"Error: {type(e).__name__}. "
                    f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
                delay *= backoff_factor
            else:
                raise

    # Should not reach here, but just in case
    if last_exception:
        raise last_exception


class GigaChatClient:
    """GigaChat client with session management"""

    def __init__(
        self,
        credentials: str,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat",
        max_history: int = 10,
    ):
        """
        Initialize GigaChat client.

        Args:
            credentials: GigaChat authorization key
            scope: API scope (GIGACHAT_API_PERS or GIGACHAT_API_CORP)
            model: Model name (GigaChat, GigaChat-Pro, etc.)
            max_history: Maximum messages to keep in session history
        """
        self.client = GigaChat(
            credentials=credentials,
            scope=scope,
            model=model,
            verify_ssl_certs=False,  # For development
        )
        self.model = model
        self.max_history = max_history

        # Session storage: session_id -> list of messages
        self.sessions: Dict[str, List[Dict[str, str]]] = {}

        logger.info(f"GigaChat client initialized with model: {model}")

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get chat history for session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def add_to_history(self, session_id: str, role: str, content: str) -> None:
        """
        Add message to session history.

        Args:
            session_id: Session identifier
            role: Message role (user/assistant/system)
            content: Message content
        """
        history = self.get_session_history(session_id)
        history.append({"role": role, "content": content})

        # Keep only last N messages to avoid context overflow
        if len(history) > self.max_history:
            # Keep first message (system prompt if exists) and last N-1
            if history[0]["role"] == "system":
                keep_count = self.max_history - 1
                self.sessions[session_id] = [history[0]] + history[-keep_count:]
            else:
                self.sessions[session_id] = history[-self.max_history :]

    def clear_session(self, session_id: str) -> None:
        """
        Clear session history.

        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")

    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send message to GigaChat and get response.

        Args:
            message: User message
            session_id: Session ID for context (optional)
            system_prompt: System prompt for first message (optional)

        Returns:
            Assistant response or None on error
        """
        try:
            # Use session_id for context, or create one-off chat
            if session_id:
                history = self.get_session_history(session_id)

                # Add system prompt if it's the first message
                if not history and system_prompt:
                    self.add_to_history(session_id, "system", system_prompt)
                    history = self.get_session_history(session_id)

                # Add user message
                self.add_to_history(session_id, "user", message)
                history = self.get_session_history(session_id)

                # Prepare messages for API
                messages = [
                    Messages(role=msg["role"], content=msg["content"])
                    for msg in history
                ]
            else:
                # One-off chat without context
                messages = [Messages(role="user", content=message)]
                if system_prompt:
                    messages.insert(0, Messages(role="system", content=system_prompt))

            # Call GigaChat API
            response = self.client.chat(Chat(messages=messages))

            # Extract response text
            if response and response.choices:
                assistant_message = response.choices[0].message.content

                # Add to history if using sessions
                if session_id:
                    self.add_to_history(session_id, "assistant", assistant_message)

                return assistant_message

            return None

        except Exception as e:
            logger.error(f"Error calling GigaChat: {e}", exc_info=True)
            return None

    async def chat_async(
        self,
        message: str,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Async version of chat (currently wraps sync version).

        Args:
            message: User message
            session_id: Session ID for context (optional)
            system_prompt: System prompt (optional)

        Returns:
            Assistant response or None on error
        """
        # TODO: Use async version when available
        return self.chat(message, session_id, system_prompt)

    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)

    def get_all_session_ids(self) -> List[str]:
        """Get all active session IDs"""
        return list(self.sessions.keys())


# ============================================================================
#                    LightRAG Adapters for GigaChat
# ============================================================================


class GigaChatLLM:
    """
    LightRAG-compatible LLM adapter for GigaChat.
    Implements the interface expected by LightRAG for text generation.
    """

    def __init__(
        self,
        credentials: str,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat",
    ):
        """
        Initialize GigaChat LLM adapter for LightRAG.

        Args:
            credentials: GigaChat authorization key
            scope: API scope (GIGACHAT_API_PERS or GIGACHAT_API_CORP)
            model: Model name (GigaChat, GigaChat-Pro, etc.)
        """
        # Do not keep the GigaChat client instance as an attribute because
        # it may contain threading locks that are not picklable. Create a
        # client on each call instead to keep the adapter stateless and
        # safe for multiprocessing/pickling inside LightRAG.
        self.credentials = credentials
        self.scope = scope
        self.model = model
        logger.info(f"GigaChatLLM initialized with model: {model}")

    async def __call__(self, prompt: str, **kwargs) -> str:
        """
        Generate text completion for the given prompt.
        This is the main interface method used by LightRAG.
        Must be async for LightRAG compatibility.

        Args:
            prompt: Input prompt text
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """

        async def _make_request():
            # Extract parameters
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 2000)
            system_prompt = kwargs.get("system_prompt")

            # Prepare messages
            messages = []

            # Add system prompt if provided (contains the actual text for LightRAG)
            if system_prompt:
                messages.append(Messages(role="system", content=system_prompt))

            # Add user prompt (contains the task instructions)
            messages.append(Messages(role="user", content=prompt))

            # Create a short-lived client for this call to avoid storing
            # unpicklable objects on the adapter instance.
            client = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model,
                verify_ssl_certs=False,
            )

            logger.error(messages)

            # Call GigaChat API in thread pool (GigaChat SDK is synchronous)
            response = await asyncio.to_thread(
                client.chat,
                Chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
            )

            if response and response.choices:
                return response.choices[0].message.content

            logger.warning("Empty response from GigaChat")
            return ""

        try:
            # Use retry with exponential backoff
            return await retry_with_backoff(_make_request, max_retries=5)

        except ResponseError as e:
            if e.status_code == 429:
                logger.error(
                    "Rate limit exceeded even after retries. Returning empty response."
                )
                return ""
            logger.error(f"GigaChat API error ({e.status_code}): {e}")
            return ""
        except Exception as e:
            logger.error(f"Error in GigaChatLLM: {e}", exc_info=True)
            return ""


class GigaChatEmbedding:
    """
    LightRAG-compatible Embedding adapter for GigaChat.
    Implements the interface expected by LightRAG for text embeddings.
    """

    def __init__(
        self,
        credentials: str,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "Embeddings",
        embedding_dim: int = 1024,
    ):
        """
        Initialize GigaChat Embedding adapter for LightRAG.

        Args:
            credentials: GigaChat authorization key
            scope: API scope
            model: Embedding model name (default: "Embeddings")
            embedding_dim: Dimension of embedding vectors (GigaChat uses 1024)
        """
        # Keep only connection parameters to avoid holding an actual
        # GigaChat client instance (which can include locks). The client
        # will be created on demand inside __call__.
        self.credentials = credentials
        self.scope = scope
        self.model = model
        self.embedding_dim = embedding_dim
        logger.info(f"GigaChatEmbedding initialized with model: {model}")

    async def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        This is the main interface method used by LightRAG.
        Must be async for LightRAG compatibility.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (each is a list of floats)
        """

        async def _make_request():
            if not texts:
                return []

            # Create a short-lived client for this call and request embeddings
            client = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                verify_ssl_certs=False,
            )

            # GigaChat embeddings API in thread pool (GigaChat SDK is synchronous)
            response = await asyncio.to_thread(
                client.embeddings, texts, model=self.model
            )

            if response and response.data:
                # Extract embeddings from response
                embeddings = [item.embedding for item in response.data]
                return embeddings

            logger.warning("Empty embeddings response from GigaChat")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dim for _ in texts]

        try:
            # Use retry with exponential backoff
            return await retry_with_backoff(_make_request, max_retries=5)

        except ResponseError as e:
            if e.status_code == 429:
                logger.error(
                    "Rate limit exceeded even after retries. Returning zero vectors."
                )
                return [[0.0] * self.embedding_dim for _ in texts]
            logger.error(f"GigaChat API error ({e.status_code}): {e}")
            return [[0.0] * self.embedding_dim for _ in texts]
        except Exception as e:
            logger.error(f"Error in GigaChatEmbedding: {e}", exc_info=True)
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dim for _ in texts]
