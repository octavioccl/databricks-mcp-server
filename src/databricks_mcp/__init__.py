"""
Databricks MCP Server

A Model Context Protocol (MCP) server for Databricks Unity Catalog and SQL Warehouses.
Provides tools for listing catalogs, schemas, tables, executing queries, and more.
"""

from pathlib import Path

__version__ = "1.0.0"
__author__ = "Databricks MCP Team"
__email__ = "support@databricks.com"
__description__ = "MCP Server for Databricks Unity Catalog"

# Package metadata
__title__ = "databricks-mcp"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Databricks Inc."

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = Path(__file__).parent.parent
PACKAGE_ROOT = Path(__file__).parent

# Expose main components
from .core.config import DatabricksConfig, MCPConfig
from .core.utils.databricks_client import DatabricksClientWrapper

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "DatabricksConfig",
    "MCPConfig", 
    "DatabricksClientWrapper",
    "PROJECT_ROOT",
    "SRC_ROOT",
    "PACKAGE_ROOT"
] 