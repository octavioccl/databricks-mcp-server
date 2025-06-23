"""
SQL Query validator for safety checks.
"""

import re
import logging
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class QueryValidator:
    """Validates SQL queries for safety and security."""
    
    # Allowed SQL statement types (read-only operations)
    ALLOWED_STATEMENTS = {
        "SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN", "DESC"
    }
    
    # Dangerous keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        "DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER", 
        "TRUNCATE", "MERGE", "COPY", "IMPORT", "EXPORT", "GRANT", 
        "REVOKE", "SET", "CALL", "EXEC", "EXECUTE"
    }
    
    # System functions that might be dangerous
    DANGEROUS_FUNCTIONS = {
        "SYSTEM", "SHELL", "CMD", "EVAL", "EXECUTE"
    }
    
    def __init__(self):
        """Initialize the query validator."""
        self.max_query_length = 10000  # Maximum query length
        self.max_result_limit = 10000  # Maximum LIMIT value
    
    def is_safe_query(self, query: str) -> tuple[bool, Optional[str]]:
        """
        Check if a SQL query is safe for execution.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not query or not query.strip():
            return False, "Empty query not allowed"
        
        # Check query length
        if len(query) > self.max_query_length:
            return False, f"Query too long (max {self.max_query_length} characters)"
        
        # Clean and normalize query
        normalized_query = self._normalize_query(query)
        
        # Extract the main statement type
        statement_type = self._get_statement_type(normalized_query)
        
        if not statement_type:
            return False, "Unable to determine query type"
        
        # Check if statement type is allowed
        if statement_type not in self.ALLOWED_STATEMENTS:
            return False, f"Statement type '{statement_type}' not allowed"
        
        # Check for dangerous keywords
        dangerous_found = self._find_dangerous_keywords(normalized_query)
        if dangerous_found:
            return False, f"Dangerous keywords found: {', '.join(dangerous_found)}"
        
        # Check for dangerous functions
        dangerous_funcs = self._find_dangerous_functions(normalized_query)
        if dangerous_funcs:
            return False, f"Dangerous functions found: {', '.join(dangerous_funcs)}"
        
        # Check LIMIT clause if present
        limit_check = self._check_limit_clause(normalized_query)
        if not limit_check[0]:
            return False, limit_check[1]
        
        # Additional security checks
        security_check = self._additional_security_checks(normalized_query)
        if not security_check[0]:
            return False, security_check[1]
        
        logger.info(f"Query validated successfully: {statement_type}")
        return True, None
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for analysis."""
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        return query.upper()
    
    def _get_statement_type(self, query: str) -> Optional[str]:
        """Extract the main statement type from the query."""
        # Match the first SQL keyword
        match = re.match(r'\s*(\w+)', query)
        if match:
            return match.group(1).upper()
        return None
    
    def _find_dangerous_keywords(self, query: str) -> Set[str]:
        """Find dangerous keywords in the query."""
        found = set()
        words = re.findall(r'\b\w+\b', query)
        
        for word in words:
            if word.upper() in self.DANGEROUS_KEYWORDS:
                found.add(word.upper())
        
        return found
    
    def _find_dangerous_functions(self, query: str) -> Set[str]:
        """Find dangerous function calls in the query."""
        found = set()
        
        # Look for function calls pattern
        func_pattern = r'\b(\w+)\s*\('
        matches = re.findall(func_pattern, query)
        
        for func in matches:
            if func.upper() in self.DANGEROUS_FUNCTIONS:
                found.add(func.upper())
        
        return found
    
    def _check_limit_clause(self, query: str) -> tuple[bool, Optional[str]]:
        """Check LIMIT clause for reasonable values."""
        limit_pattern = r'\bLIMIT\s+(\d+)'
        matches = re.findall(limit_pattern, query)
        
        for limit_str in matches:
            try:
                limit_value = int(limit_str)
                if limit_value > self.max_result_limit:
                    return False, f"LIMIT value {limit_value} exceeds maximum allowed ({self.max_result_limit})"
            except ValueError:
                return False, f"Invalid LIMIT value: {limit_str}"
        
        return True, None
    
    def _additional_security_checks(self, query: str) -> tuple[bool, Optional[str]]:
        """Additional security checks."""
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\bUNION\s+ALL\s+SELECT.*FROM.*INFORMATION_SCHEMA',
            r'\bSELECT.*FROM.*INFORMATION_SCHEMA.*TABLES',
            r';\s*DROP',
            r';\s*DELETE',
            r';\s*INSERT',
            r'CONCAT\s*\(\s*CHAR\s*\(',
            r'EXEC\s*\(',
            r'EXECUTE\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Suspicious pattern detected: {pattern}"
        
        # Check for SQL injection attempts
        injection_patterns = [
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"'\s*OR\s*1\s*=\s*1",
            r"'\s*UNION\s+SELECT",
            r"'\s*;\s*DROP",
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Potential SQL injection attempt detected"
        
        return True, None
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize query by adding safety measures."""
        # Add LIMIT if not present in SELECT statements
        if query.strip().upper().startswith('SELECT') and 'LIMIT' not in query.upper():
            query = f"{query.rstrip(';')} LIMIT {min(1000, self.max_result_limit)}"
        
        return query
    
    def get_allowed_statements(self) -> List[str]:
        """Get list of allowed statement types."""
        return list(self.ALLOWED_STATEMENTS) 