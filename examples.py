"""
Примеры использования GraphMemory с различными сценариями
"""

from graph_memory import GraphMemory


def example_1_basic_usage():
    """Пример 1: Базовое использование - добавление и запрос"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 1: Базовое использование")
    print("=" * 60)

    gm = GraphMemory()

    # Добавляем информацию
    gm.save("basic", "Москва - столица России. Население более 12 миллионов человек.")

    # Запрашиваем
    answer = gm.query("basic", "Какая столица России?")
    print(f"Ответ: {answer}")


def example_2_multiple_texts():
    """Пример 2: Добавление нескольких текстов в один граф"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Множественные тексты в одном графе")
    print("=" * 60)

    gm = GraphMemory()

    texts = [
        "Python - высокоуровневый язык программирования.",
        "Python был создан Гвидо ван Россумом в 1991 году.",
        "Python используется для web-разработки, data science, ML.",
    ]

    for text in texts:
        gm.save("python_info", text)

    # Запросы к единому графу знаний
    questions = [
        "Кто создал Python?",
        "Когда был создан Python?",
        "Где используется Python?",
    ]

    for q in questions:
        answer = gm.query("python_info", q, mode="hybrid")
        print(f"\nQ: {q}")
        print(f"A: {answer[:100]}...")


def example_3_different_modes():
    """Пример 3: Разные режимы поиска"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 3: Разные режимы поиска")
    print("=" * 60)

    gm = GraphMemory()

    # Добавляем данные
    gm.save(
        "modes_test",
        """
        Квантовые компьютеры используют принципы квантовой механики.
        Они могут решать определенные задачи быстрее классических компьютеров.
        Квантовые биты (кубиты) могут находиться в суперпозиции состояний.
        """,
    )

    question = "Что такое квантовые компьютеры?"

    # Тестируем разные режимы
    modes = ["naive", "local", "global", "hybrid"]

    for mode in modes:
        answer = gm.query("modes_test", question, mode=mode)
        print(f"\nРежим '{mode}':")
        print(f"  {answer[:80]}...")


def example_4_multiple_graphs():
    """Пример 4: Работа с несколькими графами"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 4: Несколько графов")
    print("=" * 60)

    gm = GraphMemory()

    # Создаем разные графы для разных тем
    graphs = {
        "history": "Вторая мировая война длилась с 1939 по 1945 год.",
        "science": "Фотосинтез - процесс преобразования света в химическую энергию.",
        "tech": "Блокчейн - это распределенная база данных.",
    }

    for graph_id, text in graphs.items():
        gm.save(graph_id, text)

    # Список всех графов
    all_graphs = gm.list_graphs()
    print(f"Создано графов: {len(all_graphs)}")
    print(f"Графы: {all_graphs}")

    # Запросы к разным графам
    print("\nЗапросы к разным графам:")
    answer1 = gm.query("history", "Когда была вторая мировая война?")
    print(f"История: {answer1[:60]}...")

    answer2 = gm.query("science", "Что такое фотосинтез?")
    print(f"Наука: {answer2[:60]}...")


def example_5_graph_management():
    """Пример 5: Управление графами"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 5: Управление графами")
    print("=" * 60)

    gm = GraphMemory()

    # Создаем временный граф
    temp_graph = "temp_graph"
    gm.save(temp_graph, "Временные данные для тестирования")

    # Проверяем наличие
    graphs_before = gm.list_graphs()
    print(f"Графов до удаления: {len(graphs_before)}")
    print(f"Список: {graphs_before}")

    # Удаляем граф
    if temp_graph in graphs_before:
        gm.delete_graph(temp_graph)
        print(f"\n✓ Граф '{temp_graph}' удален")

    # Проверяем после удаления
    graphs_after = gm.list_graphs()
    print(f"Графов после удаления: {len(graphs_after)}")
    print(f"Список: {graphs_after}")


def example_6_incremental_updates():
    """Пример 6: Постепенное обновление графа"""
    print("\n" + "=" * 60)
    print("ПРИМЕР 6: Постепенное обновление графа")
    print("=" * 60)

    gm = GraphMemory()

    graph_id = "incremental"

    # День 1: базовая информация
    gm.save(graph_id, "Компания X основана в 2020 году.")

    # День 2: добавление деталей
    gm.save(graph_id, "Компания X специализируется на разработке AI.")

    # День 3: еще больше информации
    gm.save(graph_id, "В компании X работает 100 сотрудников.")

    # Теперь можем задавать комплексные вопросы
    questions = [
        "Когда основана компания X?",
        "Чем занимается компания X?",
        "Сколько сотрудников в компании X?",
    ]

    for q in questions:
        answer = gm.query(graph_id, q, mode="hybrid")
        print(f"\nQ: {q}")
        print(f"A: {answer[:80]}...")


def main():
    """Запуск всех примеров"""
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ GraphMemory")
    print("=" * 60)

    try:
        example_1_basic_usage()
        example_2_multiple_texts()
        example_3_different_modes()
        example_4_multiple_graphs()
        example_5_graph_management()
        example_6_incremental_updates()

        print("\n" + "=" * 60)
        print("✅ Все примеры выполнены успешно!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nУбедитесь что:")
        print("1. Установлены все зависимости")
        print("2. GIGACHAT_CREDENTIALS настроен в .env")


if __name__ == "__main__":
    main()
