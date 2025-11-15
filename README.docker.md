# Max Bot - Docker Setup

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose installed
- `.env` file with your credentials (copy from `.env.example`)

### 1. Setup Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

Make sure to set at minimum:

- `BOT_TOKEN` - Your Max Bot token
- `GIGACHAT_CREDENTIALS` - Your GigaChat API credentials

### 2. Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the bot in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### 3. Alternative: Run with Docker directly

```bash
# Build the image
docker build -t max-bot .

# Run the container
docker run -d \
  --name max-bot \
  --env-file .env \
  -v $(pwd)/data/lightrag:/app/data/lightrag \
  max-bot

# View logs
docker logs -f max-bot

# Stop the container
docker stop max-bot
docker rm max-bot
```

## Docker Commands Reference

### Viewing Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific time
docker-compose logs --since 30m
```

### Restarting the Bot

```bash
# Restart after code changes
docker-compose restart

# Rebuild and restart (after dependency changes)
docker-compose up -d --build
```

### Managing Containers

```bash
# Check container status
docker-compose ps

# Stop the bot
docker-compose stop

# Start the bot
docker-compose start

# Remove containers (keeps data)
docker-compose down

# Remove containers and volumes (deletes data!)
docker-compose down -v
```

### Accessing the Container

```bash
# Open a shell in the running container
docker-compose exec max-bot /bin/bash

# Run a command in the container
docker-compose exec max-bot python --version
```

## Data Persistence

The LightRAG graph data is stored in `./data/lightrag` on your host machine and mounted into the container. This ensures your knowledge graphs persist even if you rebuild or restart the container.

## Development Mode

To enable live code reloading during development, uncomment the volume mounts in `docker-compose.yml`:

```yaml
volumes:
  - ./data/lightrag:/app/data/lightrag
  - ./bot:/app/bot
  - ./llm:/app/llm
  - ./memory:/app/memory
  - ./maxbot_api:/app/maxbot_api
```

Then restart with:

```bash
docker-compose restart
```

## Troubleshooting

### Container exits immediately

Check logs for errors:

```bash
docker-compose logs
```

Common issues:

- Missing or invalid credentials in `.env`
- Network connectivity issues
- Permission issues with data directory

### Out of memory errors

Uncomment and adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

### Permission issues with data directory

Fix permissions:

```bash
sudo chown -R $(id -u):$(id -g) ./data
```

## Production Considerations

1. **Resource Limits**: Uncomment and adjust the `deploy` section in `docker-compose.yml`
2. **Restart Policy**: Already set to `unless-stopped` for automatic recovery
3. **Log Rotation**: Configured with 10MB max size and 3 files
4. **Secrets Management**: Consider using Docker secrets instead of `.env` for production
5. **Monitoring**: Add health checks and monitoring solutions

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:

- `BOT_TOKEN` - Required: Your Max Bot token
- `GIGACHAT_CREDENTIALS` - Required: GigaChat API credentials
- `GIGACHAT_SCOPE` - Optional: API scope (default: GIGACHAT_API_PERS)
- `GIGACHAT_MODEL` - Optional: Model name (default: GigaChat)
- `LIGHRAG_WORKSPACE_BASE` - Optional: Data directory (default: ./data/lightrag)
- `GIGACHAT_CALLS_PER_MINUTE` - Optional: Rate limit (default: 20)
