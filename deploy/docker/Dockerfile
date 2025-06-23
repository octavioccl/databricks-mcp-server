# Multi-stage Dockerfile for Databricks MCP Server
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER_CONTAINER=true \
    PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements and application code
COPY pyproject.toml ./
COPY src/ ./src/
COPY bin/ ./bin/
COPY tools/ ./tools/
COPY docs/examples/ ./docs/examples/
COPY config.env.example ./

# Install the package in development mode
RUN pip install --no-cache-dir --upgrade pip && \
    # Install the package itself in development mode
    pip install -e . && \
    # Install additional dependencies that might not be in pyproject.toml
    pip install --no-cache-dir \
        fastmcp \
        "mcp[cli]" \
        databricks-sdk \
        python-dotenv \
        pydantic \
        aiofiles && \
    # Create logs directory and set permissions
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check - test import and basic functionality
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from databricks_mcp.core.config import DatabricksConfig; print('✅ Health check passed')" || exit 1

# Default command - FastMCP server entry point
CMD ["python", "-m", "databricks_mcp.servers.main_fastmcp"]

# Alternative entry points (can be overridden)
# For standard MCP server: CMD ["python", "-m", "databricks_mcp.servers.main"]
# For CLI tool: CMD ["databricks-mcp-server", "--server", "fastmcp"]
# For bin script: CMD ["./bin/databricks-mcp-server", "--server", "fastmcp"]

# Expose port for development (MCP typically uses stdio)
EXPOSE 8000

# Labels for container metadata
LABEL maintainer="Databricks MCP Team" \
      version="1.0.0" \
      description="Databricks MCP Server with asyncio fixes" \
      org.opencontainers.image.source="https://github.com/databricks/databricks-mcp-server" 