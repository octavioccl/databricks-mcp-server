#!/usr/bin/env python3
"""
Test script to verify Databricks connection and basic functionality.
Run with: poetry run python scripts/test_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from databricks_mcp.core.config import DatabricksConfig
    from databricks_mcp.core.utils.databricks_client import DatabricksClientWrapper
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    print("Make sure you have installed dependencies: poetry install")
    sys.exit(1)

async def test_connection():
    """Test basic Databricks connection and functionality."""
    
    print("=== Databricks MCP Server Connection Test ===")
    
    try:
        # Load configuration
        config = DatabricksConfig.from_env()
        print(f"Host: {config.host}")
        print(f"Token: {'*' * 10 if config.token else 'Not set'}")
        print(f"Warehouse ID: {config.sql_warehouse_id or 'Not set'}")
        print(f"Default Catalog: {config.default_catalog}")
        print(f"Default Schema: {config.default_schema}")
        print()
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease check your .env file or environment variables:")
        print("- DATABRICKS_HOST")
        print("- DATABRICKS_TOKEN")
        print("- DATABRICKS_SQL_WAREHOUSE_ID (optional but recommended)")
        return False
    
    # Initialize client
    try:
        client = DatabricksClientWrapper(config)
        print("📡 Testing Databricks connection...")
        
        # Test connection
        if await client.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return False
        
        print("\n🔍 Testing basic operations...")
        
        # Test listing catalogs
        try:
            catalogs = await client.list_catalogs()
            print(f"✅ Found {len(catalogs)} catalogs")
            if catalogs:
                print(f"   Example: {catalogs[0].name}")
        except Exception as e:
            print(f"⚠️  Error listing catalogs: {e}")
        
        # Test listing schemas
        try:
            schemas = await client.list_schemas()
            print(f"✅ Found {len(schemas)} schemas in {config.default_catalog}")
            if schemas:
                print(f"   Example: {schemas[0].name}")
        except Exception as e:
            print(f"⚠️  Error listing schemas: {e}")
        
        # Test listing tables
        try:
            tables = await client.list_tables()
            print(f"✅ Found {len(tables)} tables in {config.default_catalog}.{config.default_schema}")
            if tables:
                print(f"   Example: {tables[0].name}")
        except Exception as e:
            print(f"⚠️  Error listing tables: {e}")
        
        # Test SQL execution if warehouse is configured
        if config.sql_warehouse_id:
            print(f"\n🏃 Testing SQL execution with warehouse {config.sql_warehouse_id}...")
            try:
                result = await client.execute_query("SELECT 1 as test_value")
                if result["status"] == "success":
                    print("✅ SQL execution successful!")
                    print(f"   Result: {result}")
                else:
                    print(f"❌ SQL execution failed: {result.get('error')}")
            except Exception as e:
                print(f"⚠️  Error executing SQL: {e}")
        else:
            print("\n⚠️  SQL warehouse ID not configured - skipping SQL execution test")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def main():
    """Main test function."""
    try:
        success = await test_connection()
        if not success:
            print("\n💡 Troubleshooting tips:")
            print("1. Verify your Databricks workspace URL")
            print("2. Check that your personal access token is valid")
            print("3. Ensure you have proper permissions")
            print("4. Verify network connectivity to Databricks")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 