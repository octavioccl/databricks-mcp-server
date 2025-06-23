#!/bin/bash

# Simple Docker runner for Databricks MCP Server
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "❌ .env file not found. Please create it from config.env.example"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

cd "$PROJECT_DIR"

# Build and run the container
echo "🚀 Building and starting Databricks MCP Server..."
docker-compose up --build databricks-mcp 