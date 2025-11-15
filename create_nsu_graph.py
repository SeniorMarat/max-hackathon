import asyncio
import glob
import os

from memory.graph_memory import GraphMemory

GRAPH_ID = "NSU"
BAZA_PATH = "./baza/*.md"


async def build_nsu_graph():
    print("=== Создание графа NSU ===")

    gm = GraphMemory()

    files = glob.glob(BAZA_PATH)
    if not files:
        print("❌ В папке ./baza/ нет markdown файлов!")
        return

    print(f"Найдено файлов: {len(files)}")
    print("Начинаю загрузку...")

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            if not text.strip():
                print(f"⚠️ Файл пустой: {file_path}")
                continue

            print(f"→ Добавление в граф: {os.path.basename(file_path)}")
            ok = await gm.save(GRAPH_ID, text)

            if not ok:
                print(f"❌ Ошибка вставки данных из файла: {file_path}")
            else:
                print(f"✔ Успех: {file_path}")

        except Exception as e:
            print(f"❌ Ошибка чтения файла {file_path}: {e}")

    print("\n=== Граф NSU собран ===")
    print(f"Всего файлов обработано: {len(files)}")
    print(f"Граф хранится в: {os.path.abspath(gm.workspace_path)}/{GRAPH_ID}")


if __name__ == "__main__":
    asyncio.run(build_nsu_graph())
