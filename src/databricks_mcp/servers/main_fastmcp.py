#!/usr/bin/env python3
"""
FastMCP Entry Point for Databricks MCP Server
Fixed for Docker container asyncio event loop issues
"""

import sys
import asyncio
import signal
import os
from pathlib import Path

# Add the src directory to Python path for development
current_dir = Path(__file__).parent
src_root = current_dir.parent.parent
sys.path.insert(0, str(src_root))

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

async def run_server_async():
    """Run the FastMCP server in async mode."""
    try:
        # Import the FastMCP server instance
        from databricks_mcp.core.server_fastmcp import mcp
        
        print("🚀 Starting FastMCP server (async mode)...")
        # Use run_async() when we're already in an async context
        await mcp.run_async()
    except ImportError as e:
        print(f"❌ Failed to import FastMCP server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        raise
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

def run_server_sync():
    """Run the FastMCP server in sync mode."""
    try:
        # Import the FastMCP server instance
        from databricks_mcp.core.server_fastmcp import mcp
        
        print("🚀 Starting FastMCP server (sync mode)...")
        # Use run() when we're in a sync context
        mcp.run()
    except ImportError as e:
        print(f"❌ Failed to import FastMCP server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

def run_server_new_loop():
    """Run the server by creating a new event loop."""
    try:
        from databricks_mcp.core.server_fastmcp import mcp
        
        print("🚀 Starting FastMCP server (new event loop)...")
        
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the server in the new loop
            loop.run_until_complete(mcp.run_async())
        finally:
            # Clean up the loop
            loop.close()
            
    except ImportError as e:
        print(f"❌ Failed to import FastMCP server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

def detect_environment():
    """Detect the running environment and return appropriate startup method."""
    # Check if we're in Docker
    in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'
    
    # Check if there's already a running event loop
    try:
        loop = asyncio.get_running_loop()
        has_running_loop = True
        print("⚠️  Detected running event loop")
    except RuntimeError:
        has_running_loop = False
        print("✅ No event loop detected")
    
    # Determine the best approach
    if in_docker:
        print("🐳 Running in Docker container")
        if has_running_loop:
            print("💡 Using new event loop approach for Docker")
            return "new_loop"
        else:
            return "sync"
    else:
        print("🖥️  Running in local environment")
        if has_running_loop:
            print("💡 Running in async context - this may not work properly")
            return "new_loop"
        else:
            return "sync"

def main():
    """Main entry point for the FastMCP server."""
    # Setup signal handlers for graceful shutdown
    setup_signal_handlers()
    
    try:
        # Detect environment and choose appropriate startup method
        method = detect_environment()
        
        print(f"🔧 Using startup method: {method}")
        
        if method == "sync":
            run_server_sync()
        elif method == "async":
            # This should rarely be used
            asyncio.run(run_server_async())
        elif method == "new_loop":
            run_server_new_loop()
        else:
            print(f"❌ Unknown startup method: {method}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Import and run the FastMCP server
if __name__ == "__main__":
    main() 