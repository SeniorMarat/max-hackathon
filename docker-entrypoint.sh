#!/bin/bash
set -e

# Ensure data directory exists
mkdir -p /app/data/lightrag

# Check if required environment variables are set
if [ -z "$BOT_TOKEN" ]; then
    echo "ERROR: BOT_TOKEN environment variable is not set"
    exit 1
fi

if [ -z "$GIGACHAT_CREDENTIALS" ]; then
    echo "ERROR: GIGACHAT_CREDENTIALS environment variable is not set"
    exit 1
fi

echo "Starting Max Bot with GigaChat integration..."
echo "Using LightRAG workspace: ${LIGHRAG_WORKSPACE_BASE:-./data/lightrag}"
echo "GigaChat model: ${GIGACHAT_MODEL:-GigaChat}"

# Execute the main command
exec "$@"
