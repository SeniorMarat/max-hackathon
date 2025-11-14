"""
Пример использования GraphMemory с LightRAG и GigaChat
"""

from graph_memory import GraphMemory


def main():
    """Простой пример использования GraphMemory"""

    # Инициализация (credentials берутся из .env)
    graph_memory = GraphMemory()

    # ID графа
    graph_id = "my_knowledge_base"

    # Добавление информации в граф
    print("Adding data to knowledge graph...")
    graph_memory.save(
        graph_id,
        """
        LightRAG - это система для работы с графами знаний.
        Она использует векторные базы данных для быстрого поиска.
        GigaChat - это большая языковая модель от Сбера.
        """,
    )

    # Запрос к графу
    print("\nQuerying knowledge graph...")
    question = "Что такое LightRAG?"
    answer = graph_memory.query(graph_id, question, mode="hybrid")
    print(f"\nQuestion: {question}")
    print(f"Answer: {answer}")

    # Список всех графов
    graphs = graph_memory.list_graphs()
    print(f"\nAvailable graphs: {graphs}")


if __name__ == "__main__":
    main()
