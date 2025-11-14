"""
Тестовый скрипт для проверки GraphMemory с LightRAG и GigaChat
"""

import logging
import os

from dotenv import load_dotenv

from graph_memory import GraphMemory

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv()


def test_graph_memory():
    """Тестирование GraphMemory с GigaChat и LightRAG"""

    # Проверяем наличие GIGACHAT_CREDENTIALS
    if not os.getenv("GIGACHAT_CREDENTIALS"):
        logger.error("GIGACHAT_CREDENTIALS not found in .env file!")
        return

    logger.info("=" * 60)
    logger.info("Testing GraphMemory with LightRAG and GigaChat")
    logger.info("=" * 60)

    try:
        # Создаем GraphMemory
        logger.info("\n1. Initializing GraphMemory...")
        graph_memory = GraphMemory()
        logger.info("✓ GraphMemory initialized successfully")

        # Тестовый граф
        test_graph_id = "test_graph"

        # Добавляем тестовые данные
        logger.info(f"\n2. Adding test data to graph '{test_graph_id}'...")

        test_texts = [
            """
            МГТУ им. Баумана - это один из ведущих технических университетов России.
            Университет был основан в 1830 году. МГТУ специализируется на подготовке
            инженеров в области машиностроения, ракетостроения, информационных
            технологий и других технических направлений.
            """,
            """
            Факультет информатики и систем управления (ИУ) МГТУ им. Баумана готовит
            специалистов в области программирования, искусственного интеллекта,
            информационной безопасности и систем управления. На факультете работают
            ведущие ученые и преподаватели.
            """,
            """
            Студенты МГТУ им. Баумана имеют доступ к современным лабораториям,
            библиотеке с большим количеством научной литературы, а также возможность
            участвовать в научных исследованиях и проектах с ведущими компаниями.
            """,
        ]

        for i, text in enumerate(test_texts, 1):
            logger.info(f"  Adding text {i}/{len(test_texts)}...")
            success = graph_memory.save(test_graph_id, text.strip())
            if success:
                logger.info(f"  ✓ Text {i} added successfully")
            else:
                logger.error(f"  ✗ Failed to add text {i}")

        # Делаем запросы к графу
        logger.info(f"\n3. Querying graph '{test_graph_id}'...")

        questions = [
            "Когда был основан МГТУ им. Баумана?",
            "Какие направления подготовки есть на факультете ИУ?",
            "Какие возможности есть у студентов МГТУ?",
        ]

        for i, question in enumerate(questions, 1):
            logger.info(f"\n  Question {i}: {question}")

            # Используем hybrid режим для лучшего качества ответов
            answer = graph_memory.query(test_graph_id, question, mode="hybrid")

            logger.info(f"  Answer: {answer[:200]}...")
            logger.info(f"  (Full answer length: {len(answer)} chars)")

        # Список всех графов
        logger.info("\n4. Listing all graphs...")
        graphs = graph_memory.list_graphs()
        logger.info(f"  Found {len(graphs)} graph(s): {graphs}")

        # Опционально: удаление тестового графа
        # logger.info(f"\n5. Deleting test graph '{test_graph_id}'...")
        # if graph_memory.delete_graph(test_graph_id):
        #     logger.info("  ✓ Test graph deleted successfully")
        # else:
        #     logger.error("  ✗ Failed to delete test graph")

        logger.info("\n" + "=" * 60)
        logger.info("Test completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)


if __name__ == "__main__":
    test_graph_memory()
