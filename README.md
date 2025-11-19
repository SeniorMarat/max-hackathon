# Max Bot with LightRAG & GigaChat

Бот с интеграцией LightRAG (граф знаний) и GigaChat API.

### 1. Настройка окружения

```bash
# Копируем пример .env файла
cp .env.example .env

# Редактируем .env и добавляем BOT_TOKEN
nano .env
```

### 2. Запуск через докер

```bash
docker-compose up -d
```

### 2.1. Установка зависимостей

#### С использованием UV (рекомендуется)

```bash
# Установка UV
pip install uv

# Установка всех зависимостей из pyproject.toml
uv sync
source .venv/bin/activate
```

### 2.2 Запуск

```bash
python main.py
```
