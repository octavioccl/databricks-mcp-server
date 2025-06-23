"""
Databricks client wrapper with enhanced functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import ExecuteStatementRequest, StatementState
from databricks.sdk.service.catalog import CatalogInfo, SchemaInfo, TableInfo

from ..config import DatabricksConfig

logger = logging.getLogger(__name__)


class DatabricksClientWrapper:
    """Wrapper around Databricks SDK with async support and caching."""
    
    def __init__(self, config: DatabricksConfig, query_timeout: int = 30):
        """Initialize the Databricks client wrapper."""
        self.config = config
        self.query_timeout = min(max(query_timeout, 5), 50)  # Clamp between 5-50 seconds
        self.client = WorkspaceClient(
            host=config.host,
            token=config.token
        )
        self._catalog_cache: Optional[List[CatalogInfo]] = None
        self._schema_cache: Dict[str, List[SchemaInfo]] = {}
        self._table_cache: Dict[Tuple[str, str], List[TableInfo]] = {}
    
    async def test_connection(self) -> bool:
        """Test the Databricks connection."""
        try:
            # Try to list catalogs as a connection test
            await self.list_catalogs()
            logger.info("✅ Databricks connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Databricks connection failed: {e}")
            return False
    
    async def list_catalogs(self) -> List[CatalogInfo]:
        """List all catalogs with caching."""
        if self._catalog_cache is None:
            try:
                # Run the synchronous call in a thread pool to avoid blocking
                catalogs = await asyncio.to_thread(
                    lambda: list(self.client.catalogs.list())
                )
                self._catalog_cache = catalogs
                logger.info(f"Retrieved {len(catalogs)} catalogs")
            except Exception as e:
                logger.error(f"Error listing catalogs: {e}")
                raise
        
        return self._catalog_cache
    
    async def list_schemas(self, catalog: Optional[str] = None) -> List[SchemaInfo]:
        """List schemas in a catalog with caching."""
        catalog_name = catalog or self.config.default_catalog
        
        if catalog_name not in self._schema_cache:
            try:
                schemas = await asyncio.to_thread(
                    lambda: list(self.client.schemas.list(catalog_name=catalog_name))
                )
                self._schema_cache[catalog_name] = schemas
                logger.info(f"Retrieved {len(schemas)} schemas for catalog {catalog_name}")
            except Exception as e:
                logger.error(f"Error listing schemas for catalog {catalog_name}: {e}")
                raise
        
        return self._schema_cache[catalog_name]
    
    async def list_tables(self, catalog: Optional[str] = None, schema: Optional[str] = None) -> List[TableInfo]:
        """List tables in a schema with caching."""
        catalog_name = catalog or self.config.default_catalog
        schema_name = schema or self.config.default_schema
        cache_key = (catalog_name, schema_name)
        
        if cache_key not in self._table_cache:
            try:
                tables = await asyncio.to_thread(
                    lambda: list(self.client.tables.list(
                        catalog_name=catalog_name,
                        schema_name=schema_name
                    ))
                )
                self._table_cache[cache_key] = tables
                logger.info(f"Retrieved {len(tables)} tables for {catalog_name}.{schema_name}")
            except Exception as e:
                logger.error(f"Error listing tables for {catalog_name}.{schema_name}: {e}")
                raise
        
        return self._table_cache[cache_key]
    
    async def get_table_info(self, table_name: str, catalog: Optional[str] = None, schema: Optional[str] = None) -> Optional[TableInfo]:
        """Get detailed information about a specific table."""
        # Parse full table name if provided
        parts = table_name.split(".")
        if len(parts) == 3:
            catalog, schema, table_name = parts
        elif len(parts) == 2:
            schema, table_name = parts
        
        catalog_name = catalog or self.config.default_catalog
        schema_name = schema or self.config.default_schema
        
        try:
            table_info = await asyncio.to_thread(
                lambda: self.client.tables.get(
                    full_name=f"{catalog_name}.{schema_name}.{table_name}"
                )
            )
            logger.info(f"Retrieved table info for {catalog_name}.{schema_name}.{table_name}")
            return table_info
        except Exception as e:
            logger.error(f"Error getting table info for {catalog_name}.{schema_name}.{table_name}: {e}")
            return None
    
    async def execute_query(self, query: str, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a SQL query."""
        warehouse = warehouse_id or self.config.sql_warehouse_id
        if not warehouse:
            raise ValueError("SQL warehouse ID must be provided")
        
        try:
            # Execute the query
            statement = await asyncio.to_thread(
                lambda: self.client.statement_execution.execute_statement(
                    warehouse_id=warehouse,
                    statement=query,
                    wait_timeout=f"{self.query_timeout}s"
                )
            )
            
            # Wait for completion
            while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                await asyncio.sleep(0.5)
                statement = await asyncio.to_thread(
                    lambda: self.client.statement_execution.get_statement(statement.statement_id)
                )
            
            if statement.status.state == StatementState.SUCCEEDED:
                result = statement.result
                logger.info(f"Query executed successfully, returned {result.row_count if result else 0} rows")
                return {
                    "status": "success",
                    "data": result.data_array if result else [],
                    "row_count": result.row_count if result else 0
                }
            else:
                error_msg = statement.status.error.message if statement.status.error else "Unknown error"
                logger.error(f"Query failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def clear_cache(self):
        """Clear all cached data."""
        self._catalog_cache = None
        self._schema_cache.clear()
        self._table_cache.clear()
        logger.info("Cache cleared") 