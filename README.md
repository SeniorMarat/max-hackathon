# Max Bot - Long Polling Example with LightRAG & GigaChat

Бот с интеграцией LightRAG (граф знаний) и GigaChat API.

## Быстрый старт

### 1. Настройка окружения

```bash
# Копируем пример .env файла
cp .env.example .env

# Редактируем .env и добавляем GIGACHAT_CREDENTIALS
nano .env
```

### 2. Установка зависимостей

#### Вариант 1: С использованием UV (рекомендуется)

```bash
# Установка UV
pip install uv

# Установка всех зависимостей из pyproject.toml
uv sync

# Активация виртуального окружения
source .venv/bin/activate
```

#### Вариант 2: С использованием pip

```bash
# Установка зависимостей
pip install -e .

# Или используйте скрипт
bash install_deps.sh
```

### 3. Использование

#### Простой пример

```bash
python main.py
```

#### Детальное тестирование

```bash
python test_graph_memory.py
```

## LightRAG + GigaChat Integration

Проект использует **локальное хранение графов знаний** через LightRAG с **GigaChat API** для:

- Генерации текста (LLM)
- Создания эмбеддингов

### Основные компоненты

- **`llm/gigachat.py`** - Адаптеры GigaChatLLM и GigaChatEmbedding для LightRAG
- **`graph_memory.py`** - Менеджер графов знаний с простым API
- **`test_graph_memory.py`** - Примеры и тесты

### Документация

Подробную документацию смотрите в [LIGHTRAG_SETUP.md](./LIGHTRAG_SETUP.md)

## API GraphMemory

```python
from graph_memory import GraphMemory

# Инициализация
graph_memory = GraphMemory()

# Сохранение данных в граф
graph_memory.save("graph_id", "Ваш текст здесь")

# Запрос к графу
answer = graph_memory.query("graph_id", "Ваш вопрос?", mode="hybrid")

# Список графов
graphs = graph_memory.list_graphs()

# Удаление графа
graph_memory.delete_graph("graph_id")
```

## Структура проекта

```
.
├── llm/                    # Модули для работы с LLM
│   └── gigachat.py        # GigaChat клиент и адаптеры для LightRAG
├── graph_memory.py         # Менеджер графов знаний
├── test_graph_memory.py    # Тесты и примеры
├── main.py                 # Простой пример использования
├── pyproject.toml          # Зависимости проекта
├── .env.example            # Пример конфигурации
└── LIGHTRAG_SETUP.md       # Подробная документация
```

## Требования

- Python >= 3.12
- GigaChat API credentials
- Зависимости из `pyproject.toml`

## Примечания

- Графы хранятся локально в `./data/lightrag/` (настраивается через `LIGHRAG_WORKSPACE_BASE`)
- Каждый граф имеет свой уникальный `graph_id`
- Поддерживается несколько режимов поиска: `naive`, `local`, `global`, `hybrid`
