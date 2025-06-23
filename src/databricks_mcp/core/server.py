#!/usr/bin/env python3
"""
Databricks MCP Server
Main server module with MCP protocol implementation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from .config import DatabricksConfig, MCPConfig
from .utils import DatabricksClientWrapper, QueryValidator, NaturalLanguageProcessor
from .tools import CatalogTools, QueryTools, NaturalLanguageTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabricksMCPServer:
    """Main Databricks MCP Server class."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.config = DatabricksConfig.from_env()
        self.mcp_config = MCPConfig.from_env()
        self.databricks_client = DatabricksClientWrapper(self.config)
        self.query_validator = QueryValidator()
        self.nl_processor = NaturalLanguageProcessor()
        
        # Initialize tool handlers
        self.catalog_tools = CatalogTools(self.databricks_client, self.config)
        self.query_tools = QueryTools(self.databricks_client, self.config, self.query_validator)
        self.nl_tools = NaturalLanguageTools(self.databricks_client, self.nl_processor, self.config)
        
        # Set up logging level
        logger.setLevel(getattr(logging, self.mcp_config.log_level.upper()))
        
        # Create MCP server instance
        self.server = Server(self.mcp_config.server_name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """Handle list tools request."""
            try:
                tools = []
                
                # Add catalog tools
                try:
                    catalog_tools = await self.catalog_tools.get_tools()
                    tools.extend(catalog_tools)
                    logger.debug(f"Added {len(catalog_tools)} catalog tools")
                except Exception as e:
                    logger.error(f"Error getting catalog tools: {e}")
                
                # Add query tools if enabled
                if self.mcp_config.enable_query_execution:
                    try:
                        query_tools = await self.query_tools.get_tools()
                        tools.extend(query_tools)
                        logger.debug(f"Added {len(query_tools)} query tools")
                    except Exception as e:
                        logger.error(f"Error getting query tools: {e}")
                
                # Add natural language tools if enabled
                if self.mcp_config.enable_natural_language:
                    try:
                        nl_tools = await self.nl_tools.get_tools()
                        tools.extend(nl_tools)
                        logger.debug(f"Added {len(nl_tools)} natural language tools")
                    except Exception as e:
                        logger.error(f"Error getting natural language tools: {e}")
                
                logger.info(f"Listed {len(tools)} available tools")
                return ListToolsResult(tools=tools)
            except Exception as e:
                logger.error(f"Error in handle_list_tools: {e}")
                # Return empty tools list on error to prevent server crash
                return ListToolsResult(tools=[])
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool call request."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                # Route to appropriate tool handler
                if name in await self.catalog_tools.get_tool_names():
                    result = await self.catalog_tools.handle_tool_call(name, arguments)
                elif name in await self.query_tools.get_tool_names():
                    result = await self.query_tools.handle_tool_call(name, arguments)
                elif name in await self.nl_tools.get_tool_names():
                    result = await self.nl_tools.handle_tool_call(name, arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                logger.info(f"Tool {name} executed successfully")
                return CallToolResult(content=[TextContent(type="text", text=result)])
                
            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )
    
    async def run(self):
        """Run the MCP server."""
        logger.info(f"Starting {self.mcp_config.server_name} v{self.mcp_config.server_version}")
        
        # Test Databricks connection
        if not await self.databricks_client.test_connection():
            logger.error("Failed to connect to Databricks. Please check your configuration.")
            return
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream, 
                InitializationOptions(
                    server_name=self.mcp_config.server_name,
                    server_version=self.mcp_config.server_version,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


# Global server instance for module-level access
_server_instance: Optional[DatabricksMCPServer] = None


def get_server() -> DatabricksMCPServer:
    """Get the global server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = DatabricksMCPServer()
    return _server_instance


async def main():
    """Main entry point for the server."""
    try:
        server = get_server()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 