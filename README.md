# Databricks MCP Server

A comprehensive **FastMCP** server that provides AI agents with powerful tools to interact with Databricks workspaces. Built with modern MCP best practices using individual `@mcp.tool()` decorated functions in a single, efficient server.

## 🚀 Architecture

This project uses a **unified FastMCP server architecture** with all tools implemented as individual `@mcp.tool()` decorated functions, providing:

- **35+ MCP Tools** across 6 comprehensive categories
- **Single Entry Point**: Simplified deployment and management
- **Async/Await Support**: With event loop conflict handling for Docker environments  
- **JSON Responses**: Structured, consistent tool outputs
- **Thread-Safe**: Concurrent tool execution support
- **Docker Ready**: Optimized for containerized deployment with Poetry

## ✨ Features

### 🗄️ **Catalog Management Tools** (6 tools)
- **`list_catalogs`** - Browse available data catalogs
- **`list_schemas`** - Explore schemas within catalogs  
- **`list_tables`** - Discover tables and views
- **`get_table_info`** - Get detailed table metadata and schema
- **`search_tables`** - Find tables using pattern matching
- **`generate_sql_query`** - AI-powered SQL generation from natural language

### 🔍 **Advanced Query Execution** (2 tools)
- **`execute_query`** - Execute SQL queries with automatic LIMIT handling
- **`execute_statement`** - Advanced SQL execution with parameters, catalogs, schemas, and timeout control

### 🖥️ **Cluster Management** (7 tools)
- **`list_clusters`** - View all workspace clusters
- **`get_cluster`** - Get detailed cluster information
- **`create_cluster`** - Create new clusters with autoscaling
- **`start_cluster`** - Start stopped clusters
- **`terminate_cluster`** - Terminate running clusters
- **`restart_cluster`** - Restart clusters for maintenance
- **`resize_cluster`** - Dynamically resize cluster capacity

### ⚙️ **Job Management** (9 tools)
- **`list_jobs`** - Browse all workspace jobs
- **`get_job`** - Get detailed job configuration
- **`run_job`** - Execute jobs with custom parameters
- **`create_job`** - Create new job definitions
- **`update_job`** - Modify existing jobs
- **`delete_job`** - Remove job definitions
- **`get_run`** - Get job run details and status
- **`cancel_run`** - Cancel running job executions
- **`list_runs`** - Browse job execution history

### 📓 **Notebook Operations** (7 tools)
- **`list_notebooks`** - Browse workspace notebooks
- **`get_notebook`** - Retrieve notebook metadata
- **`export_notebook`** - Export in multiple formats (SOURCE, HTML, JUPYTER, DBC)
- **`import_notebook`** - Import notebooks with base64 content
- **`delete_notebook`** - Remove notebooks safely
- **`create_directory`** - Create workspace directories
- **`get_notebook_status`** - Check notebook availability

### 📁 **DBFS File System** (8 tools)
- **`list_files`** - Browse DBFS directories
- **`get_file`** - Download file contents (text/binary)
- **`put_file`** - Upload files with base64 encoding
- **`upload_large_file`** - Chunked upload for large files
- **`delete_file`** - Remove files and directories
- **`get_status`** - Get file/directory metadata
- **`create_directory`** - Create DBFS directories
- **`move_file`** - Move/rename files and directories

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Databricks workspace access
- Personal Access Token or Service Principal credentials

### Quick Start

1. **Install dependencies:**
   ```bash
   pip install fastmcp 'mcp[cli]' databricks-sdk
   ```

2. **Set environment variables:**
   ```bash
   export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   export DATABRICKS_TOKEN=your-personal-access-token
   export DATABRICKS_SQL_WAREHOUSE_ID=your-warehouse-id  # optional
   ```

3. **Run the server:**
   ```bash
   # Using the CLI script
   ./bin/databricks-mcp-server
   
   # Or directly with Python
   python src/databricks_mcp/servers/main.py
   ```

### Claude Desktop Configuration

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "databricks": {
      "command": "python",
      "args": ["/path/to/databricks-mcp-server/src/databricks_mcp/servers/main.py"],
      "env": {
        "DATABRICKS_HOST": "https://your-workspace.cloud.databricks.com",
        "DATABRICKS_TOKEN": "your-token-here"
      }
    }
  }
}
```

## 🐳 Docker Deployment

### Using Docker Compose

1. **Copy environment configuration:**
   ```bash
   cp config.env.example config.env
   # Edit config.env with your Databricks credentials
   ```

2. **Build and run:**
   ```bash
   docker-compose -f deploy/docker/docker-compose.yml up --build
   ```

### Claude Desktop with Docker

```json
{
  "mcpServers": {
    "databricks": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env-file", "/path/to/config.env",
        "databricks-mcp-server"
      ]
    }
  }
}
```

## 🔧 Configuration

### Environment Variables

**Required:**
```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-personal-access-token
```

**Optional:**
```bash
DATABRICKS_SQL_WAREHOUSE_ID=your-sql-warehouse-id
DATABRICKS_DEFAULT_CATALOG=main
DATABRICKS_DEFAULT_SCHEMA=default
MCP_SERVER_NAME=databricks-mcp
MCP_LOG_LEVEL=INFO
MCP_ENABLE_QUERY_EXECUTION=true
MCP_ENABLE_NATURAL_LANGUAGE=true
```

### Security Considerations

- Store tokens securely (environment variables, not in code)
- Use SQL Warehouse IDs for query execution (recommended)
- Consider read-only access tokens for production use
- Validate all SQL queries through built-in query validator

## 🧪 Testing & Development

### Test Connection
```bash
./bin/databricks-mcp-server --test
```

### Development Mode
```bash
# Start with debug logging
./bin/databricks-mcp-server --log DEBUG

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python src/databricks_mcp/servers/main.py
```

### Adding New Tools

1. Add your tool function to `src/databricks_mcp/core/server_fastmcp.py`
2. Use the `@mcp.tool()` decorator
3. Follow the established error handling pattern
4. Test with the MCP Inspector

Example:
```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Description of what this tool does."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            result = await client.some_operation(param)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                result = run_sync_in_thread(client.some_operation(param))
            else:
                raise
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2)
```

## 📊 Performance

- **Memory Usage**: ~50-100MB per server instance
- **Startup Time**: ~2-5 seconds (depending on Databricks connection)
- **Tool Execution**: ~100-2000ms per tool (depending on operation)
- **Concurrent Requests**: Thread-safe, supports multiple concurrent tool calls
- **Docker Overhead**: Minimal, single process architecture

## 🔍 Troubleshooting

### Common Issues

1. **AsyncIO Event Loop Conflicts**: The server automatically handles these by running operations in separate threads
2. **Connection Timeouts**: Check your `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
3. **Permission Errors**: Ensure your token has appropriate workspace permissions
4. **Docker Issues**: Verify environment variables are properly passed to the container

### Debug Mode
```bash
./bin/databricks-mcp-server --log DEBUG --test
```

### Logs
The server provides comprehensive logging. Check logs for:
- Connection status
- Tool execution details
- Error messages with suggested fixes
- Performance metrics

## 📚 Documentation

- **[Project Structure](docs/guides/PROJECT_STRUCTURE.md)** - Detailed architecture overview
- **[AsyncIO Guide](docs/guides/ASYNCIO.md)** - Handling async event loops
- **[Docker Guide](docs/guides/DOCKER.md)** - Container deployment
- **[Examples](docs/examples/)** - Usage examples and demos

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the established patterns
4. Test your changes (`python -m py_compile src/databricks_mcp/core/server_fastmcp.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - Modern MCP server framework
- [Databricks SDK](https://github.com/databricks/databricks-sdk-py) - Python SDK for Databricks
- [Model Context Protocol](https://modelcontextprotocol.io/) - Protocol specification
- [Anthropic](https://www.anthropic.com/) - MCP protocol development

---

**Built with ❤️ using FastMCP and the Databricks SDK**

*This server provides a comprehensive interface between AI agents and Databricks workspaces, enabling powerful data analysis, job management, and workspace automation through natural language interactions.*
