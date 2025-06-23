#!/usr/bin/env python3
"""
Utility script to list available MCP tools and their descriptions.
Run with: poetry run python scripts/list_tools.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def list_tools():
    """List all available MCP tools."""
    try:
        from main import server
        
        # Get tools from server
        tools_result = await server.list_tools()()
        
        print("=== Available Databricks MCP Tools ===\n")
        
        for i, tool in enumerate(tools_result.tools, 1):
            print(f"{i}. {tool.name}")
            print(f"   Description: {tool.description}")
            
            # Show required parameters
            schema = tool.inputSchema
            if schema and schema.get("properties"):
                required = schema.get("required", [])
                properties = schema.get("properties", {})
                
                if required:
                    print("   Required parameters:")
                    for param in required:
                        if param in properties:
                            desc = properties[param].get("description", "No description")
                            print(f"     - {param}: {desc}")
                
                optional = [p for p in properties.keys() if p not in required]
                if optional:
                    print("   Optional parameters:")
                    for param in optional:
                        desc = properties[param].get("description", "No description")
                        print(f"     - {param}: {desc}")
            
            print()  # Empty line for readability
        
        print(f"Total tools available: {len(tools_result.tools)}")
        
    except Exception as e:
        print(f"Error listing tools: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(list_tools()) 