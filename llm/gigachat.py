"""
LLM module for GigaChat integration with session management and LightRAG support
"""

import logging
from typing import Dict, List, Optional

from gigachat import GigaChat
from gigachat.models import Chat, Messages

logger = logging.getLogger(__name__)


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
        try:
            # Extract parameters
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 2000)

            # Prepare messages
            messages = [Messages(role="user", content=prompt)]

            # Create a short-lived client for this call to avoid storing
            # unpicklable objects on the adapter instance.
            client = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model,
                verify_ssl_certs=False,
            )

            # Call GigaChat API
            response = client.chat(
                Chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )

            if response and response.choices:
                return response.choices[0].message.content

            logger.warning("Empty response from GigaChat")
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
        try:
            if not texts:
                return []

            # Create a short-lived client for this call and request embeddings
            client = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                verify_ssl_certs=False,
            )

            # GigaChat embeddings API
            response = client.embeddings(texts, model=self.model)

            if response and response.data:
                # Extract embeddings from response
                embeddings = [item.embedding for item in response.data]
                return embeddings

            logger.warning("Empty embeddings response from GigaChat")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dim for _ in texts]

        except Exception as e:
            logger.error(f"Error in GigaChatEmbedding: {e}", exc_info=True)
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dim for _ in texts]
