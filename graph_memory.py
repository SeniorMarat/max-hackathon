import asyncio
import logging
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import wrap_embedding_func_with_attrs

from llm.gigachat import GigaChatEmbedding, GigaChatLLM

load_dotenv()

logger = logging.getLogger(__name__)


def _get_or_create_event_loop():
    """Получить или создать event loop для текущего потока"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


class GraphMemory:
    """
    Менеджер для нескольких локальных графов LightRAG.
    Использует GigaChat API для LLM и embeddings.

    Каждый граф — отдельная инстанция LightRAG с отдельным workspace (папкой).
    """

    def __init__(
        self,
        credentials: Optional[str] = None,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat",
        embedding_model: str = "Embeddings",
    ):
        """
        Инициализация GraphMemory с GigaChat.

        Args:
            credentials: GigaChat API ключ (если None, берется из .env)
            scope: GigaChat scope (GIGACHAT_API_PERS или GIGACHAT_API_CORP)
            model: Модель GigaChat для генерации текста
            embedding_model: Модель GigaChat для эмбеддингов
        """
        # Получаем credentials из .env если не передан
        self.credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
        if not self.credentials:
            raise ValueError(
                "GIGACHAT_CREDENTIALS not found in environment or parameters"
            )

        self.scope = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model = model or os.getenv("GIGACHAT_MODEL", "GigaChat")
        self.embedding_model = embedding_model

        # Базовая директория для хранения графов
        self.base_workspace = os.getenv("LIGHRAG_WORKSPACE_BASE", "./data/lightrag")
        os.makedirs(self.base_workspace, exist_ok=True)

        # Кэш инстансов LightRAG для каждого graph_id
        self._graphs: Dict[str, LightRAG] = {}

        # Единый event loop для всех async операций
        self._loop = _get_or_create_event_loop()

        logger.info(
            f"GraphMemory initialized with GigaChat model: {self.model}, "
            f"base workspace: {self.base_workspace}"
        )

    def _get_workspace_path(self, graph_id: str) -> str:
        """
        Возвращает путь к workspace конкретного графа.

        Args:
            graph_id: Идентификатор графа

        Returns:
            Полный путь к директории графа
        """
        path = os.path.join(self.base_workspace, graph_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _get_or_create_graph(self, graph_id: str) -> LightRAG:
        """
        Получить или создать инстанс LightRAG для указанного графа.

        Args:
            graph_id: Идентификатор графа

        Returns:
            Инстанс LightRAG
        """
        if graph_id in self._graphs:
            return self._graphs[graph_id]

        # Создаем новый инстанс LightRAG
        workspace_path = self._get_workspace_path(graph_id)

        try:
            # Создаем адаптеры GigaChat
            llm_adapter = GigaChatLLM(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model,
            )

            embedding_adapter = GigaChatEmbedding(
                credentials=self.credentials,
                scope=self.scope,
                model=self.embedding_model,
            )

            # Создаем async функции для LightRAG используя правильный декоратор
            @wrap_embedding_func_with_attrs(
                embedding_dim=embedding_adapter.embedding_dim
            )
            async def embedding_func(texts):
                return await embedding_adapter(texts)

            # Для LLM функции просто создаём async обёртку
            async def llm_model_func(prompt, **kwargs):
                return await llm_adapter(prompt, **kwargs)

            # Создаем инстанс LightRAG с функциями
            rag = LightRAG(
                working_dir=workspace_path,
                llm_model_func=llm_model_func,
                embedding_func=embedding_func,
            )

            # LightRAG требует async инициализацию хранилищ и pipeline status
            # Используем единый event loop
            async def init_rag():
                await rag.initialize_storages()
                await initialize_pipeline_status()

            self._loop.run_until_complete(init_rag())

            self._graphs[graph_id] = rag
            logger.info(f"Created new LightRAG instance for graph: {graph_id}")

        except Exception as e:
            logger.error(f"Error creating LightRAG instance for {graph_id}: {e}")
            raise

        return self._graphs[graph_id]

    # ------------------------------------------------------------
    #                      PUBLIC API
    # ------------------------------------------------------------

    def save(self, graph_id: str, text: str) -> bool:
        """
        Сохранить текст в граф знаний (обновление LightRAG).

        Args:
            graph_id: Идентификатор графа
            text: Текст для добавления в граф

        Returns:
            True если успешно, False если произошла ошибка
        """
        try:
            rag = self._get_or_create_graph(graph_id)
            # LightRAG.insert is async, используем единый event loop
            self._loop.run_until_complete(rag.ainsert(text))
            logger.info(f"Inserted text into graph {graph_id}: {len(text)} chars")
            return True

        except Exception as e:
            logger.error(f"Error inserting text into graph {graph_id}: {e}")
            return False

    def query(
        self,
        graph_id: str,
        question: str,
        mode: str = "hybrid",
    ) -> str:
        """
        Сделать запрос к выбранному графу.

        Args:
            graph_id: Идентификатор графа
            question: Вопрос для поиска
            mode: Режим поиска ('naive', 'local', 'global', 'hybrid')
                - naive: простой поиск без графа
                - local: локальный поиск в графе
                - global: глобальный поиск в графе
                - hybrid: комбинированный поиск (рекомендуется)

        Returns:
            Ответ на вопрос
        """
        try:
            rag = self._get_or_create_graph(graph_id)

            # Выполняем запрос с указанным режимом через единый event loop
            result = self._loop.run_until_complete(
                rag.aquery(question, param=QueryParam(mode=mode))
            )

            logger.info(
                f"Query to graph {graph_id} in {mode} mode: "
                f"{len(result)} chars response"
            )

            return result

        except Exception as e:
            logger.error(f"Error querying graph {graph_id}: {e}")
            return f"Ошибка при выполнении запроса: {str(e)}"

    def delete_graph(self, graph_id: str) -> bool:
        """
        Удалить граф из памяти и с диска.

        Args:
            graph_id: Идентификатор графа

        Returns:
            True если успешно удален
        """
        try:
            # Удаляем из кэша
            if graph_id in self._graphs:
                del self._graphs[graph_id]

            # Удаляем директорию
            workspace_path = self._get_workspace_path(graph_id)
            if os.path.exists(workspace_path):
                import shutil

                shutil.rmtree(workspace_path)
                logger.info(f"Deleted graph {graph_id} from disk")

            return True

        except Exception as e:
            logger.error(f"Error deleting graph {graph_id}: {e}")
            return False

    def list_graphs(self) -> list:
        """
        Получить список всех существующих графов.

        Returns:
            Список идентификаторов графов
        """
        try:
            if not os.path.exists(self.base_workspace):
                return []

            return [
                d
                for d in os.listdir(self.base_workspace)
                if os.path.isdir(os.path.join(self.base_workspace, d))
            ]

        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return []
