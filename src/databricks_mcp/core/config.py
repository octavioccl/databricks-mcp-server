"""
Configuration management for Databricks MCP Server.
"""

import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabricksConfig:
    """Configuration for Databricks connection."""
    
    host: str
    token: str
    sql_warehouse_id: Optional[str] = None
    default_catalog: str = "main"
    default_schema: str = "default"
    cluster_id: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "DatabricksConfig":
        """Create config from environment variables."""
        host = os.getenv("DATABRICKS_HOST")
        if not host:
            raise ValueError("DATABRICKS_HOST environment variable is required")
        
        token = os.getenv("DATABRICKS_TOKEN")
        if not token:
            raise ValueError("DATABRICKS_TOKEN environment variable is required")
        
        return cls(
            host=host,
            token=token,
            sql_warehouse_id=os.getenv("DATABRICKS_SQL_WAREHOUSE_ID"),
            default_catalog=os.getenv("DEFAULT_CATALOG", "main"),
            default_schema=os.getenv("DEFAULT_SCHEMA", "default"),
            cluster_id=os.getenv("DATABRICKS_CLUSTER_ID")
        )
    
    def validate(self) -> bool:
        """Validate the configuration."""
        if not self.host or not self.token:
            return False
        
        if not self.host.startswith(("http://", "https://")):
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "host": self.host,
            "token": "***" if self.token else None,  # Hide token in logs
            "sql_warehouse_id": self.sql_warehouse_id,
            "default_catalog": self.default_catalog,
            "default_schema": self.default_schema,
            "cluster_id": self.cluster_id
        }


@dataclass 
class MCPConfig:
    """Configuration for MCP Server."""
    
    server_name: str = "databricks-mcp"
    server_version: str = "1.0.0"
    log_level: str = "INFO"
    max_results: int = 1000
    query_timeout: int = 300  # seconds
    enable_caching: bool = True
    cache_ttl: int = 3600  # seconds
    enable_query_validation: bool = True
    allowed_sql_operations: list = field(default_factory=lambda: [
        "SELECT", "SHOW", "DESCRIBE", "EXPLAIN"
    ])
    
    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create MCP config from environment variables."""
        return cls(
            server_name=os.getenv("MCP_SERVER_NAME", "databricks-mcp"),
            server_version=os.getenv("MCP_SERVER_VERSION", "1.0.0"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_results=int(os.getenv("MAX_RESULTS", "1000")),
            query_timeout=int(os.getenv("QUERY_TIMEOUT", "300")),
            enable_caching=os.getenv("ENABLE_CACHING", "true").lower() == "true",
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            enable_query_validation=os.getenv("ENABLE_QUERY_VALIDATION", "true").lower() == "true"
        )
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "server_name": self.server_name,
            "server_version": self.server_version,
            "log_level": self.log_level,
            "max_results": self.max_results,
            "query_timeout": self.query_timeout,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "enable_query_validation": self.enable_query_validation,
            "allowed_sql_operations": self.allowed_sql_operations
        } 