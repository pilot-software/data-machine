import re
import html
from typing import Optional

class InputSanitizer:
    """Input sanitization utilities"""
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """Sanitize search query input"""
        if not query:
            return ""
        
        # Remove HTML entities
        query = html.unescape(query)
        
        # Remove dangerous characters
        query = re.sub(r'[<>"\';\\%_]', '', query)
        
        # Remove SQL injection patterns
        query = re.sub(r'\b(union|select|insert|update|delete|drop|create|alter)\b', '', query, flags=re.IGNORECASE)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        return query[:100]  # Limit length
    
    @staticmethod
    def sanitize_code(code: str) -> str:
        """Sanitize medical code input"""
        if not code:
            return ""
        
        # Allow only alphanumeric, dots, and hyphens
        sanitized = re.sub(r'[^A-Za-z0-9\.\-]', '', code.strip().upper())
        
        return sanitized[:20]  # Limit length
    
    @staticmethod
    def sanitize_chapter(chapter: Optional[str]) -> Optional[str]:
        """Sanitize chapter filter input"""
        if not chapter:
            return None
        
        # Allow only alphanumeric, hyphens, and dots
        sanitized = re.sub(r'[^A-Za-z0-9\-\.]', '', chapter.strip())
        
        return sanitized[:20] if sanitized else None

# Global sanitizer instance
sanitizer = InputSanitizer()