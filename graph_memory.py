import asyncio
import logging
import os
from typing import AsyncIterator, Dict, List, Literal, Optional

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


GRAPH_QUERY_MODES: frozenset = frozenset(
    {"naive", "local", "global", "hybrid", "mix", "bypass"}
)


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
        model_name: str = "GigaChat",
        embedding_model_name: str = "Embeddings",
    ) -> None:
        """
        Инициализация GraphMemory с GigaChat.

        Args:
            credentials: GigaChat API ключ (если None, берется из .env)
            scope: GigaChat scope (GIGACHAT_API_PERS или GIGACHAT_API_CORP)
            model_name: Модель GigaChat для генерации текста
            embedding_model_name: Модель GigaChat для эмбеддингов
        """
        # Получаем credentials из .env если не передан
        self.credentials: Optional[str] = credentials or os.getenv(
            "GIGACHAT_CREDENTIALS"
        )
        if not self.credentials:
            raise ValueError(
                "GIGACHAT_CREDENTIALS not found in environment or parameters"
            )

        self.scope: str = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model_name: str = model_name or os.getenv("GIGACHAT_MODEL", "GigaChat")
        self.embedding_model_name = embedding_model_name
        self._graphs: Dict[str, LightRAG] = {}
        self._loop = _get_or_create_event_loop()

        # Базовая директория для хранения графов.
        self.workspace_path = os.getenv("LIGHRAG_WORKSPACE_BASE", "./data/lightrag")
        os.makedirs(self.workspace_path, exist_ok=True)

        logger.info(
            f"GraphMemory initialized with GigaChat model: {self.model_name}, "
            f"base workspace: {self.workspace_path}"
        )

    def _get_workspace_path(self, graph_id: str) -> str:
        """
        Возвращает путь к workspace конкретного графа.

        Args:
            graph_id: Идентификатор графа

        Returns:
            Полный путь к директории графа
        """
        path: str = os.path.join(self.workspace_path, graph_id)
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

        # Создаем новый инстанс LightRAG.
        workspace_path: str = self._get_workspace_path(graph_id)

        try:
            if not self.credentials:
                raise ValueError("GIGACHAT_CREDENTIALS not found in environment")

            llm_adapter: GigaChatLLM = GigaChatLLM(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model_name,
            )

            embedding_adapter: GigaChatEmbedding = GigaChatEmbedding(
                credentials=self.credentials,
                scope=self.scope,
                model=self.embedding_model_name,
            )

            @wrap_embedding_func_with_attrs(
                embedding_dim=embedding_adapter.embedding_dim
            )
            async def embedding_func(texts: List[str]) -> List[List[float]]:
                return await embedding_adapter(texts)

            async def llm_model_func(prompt: str, **kwargs) -> str:
                return await llm_adapter(prompt, **kwargs)

            rag: LightRAG = LightRAG(
                working_dir=workspace_path,
                llm_model_func=llm_model_func,
                embedding_func=embedding_func,
            )

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
            # LightRAG.insert is async, используем единый event loop.
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
        mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = "hybrid",
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
            if mode not in GRAPH_QUERY_MODES:
                raise ValueError(f"Invalid mode: {mode}")

            rag: LightRAG = self._get_or_create_graph(graph_id)

            result: str | AsyncIterator[str] = self._loop.run_until_complete(
                rag.aquery(question, param=QueryParam(mode=mode))
            )

            logger.info(f"Query to graph {graph_id} in {mode} mode")

            return result  # type: ignore

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
            if graph_id in self._graphs:
                del self._graphs[graph_id]

            workspace_path: str = self._get_workspace_path(graph_id)
            if os.path.exists(workspace_path):
                import shutil

                shutil.rmtree(workspace_path)
                logger.info(f"Deleted graph {graph_id} from disk")

            return True

        except Exception as e:
            logger.error(f"Error deleting graph {graph_id}: {e}")
            return False

    def list_graphs(self) -> List[str]:
        """
        Получить список всех существующих графов.

        Returns:
            Список идентификаторов графов
        """
        try:
            if not os.path.exists(self.workspace_path):
                return []

            return [
                d
                for d in os.listdir(self.workspace_path)
                if os.path.isdir(os.path.join(self.workspace_path, d))
            ]

        except Exception as e:
            logger.error(f"Error listing graphs: {e}")
            return []
