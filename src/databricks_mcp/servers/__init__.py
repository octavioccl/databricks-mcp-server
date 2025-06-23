"""
MCP Server implementations for Databricks.

This module contains different server implementations:
- FastMCP server (modern, recommended)
- Standard MCP server (legacy)
- CLI entry points
"""

from .main_fastmcp import main as fastmcp_main
from .main import main as standard_main

__all__ = [
    "fastmcp_main",
    "standard_main"
] 