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
    
    async def execute_statement(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SQL statement with advanced options."""
        try:
            statement = request_data.get("statement")
            warehouse_id = request_data.get("warehouse_id")
            wait_timeout = request_data.get("wait_timeout", "30s")
            catalog = request_data.get("catalog")
            schema = request_data.get("schema") 
            parameters = request_data.get("parameters")
            
            if not statement or not warehouse_id:
                return {
                    "status": "error",
                    "error": "Missing required parameters: statement and warehouse_id"
                }
            
            # Execute the statement
            statement_result = await asyncio.to_thread(
                lambda: self.client.statement_execution.execute_statement(
                    warehouse_id=warehouse_id,
                    statement=statement,
                    wait_timeout=wait_timeout,
                    catalog=catalog,
                    schema=schema,
                    parameters=parameters
                )
            )
            
            # Wait for completion
            while statement_result.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                await asyncio.sleep(0.5)
                statement_result = await asyncio.to_thread(
                    lambda: self.client.statement_execution.get_statement(statement_result.statement_id)
                )
            
            if statement_result.status.state == StatementState.SUCCEEDED:
                result = statement_result.result
                return {
                    "status": "success",
                    "statement_id": statement_result.statement_id,
                    "data": result.data_array if result else [],
                    "row_count": result.row_count if result else 0,
                    "state": str(statement_result.status.state)
                }
            else:
                error_msg = statement_result.status.error.message if statement_result.status.error else "Unknown error"
                return {
                    "status": "error",
                    "error": error_msg,
                    "statement_id": statement_result.statement_id,
                    "state": str(statement_result.status.state)
                }
                
        except Exception as e:
            logger.error(f"Error executing statement: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def list_clusters(self) -> Dict[str, Any]:
        """List all clusters in the workspace."""
        try:
            clusters = await asyncio.to_thread(
                lambda: list(self.client.clusters.list())
            )
            
            cluster_list = []
            for cluster in clusters:
                cluster_list.append({
                    "cluster_id": cluster.cluster_id,
                    "cluster_name": cluster.cluster_name,
                    "state": str(cluster.state),
                    "node_type_id": cluster.node_type_id,
                    "num_workers": cluster.num_workers,
                    "spark_version": cluster.spark_version
                })
            
            return {
                "status": "success",
                "clusters": cluster_list,
                "count": len(cluster_list)
            }
        except Exception as e:
            logger.error(f"Error listing clusters: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific cluster."""
        try:
            cluster = await asyncio.to_thread(
                lambda: self.client.clusters.get(cluster_id)
            )
            
            return {
                "status": "success",
                "cluster": {
                    "cluster_id": cluster.cluster_id,
                    "cluster_name": cluster.cluster_name,
                    "state": str(cluster.state),
                    "node_type_id": cluster.node_type_id,
                    "num_workers": cluster.num_workers,
                    "spark_version": cluster.spark_version,
                    "driver": cluster.driver.as_dict() if cluster.driver else None,
                    "executors": [executor.as_dict() for executor in cluster.executors] if cluster.executors else []
                }
            }
        except Exception as e:
            logger.error(f"Error getting cluster: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def create_cluster(self, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new cluster."""
        try:
            response = await asyncio.to_thread(
                lambda: self.client.clusters.create(**cluster_config)
            )
            
            return {
                "status": "success",
                "cluster_id": response.cluster_id,
                "message": "Cluster creation initiated"
            }
        except Exception as e:
            logger.error(f"Error creating cluster: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def start_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Start a cluster."""
        try:
            await asyncio.to_thread(
                lambda: self.client.clusters.start(cluster_id)
            )
            
            return {
                "status": "success",
                "cluster_id": cluster_id,
                "message": "Cluster start initiated"
            }
        except Exception as e:
            logger.error(f"Error starting cluster: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def terminate_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Terminate a cluster."""
        try:
            await asyncio.to_thread(
                lambda: self.client.clusters.delete(cluster_id)
            )
            
            return {
                "status": "success",
                "cluster_id": cluster_id,
                "message": "Cluster termination initiated"
            }
        except Exception as e:
            logger.error(f"Error terminating cluster: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def restart_cluster(self, cluster_id: str) -> Dict[str, Any]:
        """Restart a cluster."""
        try:
            await asyncio.to_thread(
                lambda: self.client.clusters.restart(cluster_id)
            )
            
            return {
                "status": "success", 
                "cluster_id": cluster_id,
                "message": "Cluster restart initiated"
            }
        except Exception as e:
            logger.error(f"Error restarting cluster: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def list_jobs(self, limit: int = 25, offset: int = 0, expand_tasks: bool = False) -> Dict[str, Any]:
        """List all jobs in the workspace."""
        try:
            jobs = await asyncio.to_thread(
                lambda: self.client.jobs.list(limit=limit, offset=offset, expand_tasks=expand_tasks)
            )
            
            job_list = []
            for job in jobs:
                job_list.append({
                    "job_id": job.job_id,
                    "settings": job.settings.as_dict() if job.settings else None,
                    "created_time": job.created_time,
                    "creator_user_name": job.creator_user_name
                })
            
            return {
                "status": "success",
                "jobs": job_list,
                "count": len(job_list)
            }
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_job(self, job_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific job."""
        try:
            job = await asyncio.to_thread(
                lambda: self.client.jobs.get(job_id)
            )
            
            return {
                "status": "success",
                "job": {
                    "job_id": job.job_id,
                    "settings": job.settings.as_dict() if job.settings else None,
                    "created_time": job.created_time,
                    "creator_user_name": job.creator_user_name
                }
            }
        except Exception as e:
            logger.error(f"Error getting job: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_job(self, job_id: int, run_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a job now."""
        try:
            response = await asyncio.to_thread(
                lambda: self.client.jobs.run_now(job_id, **run_params)
            )
            
            return {
                "status": "success",
                "run_id": response.run_id,
                "message": "Job run initiated"
            }
        except Exception as e:
            logger.error(f"Error running job: {e}")
            return {
                "status": "error",
                "error": str(e)
            } 