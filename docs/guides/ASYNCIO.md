# AsyncIO Event Loop Fixes for Databricks MCP Server

## Problem Summary

When running the Databricks MCP Server in Docker containers with Cursor or other MCP clients, the following error occurs:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

This error happens because:

1. **Container Environment**: Docker containers may initialize with existing event loops
2. **FastMCP Implementation**: FastMCP uses async patterns that conflict with existing loops
3. **Nested Event Loops**: Python's asyncio doesn't allow `asyncio.run()` within an already running event loop
4. **Client-Server Interaction**: MCP clients (like Cursor) may start the server in an async context

## Root Cause Analysis

### Why This Happens in Docker

```python
# This works in a clean Python environment
asyncio.run(main())

# But fails in Docker/container environments where an event loop might already exist
# RuntimeError: asyncio.run() cannot be called from a running event loop
```

### Common Scenarios

1. **Cursor MCP Integration**: Cursor starts the Docker container within its own async context
2. **Jupyter-like Environments**: Some container runtimes have pre-existing event loops
3. **FastMCP + asyncio.to_thread**: The `asyncio.to_thread` calls in the Databricks client can conflict

## Comprehensive Solution

### 1. Environment Detection

The server now automatically detects the runtime environment:

```python
def detect_environment():
    """Detect the running environment and return appropriate startup method."""
    # Check if we're in Docker
    in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'
    
    # Check if there's already a running event loop
    try:
        loop = asyncio.get_running_loop()
        has_running_loop = True
    except RuntimeError:
        has_running_loop = False
    
    # Determine the best approach
    if in_docker:
        if has_running_loop:
            return "new_loop"  # Create fresh event loop
        else:
            return "sync"      # Use standard sync mode
    else:
        if has_running_loop:
            return "new_loop"  # Handle async context
        else:
            return "sync"      # Standard mode
```

### 2. Multiple Startup Strategies

#### Strategy A: Sync Mode (Default)
For clean environments without existing event loops:

```python
def run_server_sync():
    from databricks_mcp.server_fastmcp import mcp
    mcp.run()  # Standard FastMCP startup
```

#### Strategy B: New Event Loop
For environments with existing event loops:

```python
def run_server_new_loop():
    from databricks_mcp.server_fastmcp import mcp
    
    # Create isolated event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(mcp.run_async())
    finally:
        loop.close()  # Clean cleanup
```

#### Strategy C: Thread-based Execution
For individual tool calls that encounter event loop conflicts:

```python
def run_sync_in_thread(coro):
    """Run a coroutine in a separate thread with its own event loop."""
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        return future.result()
```

### 3. Graceful Fallbacks in Tools

Each MCP tool now includes automatic fallback handling:

```python
@mcp.tool()
async def list_catalogs() -> str:
    try:
        client = get_databricks_client()
        
        # Try async first
        try:
            catalogs = await client.list_catalogs()
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                # Automatic fallback to thread-based execution
                catalogs = run_sync_in_thread(client.list_catalogs())
            else:
                raise
        
        # Process results...
        return json.dumps(result, indent=2)
        
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            # Return helpful error message with SQL alternatives
            return json.dumps({
                "error": "AsyncIO event loop conflict",
                "message": "This tool cannot run in the current async context.",
                "suggestion": "Use: SHOW CATALOGS"
            }, indent=2)
```

### 4. Docker Environment Configuration

The Dockerfile includes specific environment variables to help with detection:

```dockerfile
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER_CONTAINER=true \
    PYTHONPATH=/app
```

### 5. Thread Safety

Added thread-safe client initialization:

```python
import threading

_databricks_client: Optional[DatabricksClientWrapper] = None
_client_lock = threading.Lock()

def get_databricks_client() -> DatabricksClientWrapper:
    global _databricks_client
    
    with _client_lock:
        if _databricks_client is None:
            config = DatabricksConfig.from_env()
            _databricks_client = DatabricksClientWrapper(config)
    
    return _databricks_client
```

## Testing the Fixes

### 1. Local Testing

```bash
# Test asyncio behavior
python scripts/test_docker_asyncio.py
```

Expected output:
```
=== Asyncio Behavior Test ===
Python version: 3.11.13
Running in Docker: False

Testing running loop detection...
✅ No running loop detected

Testing asyncio.run() in sync context...
✅ asyncio.run() worked: True

Testing new event loop approach...
✅ New event loop worked: True

Testing thread approach...
✅ Thread approach worked: True
```

### 2. Docker Testing

```bash
# Build the fixed image
docker build -t databricks-mcp-server-fastmcp-fixed .

# Test in Docker environment
docker run --rm databricks-mcp-server-fastmcp-fixed python scripts/test_docker_asyncio.py
```

Expected output:
```
=== Asyncio Behavior Test ===
Python version: 3.11.13
Running in Docker: True

Testing running loop detection...
✅ No running loop detected

✅ Successfully imported FastMCP server
✅ Successfully imported config
```

### 3. Integration Testing with Cursor

Update your `mcp.json`:

```json
{
  "mcpServers": {
    "databricks": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "DATABRICKS_HOST=your-host",
        "-e", "DATABRICKS_TOKEN=your-token",
        "-e", "DATABRICKS_SQL_WAREHOUSE_ID=your-warehouse-id",
        "-e", "DEFAULT_CATALOG=your-catalog",
        "-e", "DEFAULT_SCHEMA=your-schema",
        "-e", "LOG_LEVEL=DEBUG",
        "databricks-mcp-server-fastmcp-fixed"
      ]
    }
  }
}
```

## Key Benefits

1. **✅ Automatic Detection**: No manual configuration needed
2. **✅ Multiple Fallbacks**: Graceful degradation if one method fails
3. **✅ Informative Errors**: Clear error messages with SQL alternatives
4. **✅ Thread Safety**: Safe for concurrent usage
5. **✅ Debug Support**: Comprehensive logging for troubleshooting
6. **✅ Zero Breaking Changes**: Existing functionality preserved

## Migration Guide

### For Existing Users

1. **Rebuild Docker Image**:
   ```bash
   docker build -t your-image-name .
   ```

2. **Update MCP Config**:
   - Change image name in your `mcp.json`
   - No other changes needed

3. **Test**:
   ```bash
   # Verify the fix works
   docker run --rm your-image-name python scripts/test_docker_asyncio.py
   ```

### For New Users

Simply follow the standard installation process - the fixes are automatically included.

## Advanced Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `DOCKER_CONTAINER` | Force Docker detection | `true` (set in Dockerfile) |
| `LOG_LEVEL` | Enable debug logging | `INFO` |
| `PYTHONPATH` | Ensure imports work | `/app` |

### Debugging

Enable detailed logging:

```bash
docker run -e LOG_LEVEL=DEBUG your-image-name
```

Look for these log messages:
- `🐳 Running in Docker container`
- `⚠️  Detected running event loop`
- `💡 Using new event loop approach for Docker`
- `Event loop conflict detected, running in separate thread`

## References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [FastMCP documentation](https://gofastmcp.com/deployment/running-server)
- [MCP specification](https://modelcontextprotocol.io/specification)
- [Docker best practices for Python](https://docs.docker.com/language/python/best-practices/)

## Future Improvements

1. **Native Async Support**: Future versions of FastMCP may include better async context handling
2. **Performance Optimization**: Thread-based execution could be optimized further
3. **Error Recovery**: More sophisticated error recovery mechanisms
4. **Health Checks**: Better container health monitoring 