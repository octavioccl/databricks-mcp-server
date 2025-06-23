#!/usr/bin/env python3
"""
Working example script demonstrating natural language query generation with Databricks MCP Server.
This version works directly with the client modules.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def demonstrate_natural_language_queries():
    """Demonstrate natural language query generation."""
    
    try:
        # Import the client directly
        from databricks_mcp.config import DatabricksConfig
        from databricks_mcp.utils.databricks_client import DatabricksClientWrapper
        from databricks_mcp.utils.natural_language import NaturalLanguageProcessor
        
        print("=== Databricks Natural Language Query Demo ===\n")
        
        # Initialize configuration and client
        config = DatabricksConfig.from_env()
        client = DatabricksClientWrapper(config)
        nl_processor = NaturalLanguageProcessor()
        
        # Test connection first
        if not await client.test_connection():
            print("❌ Connection failed. Please check your credentials.")
            return
        
        # Example natural language requests
        requests = [
            "How many records are in each table?",
            "Show me the structure of all tables",
            "List the first few rows from each table",
            "Count records by table",
            "Show table schemas",
        ]
        
        print("🔍 Discovering available tables...")
        
        # Get some sample tables
        catalogs = await client.list_catalogs()
        if not catalogs:
            print("❌ No catalogs found. Please check your Databricks connection.")
            return
        
        print(f"Found {len(catalogs)} catalogs:")
        for catalog in catalogs[:3]:
            print(f"  - {catalog.name}")
        
        # Get tables from first catalog
        first_catalog = catalogs[0].name
        schemas = await client.list_schemas(first_catalog)
        
        sample_tables = []
        if schemas:
            first_schema = schemas[0].name
            tables = await client.list_tables(first_catalog, first_schema)
            sample_tables = [
                {
                    "name": table.name,
                    "full_name": table.full_name,
                    "catalog": table.catalog_name,
                    "schema": table.schema_name
                }
                for table in tables[:5]  # Limit to 5 tables for demo
            ]
        
        if not sample_tables:
            print("❌ No tables found. Creating some example suggestions...")
            # Create example suggestions without real tables
            sample_tables = [
                {"name": "users", "full_name": "main.default.users", "catalog": "main", "schema": "default"},
                {"name": "orders", "full_name": "main.default.orders", "catalog": "main", "schema": "default"},
                {"name": "products", "full_name": "main.default.products", "catalog": "main", "schema": "default"}
            ]
        
        print(f"\n📊 Using sample tables from {first_catalog}.{first_schema}:")
        for table in sample_tables:
            print(f"  - {table['full_name']}")
        
        print("\n🤖 Generating natural language query suggestions...\n")
        
        # Test each natural language request
        for i, request in enumerate(requests, 1):
            print(f"{i}. Request: \"{request}\"")
            print("   " + "="*50)
            
            try:
                # Use the natural language processor directly
                suggestions = nl_processor.generate_sql_suggestions(request, sample_tables)
                
                if suggestions:
                    print(f"   Generated {len(suggestions)} suggestions:")
                    for j, suggestion in enumerate(suggestions[:3], 1):  # Show top 3
                        print(f"     {j}. {suggestion['description']}")
                        print(f"        Query: {suggestion['query']}")
                        print(f"        Table: {suggestion['table']}")
                        print(f"        Confidence: {suggestion['confidence']}")
                        print()
                else:
                    print("   No suggestions generated")
            
            except Exception as e:
                print(f"   Error generating suggestions: {e}")
            
            print()
        
        print("🎯 Advanced Example: Intent Analysis")
        print("="*50)
        
        # Test intent analysis
        test_queries = [
            "Count all records in the catalog table",
            "Describe the structure of the products table", 
            "Show me the first 10 rows from markdowns_from_catalog",
            "What tables are available in this schema?"
        ]
        
        for query in test_queries:
            intent = nl_processor.analyze_intent(query)
            patterns = nl_processor.extract_table_patterns(query)
            
            print(f"\nQuery: \"{query}\"")
            print(f"  Intent: {intent}")
            print(f"  Table patterns: {patterns}")
        
        print("\n✨ Try these natural language requests with your MCP client:")
        example_requests = [
            "Find all tables containing catalog data",
            "Show me the schema of the largest tables",
            "Generate a query to count records in each table",
            "What are the available product tables?",
            "Count records in all consumer-related tables",
            "Show me tables related to markdowns",
        ]
        
        for request in example_requests:
            print(f"  • \"{request}\"")
        
        print(f"\n🎉 Demo completed! The natural language processor can understand queries")
        print("   and generate appropriate SQL for your Databricks tables.")
        print(f"\nYour Databricks workspace has:")
        print(f"  - {len(catalogs)} catalogs")
        print(f"  - {len(schemas)} schemas in '{first_catalog}'")
        print(f"  - {len(sample_tables)} tables available for queries")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def main():
    """Main function."""
    # Check if required environment variables are set
    if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
        print("❌ Please set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables")
        print("   Copy config.env.example to .env and fill in your credentials")
        sys.exit(1)
    
    await demonstrate_natural_language_queries()

if __name__ == "__main__":
    asyncio.run(main()) 