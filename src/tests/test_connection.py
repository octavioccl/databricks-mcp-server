#!/usr/bin/env python3
"""
Test script to verify Databricks connection and basic functionality.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

# Load environment variables
load_dotenv()

async def test_connection():
    """Test basic Databricks connection and functionality."""
    
    # Check environment variables
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    
    print("=== Databricks MCP Server Connection Test ===")
    print(f"Host: {host}")
    print(f"Token: {'*' * 10 if token else 'Not set'}")
    print(f"Warehouse ID: {warehouse_id}")
    
    if not host or not token:
        print("❌ DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        return False
    
    try:
        # Initialize workspace client
        workspace = WorkspaceClient(host=host, token=token)
        
        # Test workspace access
        print("\n--- Testing workspace access ---")
        current_user = workspace.current_user.me()
        print(f"✅ Connected as: {current_user.user_name}")
        
        # Test SQL warehouse access if provided
        if warehouse_id:
            print("\n--- Testing SQL warehouse access ---")
            try:
                # Execute a simple query
                statement = workspace.statement_execution.execute_statement(
                    warehouse_id=warehouse_id,
                    statement="SELECT 1 as test_column",
                    wait_timeout="30s"
                )
                
                if statement.status.state.name == "SUCCEEDED":
                    print("✅ SQL warehouse connection successful")
                else:
                    print(f"❌ SQL warehouse query failed: {statement.status.error}")
                    return False
                    
            except Exception as e:
                print(f"❌ SQL warehouse connection failed: {e}")
                return False
        else:
            print("⚠️  DATABRICKS_SQL_WAREHOUSE_ID not set - SQL features will not work")
        
        # Test catalog access
        print("\n--- Testing catalog access ---")
        try:
            catalogs = list(workspace.catalogs.list())
            if catalogs:
                print(f"✅ Found {len(catalogs)} catalogs:")
                for catalog in catalogs[:3]:  # Show first 3
                    print(f"  - {catalog.name}")
                if len(catalogs) > 3:
                    print(f"  ... and {len(catalogs) - 3} more")
            else:
                print("⚠️  No catalogs found - check Unity Catalog access")
                
        except Exception as e:
            print(f"⚠️  Catalog access failed: {e}")
            print("   This is normal if Unity Catalog is not enabled")
        
        # Test clusters access
        print("\n--- Testing clusters access ---")
        try:
            clusters = list(workspace.clusters.list())
            if clusters:
                print(f"✅ Found {len(clusters)} clusters:")
                for cluster in clusters[:3]:  # Show first 3
                    print(f"  - {cluster.cluster_name} ({cluster.state})")
                if len(clusters) > 3:
                    print(f"  ... and {len(clusters) - 3} more")
            else:
                print("⚠️  No clusters found")
                
        except Exception as e:
            print(f"⚠️  Cluster access failed: {e}")
        
        print("\n=== Connection test completed successfully! ===")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function."""
    if not asyncio.run(test_connection()):
        sys.exit(1)
    
    print("\n🎉 Your Databricks MCP server is ready to use!")
    print("\nNext steps:")
    print("1. Configure your MCP client to use this server")
    print("2. Run: python main.py")
    print("3. Or use with Claude Desktop, Cursor, etc.")

if __name__ == "__main__":
    main() 