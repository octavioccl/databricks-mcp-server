#!/usr/bin/env python3
"""
Main CLI entry point for Databricks MCP Server.
This module is referenced by the package entry points.
"""

import sys
import os
import subprocess
from pathlib import Path

# Ensure the src directory is in the Python path
current_dir = Path(__file__).parent
src_root = current_dir.parent.parent
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

def main():
    """Main CLI entry point - delegates to the bin script or runs directly."""
    # Try to find and run the bin script first
    bin_script = src_root.parent / "bin" / "databricks-mcp-server"
    
    if bin_script.exists() and bin_script.is_file():
        # Run the bin script with the same arguments
        try:
            result = subprocess.run([str(bin_script)] + sys.argv[1:], 
                                   capture_output=False, 
                                   text=True)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Failed to run bin script: {e}")
            # Fall through to direct execution
    
    # Fallback - run directly using the server
    try:
        from databricks_mcp.servers.main import main as server_main
        server_main()
    except ImportError as e:
        print(f"❌ Failed to import server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("pip install fastmcp 'mcp[cli]' databricks-sdk")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 