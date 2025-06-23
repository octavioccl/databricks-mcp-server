#!/usr/bin/env python3
"""
Databricks MCP Server - Standard MCP Entry Point

This is the entry point for the standard (legacy) MCP server implementation.
For the modern FastMCP server, use main_fastmcp.py instead.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path for development
current_dir = Path(__file__).parent
src_root = current_dir.parent.parent
sys.path.insert(0, str(src_root))

def main():
    """Main entry point for the standard MCP server."""
    try:
        # Import the standard MCP server
        from databricks_mcp.core.server import DatabricksMCPServer
        from databricks_mcp.core.config import DatabricksConfig
        
        print("🚀 Starting Databricks MCP Server (Standard)")
        
        # Load configuration
        config = DatabricksConfig.from_env()
        
        # Create and run server
        server = DatabricksMCPServer(config)
        
        # Run the server
        return server.run()
        
    except ImportError as e:
        print(f"❌ Failed to import server module: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1) 