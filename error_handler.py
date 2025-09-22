"""
Rose AI Assistant Error Handling System
Provides comprehensive error handling, logging, and user feedback
"""

import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from datetime import datetime
import json

class RoseError(Exception):
    """Base exception for Rose AI Assistant"""
    pass

class APIConnectionError(RoseError):
    """API connection related errors"""
    pass

class ConfigurationError(RoseError):
    """Configuration related errors"""
    pass

class FeatureNotAvailableError(RoseError):
    """Feature not available errors"""
    pass

class ValidationError(RoseError):
    """Input validation errors"""
    pass

class ErrorHandler:
    """Centralized error handling and logging system"""
    
    def __init__(self, log_file: str = "rose_errors.log"):
        self.log_file = log_file
        self.setup_logging()
        self.error_count = 0
        self.last_error = None
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RoseAI')
    
    def handle_error(self, error: Exception, context: str = "", user_message: str = "") -> str:
        """Handle errors with logging and user feedback"""
        self.error_count += 1
        self.last_error = error
        
        # Log the error
        self.logger.error(f"Error in {context}: {str(error)}")
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Determine user-friendly message
        if user_message:
            return user_message
        
        # Generate appropriate user message based on error type
        if isinstance(error, APIConnectionError):
            return "I'm having trouble connecting to external services. Please check your internet connection."
        elif isinstance(error, ConfigurationError):
            return "There's a configuration issue. Please check your settings."
        elif isinstance(error, FeatureNotAvailableError):
            return "This feature is not available. Please install required dependencies."
        elif isinstance(error, ValidationError):
            return f"Invalid input: {str(error)}"
        elif isinstance(error, FileNotFoundError):
            return "Required file not found. Please check your installation."
        elif isinstance(error, PermissionError):
            return "Permission denied. Please check file permissions."
        else:
            return f"An unexpected error occurred: {str(error)}"
    
    def safe_execute(self, func: Callable, *args, context: str = "", fallback: Any = None, **kwargs) -> Any:
        """Safely execute a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = self.handle_error(e, context)
            if fallback is not None:
                return fallback
            raise RoseError(error_msg) from e
    
    def log_info(self, message: str, context: str = ""):
        """Log informational message"""
        self.logger.info(f"{context}: {message}")
    
    def log_warning(self, message: str, context: str = ""):
        """Log warning message"""
        self.logger.warning(f"{context}: {message}")
    
    def get_error_stats(self) -> dict:
        """Get error statistics"""
        return {
            "total_errors": self.error_count,
            "last_error": str(self.last_error) if self.last_error else None,
            "log_file": self.log_file
        }

def error_handler(context: str = "", fallback: Any = None):
    """Decorator for automatic error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler()
                error_msg = handler.handle_error(e, context)
                if fallback is not None:
                    return fallback
                raise RoseError(error_msg) from e
        return wrapper
    return decorator

def validate_input(value: Any, validation_type: str, context: str = "") -> bool:
    """Validate input based on type"""
    try:
        if validation_type == "email":
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, str(value)):
                raise ValidationError(f"Invalid email format: {value}")
        
        elif validation_type == "api_key":
            if not value or len(str(value)) < 10:
                raise ValidationError("API key appears to be invalid")
        
        elif validation_type == "file_path":
            from pathlib import Path
            if not Path(str(value)).exists():
                raise ValidationError(f"File not found: {value}")
        
        elif validation_type == "url":
            import re
            pattern = r'^https?://.+'
            if not re.match(pattern, str(value)):
                raise ValidationError(f"Invalid URL format: {value}")
        
        return True
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validation error for {validation_type}: {str(e)}")

# Global error handler instance
error_handler_instance = ErrorHandler()
