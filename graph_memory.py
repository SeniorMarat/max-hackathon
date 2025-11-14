import os

import requests
from dotenv import load_dotenv

load_dotenv()


class GraphMemory:
    """
    Менеджер для нескольких локальных графов LightRAG,
    работает через LightRAG API сервер.

    Каждый граф — отдельный workspace (папка).
    """

    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url.rstrip("/")
        self.base_workspace = os.getenv("LIGHRAG_WORKSPACE_BASE", "./data/lightrag")

        os.makedirs(self.base_workspace, exist_ok=True)

    def _workspace(self, graph_id: str) -> str:
        """
        Возвращает путь к workspace конкретного графа.
        """
        path = os.path.join(self.base_workspace, graph_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _post(self, endpoint: str, data: dict):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        r = requests.post(url, json=data, timeout=30)
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------
    #                      PUBLIC API
    # ------------------------------------------------------------

    def save(self, graph_id: str, text: str):
        """
        Сохранить текст в граф знаний (обновление LightRAG).
        """
        workspace = self._workspace(graph_id)
        return self._post(
            "insert",
            {
                "workspace": workspace,
                "text": text,
            },
        )

    def query(self, graph_id: str, question: str) -> str:
        """
        Сделать запрос к выбранному графу.
        """
        workspace = self._workspace(graph_id)
        result = self._post(
            "query",
            {
                "workspace": workspace,
                "query": question,
            },
        )
        return result.get("answer", "")
