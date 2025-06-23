#!/usr/bin/env python3
"""
Databricks MCP Server - Main Entry Point

This redirects to the FastMCP server implementation.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for development
current_dir = Path(__file__).parent
src_root = current_dir.parent.parent
sys.path.insert(0, str(src_root))

def main():
    """Main entry point - redirects to FastMCP server."""
    print("🔄 Redirecting to FastMCP server...")
    
    try:
        # Import and run the FastMCP server
        from databricks_mcp.servers.main_fastmcp import main as fastmcp_main
        return fastmcp_main()
        
    except ImportError as e:
        print(f"❌ Failed to import FastMCP server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 