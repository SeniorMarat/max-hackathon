import asyncio
import glob
import logging
import os

from memory.graph_memory import GraphMemory

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

GRAPH_ID = "NSU"
BAZA_PATH = "./baza/*.md"


async def build_nsu_graph():
    print("=== Создание графа NSU ===")

    gm = GraphMemory()
    rag_instance = None

    try:
        files = glob.glob(BAZA_PATH)
        if not files:
            print("❌ В папке ./baza/ нет markdown файлов!")
            return

        print(f"Найдено файлов: {len(files)}")
        print("Начинаю загрузку...")

        for idx, file_path in enumerate(files, 1):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

                if not text.strip():
                    print(f"⚠️ Файл пустой: {file_path}")
                    continue

                filename = os.path.basename(file_path)
                print(f"→ [{idx}/{len(files)}] Добавление в граф: {filename}")
                ok = await gm.save(GRAPH_ID, text)

                if not ok:
                    print(f"❌ Ошибка вставки данных из файла: {file_path}")
                else:
                    print(f"✔ Успех: {file_path}")

            except Exception as e:
                logger.error(f"❌ Ошибка чтения файла {file_path}: {e}")

        print("\n=== Граф NSU собран ===")
        print(f"Всего файлов обработано: {len(files)}")
        print(f"Граф хранится в: {os.path.abspath(gm.workspace_path)}/{GRAPH_ID}")

        # Get RAG instance for cleanup
        if GRAPH_ID in gm._graphs:
            rag_instance = gm._graphs[GRAPH_ID]

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # Properly finalize storages
        if rag_instance:
            logger.info("Finalizing storages...")
            await rag_instance.finalize_storages()
            print("✔ Хранилище закрыто корректно")


if __name__ == "__main__":
    asyncio.run(build_nsu_graph())
