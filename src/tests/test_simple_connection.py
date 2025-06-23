#!/usr/bin/env python3
"""
Simplified test script to verify Databricks connection and basic functionality.
This version works independently without the MCP server infrastructure.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_simple_connection():
    """Test basic Databricks connection and functionality."""
    
    # Check environment variables
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    
    print("=== Simple Databricks Connection Test ===")
    print(f"Host: {host}")
    print(f"Token: {'*' * 10 if token else 'Not set'}")
    print(f"Warehouse ID: {warehouse_id}")
    
    if not host or not token:
        print("❌ DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env file")
        print("   Please copy config.env.example to .env and fill in your credentials")
        return False
    
    try:
        # Direct import without complex MCP infrastructure
        from databricks_mcp.config import DatabricksConfig
        from databricks_mcp.utils.databricks_client import DatabricksClientWrapper
        
        # Initialize configuration and client
        config = DatabricksConfig.from_env()
        client = DatabricksClientWrapper(config)
        
        print("\n--- Testing Databricks connection ---")
        
        # Test connection
        if await client.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed")
            return False
        
        # Test catalog listing
        print("\n--- Testing catalog access ---")
        try:
            catalogs = await client.list_catalogs()
            if catalogs:
                print(f"✅ Found {len(catalogs)} catalogs:")
                for catalog in catalogs[:5]:  # Show first 5
                    print(f"  - {catalog.name}")
                if len(catalogs) > 5:
                    print(f"  ... and {len(catalogs) - 5} more")
            else:
                print("⚠️  No catalogs found")
        except Exception as e:
            print(f"⚠️  Error accessing catalogs: {e}")
        
        # Test schema listing (using first catalog if available)
        if catalogs:
            print(f"\n--- Testing schema access for catalog '{catalogs[0].name}' ---")
            try:
                schemas = await client.list_schemas(catalogs[0].name)
                if schemas:
                    print(f"✅ Found {len(schemas)} schemas:")
                    for schema in schemas[:3]:  # Show first 3
                        print(f"  - {schema.name}")
                    if len(schemas) > 3:
                        print(f"  ... and {len(schemas) - 3} more")
                else:
                    print("⚠️  No schemas found")
            except Exception as e:
                print(f"⚠️  Error accessing schemas: {e}")
        
        # Test table listing (using first catalog and schema if available)
        if catalogs and schemas:
            print(f"\n--- Testing table access for '{catalogs[0].name}.{schemas[0].name}' ---")
            try:
                tables = await client.list_tables(catalogs[0].name, schemas[0].name)
                if tables:
                    print(f"✅ Found {len(tables)} tables:")
                    for table in tables[:3]:  # Show first 3
                        print(f"  - {table.name} ({table.table_type})")
                    if len(tables) > 3:
                        print(f"  ... and {len(tables) - 3} more")
                else:
                    print("⚠️  No tables found in this schema")
            except Exception as e:
                print(f"⚠️  Error accessing tables: {e}")
        
        # Test SQL execution if warehouse is configured
        if warehouse_id and warehouse_id != "your_sql_warehouse_id":
            print(f"\n--- Testing SQL execution ---")
            try:
                result = await client.execute_query("SELECT 1 as test_column, 'Hello Databricks' as message")
                if result.get("status") == "success":
                    print("✅ SQL execution successful!")
                    print(f"   Query returned {result.get('row_count', 0)} rows")
                    if result.get("data"):
                        print(f"   Sample data: {result['data'][0] if result['data'] else 'No data'}")
                else:
                    print(f"❌ SQL execution failed: {result.get('error')}")
            except Exception as e:
                print(f"❌ SQL execution error: {e}")
        else:
            print("\n⚠️  SQL warehouse ID not configured - skipping SQL execution test")
        
        print("\n=== Test completed successfully! ===")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you've installed dependencies with: poetry install")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function."""
    success = asyncio.run(test_simple_connection())
    
    if success:
        print("\n🎉 Your Databricks setup is working!")
        print("\nNext steps:")
        print("1. Configure your MCP client to use this server")
        print("2. Run the full MCP server: poetry run python main.py")
        print("3. Test with the natural language example (after configuring real credentials)")
    else:
        print("\n❌ Please fix the connection issues and try again")
        sys.exit(1)

if __name__ == "__main__":
    main() 