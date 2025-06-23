"""
Natural Language Processing utilities for Databricks MCP Server.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NaturalLanguageProcessor:
    """Process natural language queries and convert them to SQL."""
    
    def __init__(self):
        """Initialize the natural language processor."""
        self.query_patterns = {
            "count_records": [
                r"(?i).*how many.*records.*",
                r"(?i).*count.*records.*",
                r"(?i).*number of.*rows.*",
                r"(?i).*count.*rows.*"
            ],
            "show_structure": [
                r"(?i).*structure.*tables?.*",
                r"(?i).*schema.*tables?.*",
                r"(?i).*describe.*tables?.*",
                r"(?i).*columns.*tables?.*"
            ],
            "list_tables": [
                r"(?i).*list.*tables?.*",
                r"(?i).*show.*tables?.*",
                r"(?i).*available.*tables?.*"
            ],
            "sample_data": [
                r"(?i).*first.*rows.*",
                r"(?i).*sample.*data.*",
                r"(?i).*preview.*data.*",
                r"(?i).*show.*data.*"
            ]
        }
    
    def analyze_intent(self, query: str) -> str:
        """Analyze the intent of a natural language query."""
        for intent, patterns in self.query_patterns.items():
            for pattern in patterns:
                if re.match(pattern, query):
                    return intent
        return "general_query"
    
    def generate_sql_suggestions(self, query: str, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate SQL query suggestions based on natural language input."""
        intent = self.analyze_intent(query)
        suggestions = []
        
        if intent == "count_records":
            for table in tables[:5]:  # Limit to 5 tables
                suggestions.append({
                    "description": f"Count records in {table['full_name']}",
                    "query": f"SELECT COUNT(*) as record_count FROM {table['full_name']}",
                    "table": table['full_name'],
                    "confidence": 0.9
                })
        
        elif intent == "show_structure":
            for table in tables[:3]:  # Limit to 3 tables
                suggestions.append({
                    "description": f"Show structure of {table['full_name']}",
                    "query": f"DESCRIBE {table['full_name']}",
                    "table": table['full_name'],
                    "confidence": 0.9
                })
        
        elif intent == "list_tables":
            # This would typically show available tables
            catalog = tables[0]['catalog'] if tables else 'main'
            schema = tables[0]['schema'] if tables else 'default'
            suggestions.append({
                "description": f"List all tables in {catalog}.{schema}",
                "query": f"SHOW TABLES IN {catalog}.{schema}",
                "table": f"{catalog}.{schema}",
                "confidence": 0.8
            })
        
        elif intent == "sample_data":
            for table in tables[:3]:  # Limit to 3 tables
                suggestions.append({
                    "description": f"Show first 10 rows from {table['full_name']}",
                    "query": f"SELECT * FROM {table['full_name']} LIMIT 10",
                    "table": table['full_name'],
                    "confidence": 0.8
                })
        
        else:
            # General suggestions for unknown queries
            if tables:
                table = tables[0]
                suggestions.extend([
                    {
                        "description": f"Count records in {table['full_name']}",
                        "query": f"SELECT COUNT(*) FROM {table['full_name']}",
                        "table": table['full_name'],
                        "confidence": 0.5
                    },
                    {
                        "description": f"Sample data from {table['full_name']}",
                        "query": f"SELECT * FROM {table['full_name']} LIMIT 5",
                        "table": table['full_name'],
                        "confidence": 0.5
                    }
                ])
        
        return suggestions
    
    def extract_table_patterns(self, query: str) -> List[str]:
        """Extract table name patterns from natural language query."""
        patterns = []
        
        # Look for common table name patterns
        words = query.lower().split()
        
        # Common data-related terms that might indicate table types
        data_terms = [
            "user", "users", "customer", "customers",
            "order", "orders", "product", "products",
            "transaction", "transactions", "sale", "sales",
            "log", "logs", "event", "events",
            "fact", "dimension", "dim",
            "analytics", "report", "reports"
        ]
        
        for term in data_terms:
            if term in words:
                patterns.append(f".*{term}.*")
        
        return patterns
    
    def enhance_query_context(self, query: str, available_tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance query with context about available tables."""
        context = {
            "original_query": query,
            "intent": self.analyze_intent(query),
            "table_patterns": self.extract_table_patterns(query),
            "suggested_tables": [],
            "confidence": 0.0
        }
        
        # Find relevant tables based on patterns
        patterns = context["table_patterns"]
        for pattern in patterns:
            for table in available_tables:
                if re.search(pattern, table['name'], re.IGNORECASE):
                    context["suggested_tables"].append(table)
        
        # Set confidence based on matches found
        if context["suggested_tables"]:
            context["confidence"] = min(0.9, len(context["suggested_tables"]) * 0.3)
        
        return context 