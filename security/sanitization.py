"""
Security utilities for input sanitization and XSS prevention
"""

import html
import re
from typing import Any, Dict, List, Optional
import bleach
from markupsafe import Markup


class InputSanitizer:
    """Sanitizes user input to prevent XSS and injection attacks."""
    
    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br']
    
    # Allowed attributes
    ALLOWED_ATTRIBUTES = {}
    
    def __init__(self):
        """Initialize the sanitizer."""
        self.max_length = 10000  # Maximum input length
        self.patterns_to_remove = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'vbscript:',   # VBScript protocol
            r'on\w+\s*=',   # Event handlers (onclick, onload, etc.)
            r'data:text/html',  # Data URLs with HTML
        ]
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text input to prevent XSS.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text safe for display
        """
        if not isinstance(text, str):
            return str(text)
        
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length]
        
        # Remove dangerous patterns
        for pattern in self.patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML escape special characters
        text = html.escape(text, quote=True)
        
        # Remove any remaining HTML tags
        text = bleach.clean(text, tags=[], attributes={}, strip=True)
        
        return text.strip()
    
    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content allowing only safe tags.
        
        Args:
            html_content: HTML content to sanitize
            
        Returns:
            Sanitized HTML safe for display
        """
        if not isinstance(html_content, str):
            return str(html_content)
        
        # Truncate if too long
        if len(html_content) > self.max_length:
            html_content = html_content[:self.max_length]
        
        # Use bleach to clean HTML
        cleaned = bleach.clean(
            html_content,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively sanitize list values.
        
        Args:
            data: List to sanitize
            
        Returns:
            Sanitized list
        """
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_text(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def validate_message_length(self, message: str, max_length: int = 2000) -> bool:
        """
        Validate message length.
        
        Args:
            message: Message to validate
            max_length: Maximum allowed length
            
        Returns:
            True if valid, False otherwise
        """
        return len(message) <= max_length
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid email format, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_username(self, username: str) -> bool:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            True if valid username format, False otherwise
        """
        # Allow alphanumeric, underscore, hyphen, 3-30 characters
        pattern = r'^[a-zA-Z0-9_-]{3,30}$'
        return bool(re.match(pattern, username))


# Global sanitizer instance
sanitizer = InputSanitizer()


def sanitize_user_input(text: str) -> str:
    """
    Convenience function to sanitize user input.
    
    Args:
        text: User input text
        
    Returns:
        Sanitized text safe for processing
    """
    return sanitizer.sanitize_text(text)


def sanitize_for_logging(text: str) -> str:
    """
    Sanitize text for safe logging (removes sensitive patterns).
    
    Args:
        text: Text to sanitize for logging
        
    Returns:
        Sanitized text safe for logs
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove potential sensitive patterns
    patterns_to_mask = [
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',  # password: value
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',     # token: value
        r'key["\']?\s*[:=]\s*["\']?[^"\'\s]+',       # key: value
        r'secret["\']?\s*[:=]\s*["\']?[^"\'\s]+',   # secret: value
    ]
    
    sanitized = text
    for pattern in patterns_to_mask:
        sanitized = re.sub(pattern, r'\1=***MASKED***', sanitized, flags=re.IGNORECASE)
    
    # Truncate long messages
    if len(sanitized) > 500:
        sanitized = sanitized[:500] + "... [TRUNCATED]"
    
    return sanitized
