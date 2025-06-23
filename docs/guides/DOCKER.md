# Docker Fixes for Databricks MCP Server

This document explains the Docker-related issues that were resolved during the project reorganization and how they were fixed.

## Issues Identified

### 1. **Import Path Problems**
After reorganizing the project structure, the Docker container had issues with:
- Module import paths not matching the new `src/` layout
- Legacy imports referencing non-existent modules
- Missing package installation in development mode

### 2. **Entry Point Issues**
- The CLI entry points were not properly configured
- Module execution paths were incorrect
- Package scripts were not installed in the container

### 3. **Dependency Management**
- Some dependencies were not properly installed
- Package was not installed in development mode
- Missing system dependencies for git operations

## Solutions Implemented

### 1. **Fixed Dockerfile** (`deploy/docker/Dockerfile`)

#### **Before:**
```dockerfile
# Old approach - just copying files
COPY databricks_mcp/ ./databricks_mcp/
COPY *.py ./

# Installing dependencies without package
RUN pip install fastmcp mcp databricks-sdk
```

#### **After:**
```dockerfile
# New approach - proper package installation
COPY src/ ./src/
COPY pyproject.toml ./

# Install package in development mode
RUN pip install -e . && \
    pip install fastmcp "mcp[cli]" databricks-sdk
```

#### **Key Improvements:**
- ✅ **Package Installation**: Using `pip install -e .` to properly install the package
- ✅ **Correct Paths**: Using `src/` layout with proper PYTHONPATH
- ✅ **System Dependencies**: Added `git` for package installations
- ✅ **Health Checks**: Improved health check to test actual imports
- ✅ **Entry Points**: Multiple entry point options available

### 2. **Fixed Server Entry Points**

#### **FastMCP Server** (`src/databricks_mcp/servers/main_fastmcp.py`)
- ✅ Correct import paths for new structure
- ✅ Proper error handling and fallbacks
- ✅ Environment detection for Docker

#### **Standard Server** (`src/databricks_mcp/servers/main.py`)
- ✅ Updated to use correct import paths
- ✅ Fixed legacy `databricks_mcp.server` import issue
- ✅ Proper error messages and guidance

### 3. **Enhanced CLI Entry Point** (`src/databricks_mcp/cli/main.py`)
- ✅ Delegates to bin script when available
- ✅ Falls back to direct execution
- ✅ Proper argument passing
- ✅ Error handling and user guidance

### 4. **Improved Docker Compose** (`deploy/docker/docker-compose.yml`)
- ✅ Correct build context pointing to project root
- ✅ Multiple service profiles (FastMCP and Standard)
- ✅ Health checks and restart policies
- ✅ Proper volume management

## Testing the Fixes

### 1. **Build and Test**
```bash
# Build the Docker image
docker build -f deploy/docker/Dockerfile -t databricks-mcp-server .

# Test basic imports
docker run --rm databricks-mcp-server python -c "from databricks_mcp.core.config import DatabricksConfig; print('✅ OK')"

# Test CLI
docker run --rm databricks-mcp-server databricks-mcp-server --version
docker run --rm databricks-mcp-server databricks-mcp-server --help

# Test FastMCP server
docker run --rm databricks-mcp-server python -m databricks_mcp.servers.main_fastmcp

# Test with Docker Compose
cd deploy/docker
docker-compose up --build
```

### 2. **Available Entry Points**

The Docker container now supports multiple ways to start the server:

```bash
# 1. Default FastMCP server (recommended)
docker run databricks-mcp-server

# 2. Via CLI tool with options
docker run databricks-mcp-server databricks-mcp-server --server fastmcp

# 3. Via Python module
docker run databricks-mcp-server python -m databricks_mcp.servers.main_fastmcp

# 4. Standard MCP server
docker run databricks-mcp-server python -m databricks_mcp.servers.main

# 5. Via bin script
docker run databricks-mcp-server ./bin/databricks-mcp-server --server fastmcp
```

## Configuration for Cursor

The cursor MCP configuration now works correctly:

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
        "databricks-mcp-server"
      ]
    }
  }
}
```

## Benefits of the Fixes

### 1. **Reliability**
- ✅ Proper package installation prevents import errors
- ✅ Multiple fallback mechanisms for different environments
- ✅ Better error messages for troubleshooting

### 2. **Flexibility**
- ✅ Multiple server implementations (FastMCP, Standard)
- ✅ Various entry points for different use cases
- ✅ Docker Compose profiles for different scenarios

### 3. **Maintainability**
- ✅ Clean separation between development and production setups
- ✅ Proper Python packaging standards
- ✅ Clear documentation and examples

### 4. **Performance**
- ✅ Optimized Docker layers for faster builds
- ✅ Proper dependency caching
- ✅ Health checks for container monitoring

## Troubleshooting

### Common Issues and Solutions

#### **Import Errors**
```bash
# Problem: ModuleNotFoundError
# Solution: Ensure package is installed
docker run --rm databricks-mcp-server pip list | grep databricks-mcp
```

#### **Permission Issues**
```bash
# Problem: Permission denied
# Solution: Check user and file permissions
docker run --rm databricks-mcp-server ls -la /app/
```

#### **Environment Variables**
```bash
# Problem: Missing configuration
# Solution: Check environment variables
docker run --rm databricks-mcp-server databricks-mcp-server --config
```

#### **AsyncIO Issues**
```bash
# Problem: Event loop conflicts
# Solution: The server automatically detects and handles these
# Check logs for environment detection messages
```

## Future Improvements

### 1. **Multi-stage Builds**
- Separate build and runtime stages
- Smaller final image size
- Better security with minimal runtime dependencies

### 2. **Kubernetes Support**
- Helm charts for K8s deployment
- ConfigMaps and Secrets management
- Horizontal pod autoscaling

### 3. **Monitoring**
- Prometheus metrics endpoint
- Health check improvements
- Logging standardization

### 4. **Security**
- Non-root user execution (already implemented)
- Secret management best practices
- Container scanning integration

## Conclusion

The Docker fixes ensure that the Databricks MCP Server works reliably in containerized environments with:

✅ **Proper Python packaging**  
✅ **Multiple entry points**  
✅ **Robust error handling**  
✅ **Clear documentation**  
✅ **Production-ready configuration**  

The server now works seamlessly with Cursor and other MCP clients in Docker environments. 