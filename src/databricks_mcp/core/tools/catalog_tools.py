"""
Catalog-related MCP tools for Databricks.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.types import Tool

logger = logging.getLogger(__name__)


class CatalogTools:
    """Tools for browsing Databricks catalogs, schemas, and tables."""
    
    def __init__(self, databricks_client, config):
        """Initialize catalog tools."""
        self.client = databricks_client
        self.config = config
    
    async def get_tools(self) -> List[Tool]:
        """Get list of available catalog tools."""
        return [
            Tool(
                name="list_catalogs",
                description="List all available catalogs in Databricks",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="list_schemas",
                description="List schemas in a specific catalog",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "catalog": {
                            "type": "string",
                            "description": "Name of the catalog"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="list_tables",
                description="List tables in a specific schema",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "catalog": {
                            "type": "string",
                            "description": "Name of the catalog"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Name of the schema"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_table_info",
                description="Get detailed information about a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Full table name (catalog.schema.table) or just table name"
                        },
                        "catalog": {
                            "type": "string",
                            "description": "Catalog name (optional if included in table_name)"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema name (optional if included in table_name)"
                        }
                    },
                    "required": ["table_name"]
                }
            )
        ]
    
    async def get_tool_names(self) -> List[str]:
        """Get list of tool names."""
        tools = await self.get_tools()
        return [tool.name for tool in tools]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Handle a catalog tool call."""
        try:
            if name == "list_catalogs":
                return await self._list_catalogs()
            elif name == "list_schemas":
                return await self._list_schemas(arguments.get("catalog"))
            elif name == "list_tables":
                return await self._list_tables(
                    arguments.get("catalog"),
                    arguments.get("schema")
                )
            elif name == "get_table_info":
                return await self._get_table_info(
                    arguments["table_name"],
                    arguments.get("catalog"),
                    arguments.get("schema")
                )
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            return f"Error: {str(e)}"
    
    async def _list_catalogs(self) -> str:
        """List all catalogs."""
        catalogs = await self.client.list_catalogs()
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
    
    async def _list_schemas(self, catalog: Optional[str] = None) -> str:
        """List schemas in a catalog."""
        schemas = await self.client.list_schemas(catalog)
        result = {
            "schemas": [
                {
                    "name": schema.name,
                    "catalog_name": schema.catalog_name,
                    "comment": getattr(schema, 'comment', None)
                }
                for schema in schemas
            ],
            "catalog": catalog or self.config.default_catalog,
            "count": len(schemas)
        }
        return json.dumps(result, indent=2)
    
    async def _list_tables(self, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
        """List tables in a schema."""
        tables = await self.client.list_tables(catalog, schema)
        result = {
            "tables": [
                {
                    "name": table.name,
                    "full_name": table.full_name,
                    "catalog_name": table.catalog_name,
                    "schema_name": table.schema_name,
                    "table_type": table.table_type,
                    "comment": getattr(table, 'comment', None)
                }
                for table in tables
            ],
            "catalog": catalog or self.config.default_catalog,
            "schema": schema or self.config.default_schema,
            "count": len(tables)
        }
        return json.dumps(result, indent=2)
    
    async def _get_table_info(self, table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> str:
        """Get detailed table information."""
        table_info = await self.client.get_table_info(table_name, catalog, schema)
        if table_info:
            result = {
                "name": table_info.name,
                "full_name": table_info.full_name,
                "catalog_name": table_info.catalog_name,
                "schema_name": table_info.schema_name,
                "table_type": table_info.table_type,
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
            return f"Table not found: {table_name}" 