# Databricks MCP Server

A Model Context Protocol (MCP) server for Databricks that enables AI assistants to discover tables and generate queries using natural language.

## 🚀 Quick Setup

```bash
git clone <repository-url>
cd databricks-mcp-server
python setup.py  # Handles Poetry installation, dependencies, and configuration
```

This will create a local `.venv` directory with all dependencies managed by Poetry.

## Features

- **🔍 Table Discovery**: Search and list tables across catalogs and schemas by name patterns
- **📊 Table Information**: Get detailed schema information including columns, types, and properties
- **🤖 Natural Language Queries**: Generate SQL query suggestions based on natural language requests
- **🛡️ Secure SQL Execution**: Execute read-only queries with built-in safety checks
- **⚡ Async Operations**: Built with async/await for efficient performance
- **🔧 MCP Compatible**: Works with Claude Desktop, Cursor, and other MCP clients

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- Databricks workspace with:
  - Personal access token
  - SQL warehouse (recommended for full functionality)
  - Appropriate permissions for catalogs/schemas you want to query

## Installation

### Automatic Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd databricks-mcp-server
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```
   
   This will:
   - Check Poetry installation (install if needed)
   - Configure Poetry for local virtual environment
   - Install all dependencies
   - Set up environment variables
   - Test the connection

### Manual Setup

1. **Install Poetry** (if not already installed):
   ```bash
   # Linux/macOS
   curl -sSL https://install.python-poetry.org | python3 -

   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
   ```

2. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd databricks-mcp-server
   
   # Configure Poetry to create .venv in project directory
   poetry config virtualenvs.in-project true
   
   # Install dependencies
   poetry install
   ```

3. **Set up environment variables:**
   
   Copy the example configuration:
   ```bash
   cp config.env.example .env
   ```
   
   Edit `.env` with your Databricks credentials:
   ```env
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=your_personal_access_token
   DATABRICKS_SQL_WAREHOUSE_ID=your_sql_warehouse_id
   DEFAULT_CATALOG=main
   DEFAULT_SCHEMA=default
   ```

4. **Test your connection:**
   ```bash
   poetry run python test_connection.py
   ```

## Getting Databricks Credentials

### 1. Databricks Host
Your Databricks workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)

### 2. Personal Access Token
1. Go to your Databricks workspace
2. Click your username in the top right corner
3. Select "User Settings"
4. Go to the "Developer" tab
5. Click "Manage" next to "Access tokens"
6. Generate a new token and save it securely

### 3. SQL Warehouse ID
1. Go to "SQL Warehouses" in your Databricks workspace
2. Select your warehouse
3. Copy the warehouse ID from the connection details

## Usage

### Running the MCP Server

Start the server using Poetry:
```bash
# Option 1: Run directly with Poetry
poetry run python main.py

# Option 2: Activate Poetry shell first
poetry shell
python main.py

# Option 3: Use the convenient runner script
python run_poetry.py
```

### Testing with MCP Inspector

You can test the server using the MCP inspector:
```bash
poetry run npx @modelcontextprotocol/inspector python main.py
```

### Development Commands

Poetry provides convenient commands for development:
```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code
poetry run flake8 .

# Type checking
poetry run mypy .

# Run tests (when available)
poetry run pytest
```

## 🐳 Docker Support

For easy deployment and use with Cursor, the project includes Docker support.

### Quick Docker Start

```bash
# Build and run the container
./scripts/run_docker_mcp.sh

# Or use docker-compose directly
docker-compose up --build databricks-mcp
```

### Using with Cursor

To use this MCP server with Cursor, add the following configuration to your Cursor MCP settings:

**Option 1: Override environment variables directly in MCP config (Recommended)**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "databricks-mcp-server"
      ],
      "cwd": "/path/to/your/databricks-mcp-server",
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.azuredatabricks.net",
        "DATABRICKS_TOKEN": "your_token_here",
        "DATABRICKS_SQL_WAREHOUSE_ID": "your_warehouse_id",
        "DEFAULT_CATALOG": "your_catalog",
        "DEFAULT_SCHEMA": "your_schema",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Option 2: Use .env file**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/path/to/your/databricks-mcp-server/.env",
        "databricks-mcp-server"
      ],
      "cwd": "/path/to/your/databricks-mcp-server"
    }
  }
}
```

**Option 3: Use the run script**
```json
{
  "mcpServers": {
    "databricks": {
      "command": "./scripts/run_docker_mcp.sh",
      "cwd": "/path/to/your/databricks-mcp-server"
    }
  }
}
```

Replace `/path/to/your/databricks-mcp-server` with the actual path to your project directory.

> **💡 Tip**: Option 1 is recommended as it allows you to have different Databricks configurations for different projects without modifying files.

### Docker Environment Setup

1. **Create environment file:**
   ```bash
   cp config.env.example .env
   # Edit .env with your Databricks credentials
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t databricks-mcp-server .
   ```

3. **Run the container:**
   ```bash
   docker-compose up databricks-mcp
   ```

## Available MCP Tools

Once connected via MCP, you'll have access to these tools:

### Catalog Tools
- `list_catalogs` - List all available catalogs
- `list_schemas` - List schemas in a catalog  
- `list_tables` - List tables in a schema
- `describe_table` - Get table schema details

### Query Tools
- `execute_query` - Execute SQL queries (read-only)
- `validate_query` - Validate SQL syntax

### Natural Language Tools
- `generate_query_suggestions` - Convert natural language to SQL
- `analyze_query_intent` - Understand query intent
- `get_sample_queries` - Get example queries for tables

## Examples

Once configured with Cursor or another MCP client, you can ask things like:

- "Show me all the catalogs in Databricks"
- "What tables are available in the sales schema?"
- "Generate a SQL query to find customers who made purchases last month"
- "What's the schema of the user_events table?"
- "How many records are in the product_catalog table?"

## Configuration Options

You can configure the MCP server through environment variables, either in a `.env` file or directly in your MCP client configuration.

### Environment Variables

```env
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_personal_access_token

# Optional
DATABRICKS_SQL_WAREHOUSE_ID=your_sql_warehouse_id  # For query execution
DEFAULT_CATALOG=main                                # Default catalog to use
DEFAULT_SCHEMA=default                              # Default schema to use
LOG_LEVEL=INFO                                      # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Multiple Environment Configurations

You can easily manage multiple Databricks environments by using different MCP server configurations:

```json
{
  "mcpServers": {
    "databricks-dev": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "databricks-mcp-server"],
      "cwd": "/path/to/databricks-mcp-server",
      "env": {
        "DATABRICKS_HOST": "https://dev-workspace.azuredatabricks.net",
        "DATABRICKS_TOKEN": "dev_token",
        "DEFAULT_CATALOG": "dev_catalog"
      }
    },
    "databricks-prod": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "databricks-mcp-server"],
      "cwd": "/path/to/databricks-mcp-server",
      "env": {
        "DATABRICKS_HOST": "https://prod-workspace.azuredatabricks.net",
        "DATABRICKS_TOKEN": "prod_token",
        "DEFAULT_CATALOG": "prod_catalog"
      }
    }
  }
}
```

This allows you to switch between different Databricks environments within Cursor.

## Troubleshooting

### Connection Issues
1. Verify your Databricks credentials in `.env`
2. Check that your token has appropriate permissions
3. Ensure your SQL warehouse is running (for query execution)

### Docker Issues
1. Make sure Docker is running
2. Check that the `.env` file exists and has correct values
3. Verify the container can access your environment file

### MCP Client Integration
1. Ensure the paths in your MCP configuration are correct
2. Check that the Docker image is built successfully
3. Verify the MCP client can execute the configured command

## Development

### Project Structure
```
databricks-mcp-server/
├── databricks_mcp/          # Main MCP server package
│   ├── server.py            # MCP server implementation
│   ├── tools/               # MCP tool implementations
│   └── utils/               # Utility modules
├── scripts/                 # Helper scripts
├── examples/                # Example usage scripts
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── pyproject.toml          # Poetry configuration
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [Databricks SDK for Python](https://docs.databricks.com/dev-tools/sdk-python.html)
- Inspired by existing MCP server implementations

## Support

For questions and support:
1. Check the troubleshooting section above
2. Review Databricks documentation
3. Open an issue in the repository

## Asyncio and Docker Issues Fixed

### Problem
When running MCP servers in Docker containers, you might encounter the error:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

This occurs because:
1. The container environment may already have an event loop running
2. FastMCP tries to create its own event loop
3. Python's asyncio doesn't allow nested `asyncio.run()` calls

### Solution
This server includes comprehensive fixes for asyncio event loop conflicts:

1. **Environment Detection**: Automatically detects Docker environments and running event loops
2. **Multiple Startup Methods**: 
   - Sync mode for clean environments
   - New event loop creation for conflicted environments
   - Thread-based execution as fallback
3. **Graceful Fallbacks**: Each tool can fall back to thread-based execution if needed

### Technical Details
The server uses these strategies:

1. **Environment Detection**:
```python
# Detects Docker environment
in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'

# Detects running event loop
try:
    loop = asyncio.get_running_loop()
    has_running_loop = True
except RuntimeError:
    has_running_loop = False
```

2. **New Event Loop Strategy**:
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(mcp.run_async())
finally:
    loop.close()
```

3. **Thread-based Fallback**:
```python
def run_sync_in_thread(coro):
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()
```

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABRICKS_HOST` | Yes | Your Databricks workspace URL | `https://adb-xxx.azuredatabricks.net` |
| `DATABRICKS_TOKEN` | Yes | Personal access token or service principal token | `dapi...` |
| `DATABRICKS_SQL_WAREHOUSE_ID` | No* | SQL Warehouse ID for query execution | `88605d498bc68321` |
| `DEFAULT_CATALOG` | No | Default catalog name | `main` |
| `DEFAULT_SCHEMA` | No | Default schema name | `default` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `DOCKER_CONTAINER` | No | Set to `true` in Docker | `true` |

*Required for SQL query execution features

### Using .env File

Create a `.env` file based on `config.env.example`:

```bash
cp config.env.example .env
# Edit .env with your values
```

## Available Tools

### `list_catalogs()`
Lists all available catalogs in your Databricks workspace.

### `list_schemas(catalog?: string)`
Lists schemas in the specified catalog (or default catalog).

### `list_tables(catalog?: string, schema?: string)`
Lists tables in the specified schema.

### `get_table_info(table_name: string, catalog?: string, schema?: string)`
Gets detailed information about a specific table including columns and metadata.

### `execute_query(query: string, warehouse_id?: string, limit?: number)`
Executes a SQL query with validation. Automatically adds LIMIT clauses to SELECT queries.

### `search_tables(pattern: string, catalog?: string, schema?: string)`
Searches for tables matching a regex pattern.

## Development

### Local Development

```bash
# Install dependencies
pip install -e .

# Or with poetry
poetry install

# Run the server
python main_fastmcp.py

# Test the connection
python scripts/test_connection.py
```

### Testing Asyncio Fixes

```bash
# Test asyncio behavior
python scripts/test_docker_asyncio.py
```

### Building Docker Image

```bash
# Build the image
docker build -t databricks-mcp-server .

# Test the image
docker run --rm databricks-mcp-server python scripts/test_docker_asyncio.py
```

## Troubleshooting

### Common Issues

1. **"cannot be called from a running event loop"**
   - ✅ Fixed in this version with automatic fallbacks
   - The server will automatically detect and handle this situation

2. **Connection timeouts**
   - Check your `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
   - Ensure your network allows connections to Databricks

3. **SQL execution fails**
   - Verify `DATABRICKS_SQL_WAREHOUSE_ID` is set and valid
   - Check that the warehouse is running

4. **Docker container exits immediately**
   - Check the logs: `docker logs <container-id>`
   - Verify all required environment variables are set

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in Docker
docker run -e LOG_LEVEL=DEBUG ...
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
