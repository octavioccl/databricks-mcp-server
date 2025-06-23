# Dockerfile for Databricks MCP Server
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER_CONTAINER=true \
    PYTHONPATH=/app/src

# Create user (skip system dependencies for simplicity)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy Poetry configuration and README first for better caching
COPY pyproject.toml README.md ./

# Install Poetry and dependencies (without the current project)
RUN pip install --no-cache-dir --upgrade pip poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main --no-root && \
    # Create logs directory and set permissions
    mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Copy application code
COPY src/ ./src/
COPY bin/ ./bin/
COPY tools/ ./tools/
COPY docs/examples/ ./docs/examples/
COPY config.env.example ./

# Install the package itself
RUN poetry install --only-root && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check - test import and basic functionality
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from databricks_mcp.core.config import DatabricksConfig; print('✅ Health check passed')" || exit 1

# Default command - Databricks MCP server entry point
CMD ["python", "-m", "databricks_mcp.servers.main"]

# Alternative entry points (can be overridden)
# For CLI tool: CMD ["databricks-mcp-server"]
# For bin script: CMD ["./bin/databricks-mcp-server"]

# Expose port for development (MCP typically uses stdio)
EXPOSE 8000

# Labels for container metadata
LABEL maintainer="Databricks MCP Team" \
      version="1.0.0" \
      description="Databricks MCP Server - Unified FastMCP Architecture" \
      org.opencontainers.image.source="https://github.com/databricks/databricks-mcp-server" 