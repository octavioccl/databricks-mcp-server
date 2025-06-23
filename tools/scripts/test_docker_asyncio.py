#!/usr/bin/env python3
"""
Test script to verify asyncio behavior in Docker environment.
This script simulates the conditions that cause the "cannot be called from a running event loop" error.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_async_in_sync_context():
    """Test running async code from a sync context."""
    print("Testing async code in sync context...")
    
    try:
        # This should work fine
        await asyncio.sleep(0.1)
        print("✅ Async sleep worked")
        return True
    except Exception as e:
        print(f"❌ Async sleep failed: {e}")
        return False

def test_run_in_sync():
    """Test asyncio.run() in sync context."""
    print("Testing asyncio.run() in sync context...")
    
    try:
        result = asyncio.run(test_async_in_sync_context())
        print(f"✅ asyncio.run() worked: {result}")
        return True
    except RuntimeError as e:
        print(f"❌ asyncio.run() failed with RuntimeError: {e}")
        return False
    except Exception as e:
        print(f"❌ asyncio.run() failed with other error: {e}")
        return False

def test_new_loop_approach():
    """Test creating a new event loop."""
    print("Testing new event loop approach...")
    
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(test_async_in_sync_context())
            print(f"✅ New event loop worked: {result}")
            return True
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ New event loop failed: {e}")
        return False

def test_thread_approach():
    """Test running async code in a separate thread."""
    print("Testing thread approach...")
    
    import concurrent.futures
    import threading
    
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_async_in_sync_context())
        finally:
            loop.close()
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            result = future.result()
        print(f"✅ Thread approach worked: {result}")
        return True
    except Exception as e:
        print(f"❌ Thread approach failed: {e}")
        return False

def test_running_loop_detection():
    """Test detection of running event loops."""
    print("Testing running loop detection...")
    
    try:
        loop = asyncio.get_running_loop()
        print(f"⚠️  Running loop detected: {loop}")
        return True
    except RuntimeError:
        print("✅ No running loop detected")
        return False

async def test_nested_async():
    """Test what happens when we try to run asyncio.run() from within an async context."""
    print("Testing nested asyncio.run()...")
    
    try:
        # This should fail with "cannot be called from a running event loop"
        result = asyncio.run(test_async_in_sync_context())
        print(f"❌ Unexpected: nested asyncio.run() worked: {result}")
        return False
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            print(f"✅ Expected error caught: {e}")
            return True
        else:
            print(f"❌ Unexpected RuntimeError: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function."""
    print("=== Asyncio Behavior Test ===")
    print(f"Python version: {sys.version}")
    print(f"Running in Docker: {os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'}")
    print()
    
    # Test 1: Check if we're already in an event loop
    has_running_loop = test_running_loop_detection()
    print()
    
    # Test 2: Try asyncio.run() in sync context
    if not has_running_loop:
        test_run_in_sync()
        print()
    
    # Test 3: Try new event loop approach
    test_new_loop_approach()
    print()
    
    # Test 4: Try thread approach
    test_thread_approach()
    print()
    
    # Test 5: If we're not in an event loop, test nested behavior
    if not has_running_loop:
        print("Testing nested behavior...")
        try:
            asyncio.run(test_nested_async())
        except Exception as e:
            print(f"❌ Failed to test nested behavior: {e}")
        print()
    
    print("=== Test Complete ===")
    
    # Test the actual server import
    print("Testing server imports...")
    try:
        from databricks_mcp.server_fastmcp import mcp
        print("✅ Successfully imported FastMCP server")
        
        # Test client initialization (without connecting to Databricks)
        from databricks_mcp.config import DatabricksConfig
        print("✅ Successfully imported config")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ Other error during import: {e}")

if __name__ == "__main__":
    main() 