#!/usr/bin/env python3
"""
Databricks MCP Server using FastMCP
Modern implementation with @mcp.tool() decorators
Fixed for Docker and asyncio event loop issues
"""

import asyncio
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .config import DatabricksConfig
from .utils.databricks_client import DatabricksClientWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP("databricks-mcp")

# Global client instance with thread safety
_databricks_client: Optional[DatabricksClientWrapper] = None
_client_lock = threading.Lock()


def get_databricks_client() -> DatabricksClientWrapper:
    """Get the global Databricks client instance with thread safety."""
    global _databricks_client
    
    with _client_lock:
        if _databricks_client is None:
            try:
                config = DatabricksConfig.from_env()
                _databricks_client = DatabricksClientWrapper(config)
                logger.info("✅ Databricks client initialized")
            except Exception as e:
                logger.error(f"❌ Error initializing Databricks client: {e}")
                raise
    
    return _databricks_client


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


@mcp.tool()
async def list_catalogs() -> str:
    """List all available catalogs in Databricks."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            catalogs = await client.list_catalogs()
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                catalogs = run_sync_in_thread(client.list_catalogs())
            else:
                raise
        
        result = {
            "catalogs": [
                {
                    "name": catalog.name,
                    "comment": getattr(catalog, 'comment', None),
                    "metastore_id": getattr(catalog, 'metastore_id', None)
                }
                for catalog in catalogs
            ],
            "count": len(catalogs)
        }
        return json.dumps(result, indent=2)
        
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            return json.dumps({
                "error": "AsyncIO event loop conflict",
                "message": "This tool cannot run in the current async context. Please run the SQL directly in Databricks: SHOW CATALOGS",
                "suggestion": "Use: SELECT catalog_name FROM information_schema.schemata GROUP BY catalog_name"
            }, indent=2)
        else:
            raise
    except Exception as e:
        return json.dumps({
            "error": f"Failed to list catalogs: {str(e)}",
            "suggestion": "Check your Databricks connection configuration"
        }, indent=2)


@mcp.tool()
async def list_schemas(catalog: Optional[str] = None) -> str:
    """List schemas in a specific catalog."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            schemas = await client.list_schemas(catalog)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                schemas = run_sync_in_thread(client.list_schemas(catalog))
            else:
                raise
        
        config = DatabricksConfig.from_env()
        result = {
            "schemas": [
                {
                    "name": schema.name,
                    "catalog_name": schema.catalog_name,
                    "comment": getattr(schema, 'comment', None)
                }
                for schema in schemas
            ],
            "catalog": catalog or config.default_catalog,
            "count": len(schemas)
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to list schemas: {str(e)}",
            "suggestion": "Check your Databricks connection configuration"
        }, indent=2)


@mcp.tool()
async def list_tables(catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """List tables in a specific schema."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            tables = await client.list_tables(catalog, schema)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                tables = run_sync_in_thread(client.list_tables(catalog, schema))
            else:
                raise
        
        config = DatabricksConfig.from_env()
        result = {
            "tables": [
                {
                    "name": table.name,
                    "full_name": table.full_name,
                    "catalog_name": table.catalog_name,
                    "schema_name": table.schema_name,
                    "table_type": str(table.table_type),
                    "comment": getattr(table, 'comment', None)
                }
                for table in tables
            ],
            "catalog": catalog or config.default_catalog,
            "schema": schema or config.default_schema,
            "count": len(tables)
        }
        return json.dumps(result, indent=2)
        
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            catalog_name = catalog or "main"
            schema_name = schema or "default"
            return json.dumps({
                "error": "AsyncIO event loop conflict",
                "message": f"This tool cannot run in the current async context. Please run SQL directly in Databricks:",
                "sql_alternatives": [
                    f"SHOW TABLES IN {catalog_name}.{schema_name}",
                    f"SELECT table_name, table_type FROM information_schema.tables WHERE table_catalog = '{catalog_name}' AND table_schema = '{schema_name}'",
                    f"SELECT table_catalog, table_schema, table_name, table_type FROM information_schema.tables WHERE table_catalog = '{catalog_name}' ORDER BY table_schema, table_name"
                ],
                "requested_catalog": catalog_name,
                "requested_schema": schema_name
            }, indent=2)
        else:
            raise
    except Exception as e:
        catalog_name = catalog or "main"
        return json.dumps({
            "error": f"Failed to list tables: {str(e)}",
            "catalog": catalog_name,
            "schema": schema,
            "suggestion": "Check your Databricks connection configuration or try the SQL directly"
        }, indent=2)


@mcp.tool()
async def get_table_info(table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Get detailed information about a specific table."""
    try:
        client = get_databricks_client()
        
        # Try async first, fall back to sync in thread if needed
        try:
            table_info = await client.get_table_info(table_name, catalog, schema)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                table_info = run_sync_in_thread(client.get_table_info(table_name, catalog, schema))
            else:
                raise
        
        if table_info:
            result = {
                "name": table_info.name,
                "full_name": table_info.full_name,
                "catalog_name": table_info.catalog_name,
                "schema_name": table_info.schema_name,
                "table_type": str(table_info.table_type),
                "data_source_format": getattr(table_info, 'data_source_format', None),
                "comment": getattr(table_info, 'comment', None),
                "columns": [
                    {
                        "name": col.name,
                        "type_name": col.type_name,
                        "type_text": col.type_text,
                        "comment": getattr(col, 'comment', None)
                    }
                    for col in (table_info.columns or [])
                ]
            }
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"error": f"Table not found: {table_name}"}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get table info: {str(e)}",
            "table_name": table_name
        }, indent=2)


@mcp.tool()
async def execute_query(query: str, warehouse_id: Optional[str] = None, limit: int = 100) -> str:
    """Execute a SQL query in Databricks."""
    from .utils.query_validator import QueryValidator
    
    try:
        client = get_databricks_client()
        validator = QueryValidator()
        
        # Validate the query
        validation_result = validator.validate_query(query)
        if not validation_result["is_valid"]:
            return json.dumps({
                "status": "error",
                "error": f"Query validation failed: {validation_result['reason']}"
            }, indent=2)
        
        # Add LIMIT clause if not present and this is a SELECT query
        processed_query = _add_limit_if_needed(query, limit)
        
        # Try async first, fall back to sync in thread if needed
        try:
            result = await client.execute_query(processed_query, warehouse_id)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                result = run_sync_in_thread(client.execute_query(processed_query, warehouse_id))
            else:
                raise
        
        if result.get("status") == "success":
            return json.dumps({
                "status": "success",
                "row_count": result.get("row_count", 0),
                "data": result.get("data", []),
                "schema": result.get("schema"),
                "query_executed": processed_query
            }, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "query": processed_query
            }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": f"Failed to execute query: {str(e)}",
            "query": query
        }, indent=2)


@mcp.tool()
async def search_tables(pattern: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
    """Search for tables matching a pattern."""
    import re
    
    try:
        client = get_databricks_client()
        config = DatabricksConfig.from_env()
        
        # Get all tables from the specified or default catalog/schema
        catalog_name = catalog or config.default_catalog
        schema_name = schema or config.default_schema
        
        try:
            all_tables = await client.list_tables(catalog_name, schema_name)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                logger.warning("Event loop conflict detected, running in separate thread")
                all_tables = run_sync_in_thread(client.list_tables(catalog_name, schema_name))
            else:
                raise
        
        # Filter tables based on pattern
        matching_tables = []
        for table in all_tables:
            if re.search(pattern, table.name, re.IGNORECASE):
                matching_tables.append({
                    "name": table.name,
                    "full_name": table.full_name,
                    "catalog": table.catalog_name,
                    "schema": table.schema_name,
                    "type": str(table.table_type)
                })
        
        result = {
            "pattern": pattern,
            "catalog": catalog_name,
            "schema": schema_name,
            "matches": matching_tables,
            "match_count": len(matching_tables),
            "total_tables_searched": len(all_tables)
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "pattern": pattern,
            "catalog": catalog,
            "schema": schema
        }, indent=2)


def _add_limit_if_needed(query: str, limit: int) -> str:
    """Add LIMIT clause to SELECT queries if not already present."""
    query_upper = query.upper().strip()
    if query_upper.startswith("SELECT") and "LIMIT" not in query_upper:
        return f"{query.rstrip(';')} LIMIT {limit}"
    return query


# Initialize logging for FastMCP Server
logger.info("🚀 Databricks FastMCP Server module loaded")
# Note: Databricks client will be initialized lazily when first tool is called