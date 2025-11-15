import logging
import os
from typing import Dict, List, Literal, Optional

from dotenv import load_dotenv
from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import wrap_embedding_func_with_attrs

from llm.gigachat import GigaChatEmbedding, GigaChatLLM

load_dotenv()

logger = logging.getLogger(__name__)

GRAPH_QUERY_MODES: frozenset = frozenset(
    ["naive", "local", "global", "hybrid", "mix", "bypass"]
)


class GraphMemory:
    """
    Асинхронный менеджер для нескольких локальных графов LightRAG.
    Использует GigaChat API для LLM и эмбеддингов.
    """

    def __init__(
        self,
        credentials: Optional[str] = None,
        scope: str = "GIGACHAT_API_PERS",
        model_name: str = "GigaChat",
        embedding_model_name: str = "Embeddings",
    ) -> None:
        """
        Инициализация графовой памяти с GigaChat.

        Args:
            credentials: API ключ GigaChat (если None — берётся из окружения).
            scope: GigaChat scope.
            model_name: LLM модель.
            embedding_model_name: Модель эмбеддингов.
        """
        self.credentials: Optional[str] = credentials or os.getenv(
            "GIGACHAT_CREDENTIALS"
        )
        if not self.credentials:
            raise ValueError(
                "Error: GIGACHAT_CREDENTIALS environment variable is not set. "
                "Please set this variable before running the program.\n"
                "You can set it by running: "
                "export GIGACHAT_CREDENTIALS='your-credentials'"
            )

        self.scope: str = scope or os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        self.model_name: str = model_name or os.getenv("GIGACHAT_MODEL", "GigaChat-max")
        self.embedding_model_name = embedding_model_name

        self._graphs: Dict[str, LightRAG] = {}

        self.workspace_path = os.getenv("LIGHRAG_WORKSPACE_BASE", "./data/lightrag")
        os.makedirs(self.workspace_path, exist_ok=True)

        logger.info(
            f"GraphMemory initialized (async) with model: {self.model_name}, \
                workspace: {self.workspace_path}"
        )

    def _get_workspace_path(self, graph_id: str) -> str:
        """
        Получить путь к workspace графа.
        """
        path = os.path.join(self.workspace_path, graph_id)
        os.makedirs(path, exist_ok=True)
        return path

    async def _get_or_create_graph(self, graph_id: str) -> LightRAG:
        """
        Асинхронное создание/получение инстанса LightRAG.
        """
        if graph_id in self._graphs:
            return self._graphs[graph_id]

        workspace_path = self._get_workspace_path(graph_id)

        try:
            if self.credentials is None:
                raise ValueError(
                    "GIGACHAT_CREDENTIALS not found in environment or parameters"
                )
            llm_adapter = GigaChatLLM(
                credentials=self.credentials,
                scope=self.scope,
                model=self.model_name,
            )

            embedding_adapter = GigaChatEmbedding(
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
                rus_prompt = prompt.replace("English", "Russian")
                logger.error(rus_prompt)
                return await llm_adapter(rus_prompt, **kwargs)

            # Get worker counts from environment (defaults to conservative values)
            embedding_workers = int(os.getenv("LIGHTRAG_EMBEDDING_WORKERS", "2"))
            llm_workers = int(os.getenv("LIGHTRAG_LLM_WORKERS", "1"))

            rag = LightRAG(
                working_dir=workspace_path,
                llm_model_func=llm_model_func,
                embedding_func=embedding_func,
                chunk_token_size=400,  # GigaChat max is 514, using 400 for safety
                chunk_overlap_token_size=50,  # Smaller overlap for smaller chunks
                # Configurable worker counts to avoid rate limiting
                embedding_func_max_async=embedding_workers,
                llm_model_max_async=llm_workers,
            )

            logger.info(
                f"LightRAG workers: {embedding_workers} embedding, {llm_workers} LLM"
            )

            await rag.initialize_storages()
            await initialize_pipeline_status()

            # Test embedding function to verify setup
            try:
                test_embedding = await embedding_func(["test"])
                detected_dim = (
                    len(test_embedding[0])
                    if test_embedding
                    else embedding_adapter.embedding_dim
                )
                logger.info(f"Embedding dimension verified: {detected_dim}")
            except Exception as e:
                logger.warning(f"Could not verify embedding dimension: {e}")

            self._graphs[graph_id] = rag
            logger.info(f"Created async LightRAG instance for graph: {graph_id}")

        except Exception as e:
            logger.error(f"Error creating LightRAG instance for {graph_id}: {e}")
            raise

        return rag

    # ------------------------------------------------------------
    #                   PUBLIC ASYNC API
    # ------------------------------------------------------------

    async def save(self, graph_id: str, text: str) -> bool:
        """
        Асинхронно сохранить текст в граф.
        """
        logger.debug(f"Saving text to graph {graph_id}: {len(text)} chars")
        try:
            rag = await self._get_or_create_graph(graph_id)
            await rag.ainsert(text)
            logger.info(f"Inserted text into graph {graph_id}: {len(text)} chars")
            return True

        except Exception as e:
            logger.error(f"Error inserting text into graph {graph_id}: {e}")
            return False

    async def query(
        self,
        graph_id: str,
        question: str,
        mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = "hybrid",
    ) -> str:
        """
        Асинхронный запрос к графу LightRAG.
        """
        try:
            if mode not in GRAPH_QUERY_MODES:
                raise ValueError(f"Invalid mode: {mode}")

            rag = await self._get_or_create_graph(graph_id)

            result = await rag.aquery(question, param=QueryParam(mode=mode))

            logger.info(f"Async query to graph {graph_id}, mode={mode}")

            return result  # type: ignore

        except Exception as e:
            logger.error(f"Error querying graph {graph_id}: {e}")
            return f"Ошибка при выполнении запроса: {str(e)}"

    async def delete_graph(self, graph_id: str) -> bool:
        """
        Асинхронно удалить граф с диска.
        """
        try:
            if graph_id in self._graphs:
                del self._graphs[graph_id]

            workspace_path = self._get_workspace_path(graph_id)
            if os.path.exists(workspace_path):
                import shutil

                shutil.rmtree(workspace_path)
                logger.info(f"Deleted graph {graph_id} from disk")

            return True

        except Exception as e:
            logger.error(f"Error deleting graph {graph_id}: {e}")
            return False

    async def list_graphs(self) -> List[str]:
        """
        Асинхронно получить список графов.
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

    async def cleanup(self, graph_id: Optional[str] = None) -> None:
        """
        Асинхронно финализировать хранилища для корректного завершения.

        Args:
            graph_id: ID конкретного графа или None для очистки всех графов.
        """
        try:
            if graph_id and graph_id in self._graphs:
                await self._graphs[graph_id].finalize_storages()
                logger.info(f"Finalized storage for graph: {graph_id}")
            elif not graph_id:
                for gid, rag in self._graphs.items():
                    await rag.finalize_storages()
                    logger.info(f"Finalized storage for graph: {gid}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
