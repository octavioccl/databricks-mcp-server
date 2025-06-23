"""
Query execution tools for Databricks MCP Server.
"""

import json
import logging
from typing import Any, Dict, List

from mcp.types import Tool

logger = logging.getLogger(__name__)


class QueryTools:
    """Tools for executing SQL queries in Databricks."""
    
    def __init__(self, databricks_client, config, query_validator):
        """Initialize query tools."""
        self.client = databricks_client
        self.config = config
        self.validator = query_validator
    
    async def get_tools(self) -> List[Tool]:
        """Get list of available query tools."""
        return [
            Tool(
                name="execute_query",
                description="Execute a SQL query in Databricks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "warehouse_id": {
                            "type": "string",
                            "description": "SQL warehouse ID (optional, uses default if not provided)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    
    async def get_tool_names(self) -> List[str]:
        """Get list of tool names."""
        tools = await self.get_tools()
        return [tool.name for tool in tools]
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> str:
        """Handle a query tool call."""
        try:
            if name == "execute_query":
                return await self._execute_query(
                    arguments["query"],
                    arguments.get("warehouse_id"),
                    arguments.get("limit", 100)
                )
            else:
                return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            return f"Error: {str(e)}"
    
    async def _execute_query(self, query: str, warehouse_id: str = None, limit: int = 100) -> str:
        """Execute a SQL query."""
        # Validate the query
        validation_result = self.validator.validate_query(query)
        if not validation_result["is_valid"]:
            return json.dumps({
                "status": "error",
                "error": f"Query validation failed: {validation_result['reason']}"
            }, indent=2)
        
        # Add LIMIT clause if not present and this is a SELECT query
        processed_query = self._add_limit_if_needed(query, limit)
        
        # Execute the query
        result = await self.client.execute_query(processed_query, warehouse_id)
        
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
    
    def _add_limit_if_needed(self, query: str, limit: int) -> str:
        """Add LIMIT clause to SELECT queries if not already present."""
        query_upper = query.upper().strip()
        if query_upper.startswith("SELECT") and "LIMIT" not in query_upper:
            return f"{query.rstrip(';')} LIMIT {limit}"
        return query 