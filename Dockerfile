# Use Python 3.12 as base image (3.13 may not be widely available yet)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Install Python dependencies
RUN uv pip install --system --no-cache \
    ruff \
    python-dotenv \
    "requests>=2.32.5" \
    "gigachat>=0.1.0" \
    "lightrag-hku>=1.4.9.8" \
    nano-vectordb \
    "networkx>=3.0" \
    "numpy>=1.24.0"

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create data directory for LightRAG graphs
RUN mkdir -p /app/data/lightrag

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LIGHRAG_WORKSPACE_BASE=/app/data/lightrag

# Expose port (if needed for future web interface)
# EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Run the bot
CMD ["python", "main.py"]
