"""
Databricks MCP Server

This module contains the unified FastMCP server implementation.
All server functionality is consolidated into a single main.py entry point.
"""

from .main import main

__all__ = [
    "main"
] 