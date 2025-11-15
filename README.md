# Max Bot - Long Polling Example with LightRAG & GigaChat

Бот с интеграцией LightRAG (граф знаний) и GigaChat API.

## Быстрый старт (без контейнера)

### 1. Настройка окружения

```bash
# Копируем пример .env файла
cp .env.example .env

# Редактируем .env и добавляем GIGACHAT_CREDENTIALS
nano .env
```

### 2. Установка зависимостей

#### С использованием UV (рекомендуется)

```bash
# Установка UV
pip install uv

# Установка всех зависимостей из pyproject.toml
uv sync

# Активация виртуального окружения
source .venv/bin/activate
```

### 3. Запуск

#### Простой пример

```bash
python main.py
```


## LightRAG + GigaChat Integration

Проект использует **локальное хранение графов знаний** через LightRAG с **GigaChat API** для:

- Генерации текста (LLM)
- Создания эмбеддингов

### Основные компоненты

- **`llm/gigachat.py`** - Адаптеры GigaChatLLM и GigaChatEmbedding для LightRAG
- **`graph_memory.py`** - Менеджер графов знаний с простым API
- **`test_graph_memory.py`** - Примеры и тесты

## Требования

- Python >= 3.13
- GigaChat API credentials
- Зависимости из `pyproject.toml`

## Примечания

- Графы хранятся локально в `./data/lightrag/` (настраивается через `LIGHRAG_WORKSPACE_BASE`)
- Каждый граф имеет свой уникальный `graph_id`
- Поддерживается несколько режимов поиска: `naive`, `local`, `global`, `hybrid`
