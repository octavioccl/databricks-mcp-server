"""
Natural language query tools for Databricks MCP Server.
"""

import json
import logging
from typing import Any, Dict, List

from mcp.types import Tool

logger = logging.getLogger(__name__)


class NaturalLanguageTools:
    """Tools for natural language to SQL conversion."""
    
    def __init__(self, databricks_client, nl_processor, config):
        """Initialize natural language tools."""
        self.client = databricks_client
        self.nl_processor = nl_processor
        self.config = config
    
    async def get_tools(self) -> List[Tool]:
        """Get list of available natural language tools."""
        return [
            Tool(
                name="generate_query_suggestions",
                description="Generate SQL query suggestions from natural language",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "request": {
                            "type": "string",
                            "description": "Natural language query request"
                        },
                        "tables": {
                            "type": "array",
                            "description": "Available tables to consider",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "full_name": {"type": "string"},
                                    "catalog": {"type": "string"},
                                    "schema": {"type": "string"}
                                }
                            }
                        },
                        "catalog": {
                            "type": "string",
                            "description": "Catalog to search in (optional)"
                        },
                        "schema": {
                            "type": "string", 
                            "description": "Schema to search in (optional)"
                        }
                    },
                    "required": ["request"]
                }
            ),
            Tool(
                name="search_tables",
                description="Search for tables matching a pattern",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (regex supported)"
                        },
                        "catalog": {
                            "type": "string",
                            "description": "Catalog to search in (optional)"
                        },
                        "schema": {
                            "type": "string",
                            "description": "Schema to search in (optional)"
                        }
                    },
                    "required": ["pattern"]
                }
            )
        ]
    
    async def get_tool_names(self) -> List[str]:
        """Get list of tool names."""
        tools = await self.get_tools()
        return [tool.name for tool in tools]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Handle a natural language tool call."""
        try:
            if name == "generate_query_suggestions":
                return await self._generate_query_suggestions(
                    arguments["request"],
                    arguments.get("tables", []),
                    arguments.get("catalog"),
                    arguments.get("schema")
                )
            elif name == "search_tables":
                return await self._search_tables(
                    arguments["pattern"],
                    arguments.get("catalog"),
                    arguments.get("schema")
                )
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            return f"Error: {str(e)}"
    
    async def _generate_query_suggestions(self, request: str, tables: List[Dict[str, Any]], 
                                        catalog: str = None, schema: str = None) -> str:
        """Generate SQL query suggestions from natural language."""
        # If no tables provided, try to get some from the specified or default catalog/schema
        if not tables:
            try:
                catalog_name = catalog or self.config.default_catalog
                schema_name = schema or self.config.default_schema
                table_objects = await self.client.list_tables(catalog_name, schema_name)
                tables = [
                    {
                        "name": table.name,
                        "full_name": table.full_name,
                        "catalog": table.catalog_name,
                        "schema": table.schema_name
                    }
                    for table in table_objects[:10]  # Limit to 10 tables
                ]
            except Exception as e:
                logger.warning(f"Could not retrieve tables: {e}")
                tables = []
        
        # Generate suggestions using the natural language processor
        suggestions = self.nl_processor.generate_sql_suggestions(request, tables)
        
        result = {
            "success": True,
            "request": request,
            "suggestions": suggestions,
            "table_count": len(tables),
            "suggestion_count": len(suggestions)
        }
        
        return json.dumps(result, indent=2)
    
    async def _search_tables(self, pattern: str, catalog: str = None, schema: str = None) -> str:
        """Search for tables matching a pattern."""
        import re
        
        try:
            # Get all tables from the specified or default catalog/schema
            catalog_name = catalog or self.config.default_catalog
            schema_name = schema or self.config.default_schema
            
            all_tables = await self.client.list_tables(catalog_name, schema_name)
            
            # Filter tables based on pattern
            matching_tables = []
            for table in all_tables:
                if re.search(pattern, table.name, re.IGNORECASE):
                    matching_tables.append({
                        "name": table.name,
                        "full_name": table.full_name,
                        "catalog": table.catalog_name,
                        "schema": table.schema_name,
                        "type": table.table_type
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