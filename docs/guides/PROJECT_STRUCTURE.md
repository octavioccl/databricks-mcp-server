# Project Structure Guide

This document explains the reorganized folder structure of the Databricks MCP Server project, following Python best practices and modern project organization principles.

## Overview

The project has been restructured to provide better separation of concerns, improved maintainability, and easier development workflows.

## Directory Structure

```
databricks-mcp-server/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT License
├── pyproject.toml              # Modern Python project configuration
├── config.env.example          # Environment configuration template
│
├── src/                        # Source code (follows Python src-layout)
│   ├── databricks_mcp/         # Main package
│   │   ├── __init__.py         # Package initialization and metadata
│   │   ├── core/               # Core functionality
│   │   │   ├── __init__.py     # Core package exports
│   │   │   ├── config.py       # Configuration management
│   │   │   ├── server_fastmcp.py  # FastMCP server implementation
│   │   │   ├── server.py       # Standard MCP server implementation
│   │   │   ├── tools/          # MCP tool implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── catalog_tools.py    # Catalog management tools
│   │   │   │   ├── query_tools.py      # Query execution tools
│   │   │   │   └── natural_language_tools.py  # NL processing tools
│   │   │   └── utils/          # Utility modules
│   │   │       ├── __init__.py
│   │   │       ├── databricks_client.py   # Databricks SDK wrapper
│   │   │       ├── query_validator.py     # SQL query validation
│   │   │       └── natural_language.py    # NL processing utilities
│   │   ├── servers/            # Server entry points
│   │   │   ├── __init__.py     # Server implementations
│   │   │   ├── main_fastmcp.py # FastMCP server entry point
│   │   │   └── main.py         # Standard MCP server entry point
│   │   └── cli/                # Command line interface
│   │       ├── __init__.py     # CLI package
│   │       └── main.py         # Main CLI entry point
│   └── tests/                  # Test suite
│       ├── __init__.py         # Test package
│       ├── test_connection.py  # Connection tests
│       └── test_simple_connection.py  # Basic tests
│
├── bin/                        # Executable scripts
│   └── databricks-mcp-server   # Main CLI executable
│
├── tools/                      # Development and utility tools
│   ├── scripts/                # Utility scripts
│   │   ├── list_tools.py       # List available MCP tools
│   │   ├── test_connection.py  # Test Databricks connection
│   │   ├── test_docker_asyncio.py  # AsyncIO testing
│   │   └── run_docker_mcp.sh   # Docker runner script
│   └── dev/                    # Development utilities (reserved)
│
├── deploy/                     # Deployment configurations
│   ├── docker/                 # Docker deployment
│   │   ├── Dockerfile          # Container definition
│   │   └── docker-compose.yml  # Docker Compose configuration
│   └── k8s/                    # Kubernetes deployment (reserved)
│
└── docs/                       # Documentation
    ├── README.md               # Main documentation
    ├── api/                    # API documentation (reserved)
    ├── guides/                 # User and developer guides
    │   ├── ASYNCIO_FIXES.md    # AsyncIO troubleshooting guide
    │   └── PROJECT_STRUCTURE.md  # This file
    └── examples/               # Usage examples
        └── natural_language_demo.py  # NL processing example
```

## Design Principles

### 1. **src-layout Structure**
- All source code is under `src/` directory
- Prevents accidental imports of package during development
- Cleaner separation between source and other files

### 2. **Separation of Concerns**
- **Core**: Business logic and functionality
- **Servers**: Entry points and server implementations  
- **CLI**: Command-line interface and user interaction
- **Tools**: Development and utility scripts
- **Deploy**: Deployment configurations
- **Docs**: Documentation and examples

### 3. **Modular Architecture**
```python
# Clear import hierarchy
from databricks_mcp.core.config import DatabricksConfig
from databricks_mcp.core.utils.databricks_client import DatabricksClientWrapper
from databricks_mcp.servers.main_fastmcp import main as fastmcp_main
```

## Key Components

### Core Package (`src/databricks_mcp/core/`)

**Purpose**: Contains the essential business logic and functionality.

- **`config.py`**: Configuration management for both Databricks and MCP settings
- **`server_fastmcp.py`**: Modern FastMCP server with async tool decorators
- **`server.py`**: Legacy standard MCP server implementation
- **`tools/`**: Individual MCP tool implementations
- **`utils/`**: Shared utilities and helper functions

### Servers Package (`src/databricks_mcp/servers/`)

**Purpose**: Entry points for different server implementations.

- **`main_fastmcp.py`**: FastMCP server with asyncio fixes for Docker
- **`main.py`**: Standard MCP server entry point

### CLI Package (`src/databricks_mcp/cli/`)

**Purpose**: Command-line interface and user interactions.

- **`main.py`**: Main CLI entry point used by package scripts
- Handles argument parsing, configuration validation, and server startup

### Deployment (`deploy/`)

**Purpose**: Production deployment configurations.

- **`docker/`**: Docker containers and compose files
- **`k8s/`**: Kubernetes deployments (planned)

### Tools (`tools/`)

**Purpose**: Development and operational utilities.

- **`scripts/`**: Utility scripts for testing and development
- **`dev/`**: Development-specific tools (reserved)

## Benefits of This Structure

### 1. **Better Organization**
- Clear separation between different types of code
- Easy to navigate and understand
- Follows Python packaging best practices

### 2. **Improved Development**
- `src-layout` prevents import issues during development
- Modular structure allows independent testing
- Clear dependency hierarchy

### 3. **Easier Deployment**
- Docker configuration separated from source code
- Multiple entry points (CLI, FastMCP, Standard)
- Environment-specific configurations

### 4. **Enhanced Maintainability**
- Each module has a single responsibility
- Easy to add new features without affecting existing code
- Clear interfaces between components

## Migration Notes

### From Old Structure
```bash
# Old structure
databricks_mcp/
├── server.py
├── server_fastmcp.py
├── tools/...
└── utils/...

# New structure  
src/databricks_mcp/
├── core/
│   ├── server.py
│   ├── server_fastmcp.py
│   ├── tools/...
│   └── utils/...
├── servers/
│   ├── main_fastmcp.py
│   └── main.py
└── cli/
    └── main.py
```

### Import Changes
```python
# Old imports
from databricks_mcp.config import DatabricksConfig
from databricks_mcp.server_fastmcp import mcp

# New imports
from databricks_mcp.core.config import DatabricksConfig  
from databricks_mcp.core.server_fastmcp import mcp
```

### Entry Points
```bash
# Multiple ways to start the server

# Via installed CLI
databricks-mcp-server --server fastmcp

# Via bin script
./bin/databricks-mcp-server --server fastmcp

# Via Python module
python -m databricks_mcp.servers.main_fastmcp

# Via Docker
docker run databricks-mcp-server-fastmcp
```

## Development Workflow

### 1. **Setup**
```bash
# Install in development mode
pip install -e .[dev]

# Or using the traditional approach
pip install -e .
pip install pytest black isort mypy
```

### 2. **Testing**
```bash
# Run tests
pytest src/tests/

# Test specific functionality
python tools/scripts/test_connection.py
```

### 3. **Development Server**
```bash
# Start development server
./bin/databricks-mcp-server --server fastmcp --log DEBUG

# Test with different configurations
./bin/databricks-mcp-server --config
./bin/databricks-mcp-server --test
```

### 4. **Docker Development**
```bash
# Build and test Docker image
docker build -f deploy/docker/Dockerfile -t databricks-mcp-dev .
docker run --env-file config.env databricks-mcp-dev
```

## Future Enhancements

### 1. **API Documentation** (`docs/api/`)
- Auto-generated API docs from docstrings
- OpenAPI specifications for HTTP endpoints

### 2. **Kubernetes Deployment** (`deploy/k8s/`)
- Helm charts for Kubernetes deployment
- ConfigMaps and Secrets management

### 3. **Development Tools** (`tools/dev/`)
- Code generation utilities
- Development database setup scripts
- Performance profiling tools

### 4. **Plugin System** (`src/databricks_mcp/plugins/`)
- Extensible plugin architecture
- Third-party tool integrations

## Conclusion

This restructured project organization provides:

✅ **Clear separation of concerns**  
✅ **Better development experience**  
✅ **Easier deployment and maintenance**  
✅ **Follows Python best practices**  
✅ **Supports multiple deployment scenarios**  

The modular structure makes it easy to extend functionality, add new server implementations, or integrate with different deployment environments while maintaining clean, maintainable code. 