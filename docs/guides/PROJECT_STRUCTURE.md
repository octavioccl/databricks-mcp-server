# Databricks MCP Server - Project Structure

## Overview

This project implements a comprehensive Databricks MCP (Model Context Protocol) server using **FastMCP**, providing AI agents with powerful tools to interact with Databricks workspaces.

## Architecture

The project uses a **single FastMCP server architecture** with all tools implemented as individual `@mcp.tool()` decorated functions. This approach provides:

- **Simplicity**: Single server process with all functionality
- **Performance**: Direct function calls without class overhead  
- **Maintainability**: All tools in one well-organized file
- **Docker Efficiency**: Single container deployment
- **MCP Compliance**: Modern FastMCP best practices

## Directory Structure

```
databricks-mcp-server/
├── bin/
│   └── databricks-mcp-server          # CLI entry point script
├── src/
│   └── databricks_mcp/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py                # CLI module entry point
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py              # Configuration management
│       │   ├── server_fastmcp.py      # 🚀 MAIN FastMCP SERVER
│       │   └── utils/
│       │       ├── __init__.py
│       │       ├── databricks_client.py
│       │       ├── natural_language.py
│       │       └── query_validator.py
│       └── servers/
│           ├── __init__.py
│           └── main.py                # Unified FastMCP server entry point
├── docs/                              # Documentation
├── deploy/                            # Docker deployment files
├── tools/                             # Utility scripts
└── tests/                             # Test files
```

## Core Components

### 1. FastMCP Server (`server_fastmcp.py`)

The heart of the application - a single FastMCP server containing all tools:

**Tool Categories:**
- **Catalog Tools** (6 tools): `list_catalogs`, `list_schemas`, `list_tables`, `get_table_info`, `search_tables`
- **Query Tools** (2 tools): `execute_query`, `execute_statement` 
- **Cluster Tools** (7 tools): `list_clusters`, `get_cluster`, `create_cluster`, `start_cluster`, `terminate_cluster`, `restart_cluster`
- **Job Tools** (3 tools): `list_jobs`, `get_job`, `run_job`
- **Natural Language Tools** (1 tool): `generate_sql_query`

**Key Features:**
- Async/await support with event loop conflict handling
- JSON-formatted responses for all tools
- Comprehensive error handling and logging
- Thread-safe client management
- Docker and local environment compatibility

### 2. Configuration (`config.py`)

Centralized configuration management:
- `DatabricksConfig`: Databricks connection settings
- `MCPConfig`: MCP server settings
- Environment variable loading with validation
- Secure credential handling

### 3. Utilities (`utils/`)

Supporting modules:
- `DatabricksClientWrapper`: Async Databricks SDK wrapper
- `QueryValidator`: SQL query validation and security
- `NaturalLanguageProcessor`: AI-powered query generation

### 4. Entry Points

Unified entry points for simplicity:
- `bin/databricks-mcp-server`: CLI script with options
- `cli/main.py`: Python module entry point  
- `servers/main.py`: Unified FastMCP server launcher

## Tool Implementation Pattern

All tools follow the FastMCP pattern:

```python
@mcp.tool()
async def tool_name(param1: str, param2: Optional[int] = None) -> str:
    """Tool description for the LLM."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            result = await client.some_operation(param1, param2)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                result = run_sync_in_thread(client.some_operation(param1, param2))
            else:
                raise
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)
```

## Key Design Decisions

### Why FastMCP Over Traditional MCP?

1. **Modern Approach**: FastMCP is the current best practice for MCP servers
2. **Simpler Code**: Decorators vs. complex class hierarchies
3. **Better Performance**: Direct function calls
4. **Easier Testing**: Functions can be tested independently
5. **Docker Friendly**: Single process, single server

### Why Single Server vs. Multiple Servers?

1. **Client Simplicity**: One connection, all tools available
2. **Resource Efficiency**: Single process, shared client connections
3. **Deployment Simplicity**: One Docker container
4. **Maintenance**: Single codebase to maintain
5. **Performance**: No inter-server communication overhead

### Async Event Loop Handling

The server handles async event loop conflicts (common in Docker/Jupyter environments) by:
1. Attempting async operations first
2. Falling back to running operations in separate threads with new event loops
3. Providing consistent JSON responses regardless of execution method

## Development Workflow

### Adding New Tools

1. Add the tool function to `server_fastmcp.py`
2. Use the `@mcp.tool()` decorator
3. Follow the error handling pattern
4. Add appropriate logging
5. Test the tool functionality

### Testing

```bash
# Syntax check
python -m py_compile src/databricks_mcp/core/server_fastmcp.py

# Run server locally
python src/databricks_mcp/servers/main.py

# Test with MCP inspector
npx @modelcontextprotocol/inspector python src/databricks_mcp/servers/main.py
```

### Docker Development

```bash
# Build and run
docker-compose -f deploy/docker/docker-compose.yml up --build

# Test connection
docker exec -it databricks-mcp-server python -c "from databricks_mcp.core.config import DatabricksConfig; print('✅ Config loaded')"
```

## Configuration

### Environment Variables

Required:
```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
```

Optional:
```bash
DATABRICKS_SQL_WAREHOUSE_ID=your-sql-warehouse-id
DATABRICKS_DEFAULT_CATALOG=main
DATABRICKS_DEFAULT_SCHEMA=default
MCP_SERVER_NAME=databricks-mcp
MCP_LOG_LEVEL=INFO
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "databricks": {
      "command": "python",
      "args": ["/path/to/databricks-mcp-server/src/databricks_mcp/servers/main.py"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "your-token"
      }
    }
  }
}
```

## Performance Characteristics

- **Memory Usage**: ~50-100MB per server instance
- **Startup Time**: ~2-5 seconds (depending on Databricks connection)
- **Tool Execution**: ~100-2000ms per tool (depending on operation)
- **Concurrent Requests**: Thread-safe, supports multiple concurrent tool calls
- **Docker Overhead**: Minimal, single process architecture

## Future Enhancements

1. **Tool Categories**: Consider splitting into multiple FastMCP servers if the single server becomes too large
2. **Caching**: Add intelligent caching for catalog/schema information
3. **Streaming**: Add streaming support for large query results
4. **Authentication**: Enhanced authentication and authorization
5. **Monitoring**: Built-in metrics and health checks 