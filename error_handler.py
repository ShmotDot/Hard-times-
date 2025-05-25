"""
Enhanced error handling module for Hard Times: Ottawa.
Provides centralized error logging, validation, and handling.
"""
import logging
import os
import traceback
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union, Tuple

class ValidationError(Exception):
    """Exception raised for data validation errors."""
    pass

class StateError(Exception):
    """Exception for invalid state errors."""
    pass

class GameError(Exception):
    """Base exception for game errors."""
    pass

class ErrorHandler:
    """Centralized error handler with enhanced logging and validation."""
    
    def __init__(self, log_file='game_errors.log'):
        self.log_file = log_file
        
        # Set up enhanced logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,  # Capture more detailed logs
            format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create console handler for immediate feedback
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        logging.getLogger('').addHandler(console)
        
        # Initialize error counts for monitoring
        self.error_counts: Dict[str, int] = {}
        
    def validate_data(self, data: Any, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate data against a schema.
        
        Args:
            data: Data to validate
            schema: Validation schema
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not isinstance(data, type(schema.get('type', type(None)))):
                return False, f"Type mismatch: expected {schema['type']}, got {type(data)}"
                
            if 'min' in schema and data < schema['min']:
                return False, f"Value {data} below minimum {schema['min']}"
                
            if 'max' in schema and data > schema['max']:
                return False, f"Value {data} above maximum {schema['max']}"
                
            if 'required_fields' in schema:
                missing = [f for f in schema['required_fields'] if f not in data]
                if missing:
                    return False, f"Missing required fields: {', '.join(missing)}"
                    
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None, severity: str = "error") -> str:
        """Enhanced error handling with detailed logging.
        
        Args:
            error: The exception that occurred
            context: Optional dictionary with contextual information
            severity: Logging level ("debug", "info", "warning", "error", "critical")
            
        Returns:
            str: User-friendly error message
        """
        error_type = error.__class__.__name__
        
        # Add stack info for severe errors
        include_stack = severity in ("error", "critical")
        
        # Track error frequency
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Get detailed error info
        stack_trace = traceback.format_exc()
        error_time = datetime.now().isoformat()
        
        # User-friendly messages
        friendly_messages = {
            "ValueError": "Invalid value provided",
            "TypeError": "Incorrect type of data used",
            "IndexError": "Tried to access non-existent data",
            "KeyError": "Required information is missing",
            "AttributeError": "Tried to use unavailable feature",
            "ValidationError": "Data validation failed",
            "StateError": "Invalid game state",
            "GameError": "Game system error",
            "ZeroDivisionError": "Calculation error: division by zero"
        }
        
        friendly_message = friendly_messages.get(error_type, "An unexpected error occurred")
        
        # Format detailed error message
        error_details = {
            "time": error_time,
            "type": error_type,
            "message": str(error),
            "context": context or {},
            "stack_trace": stack_trace
        }
        
        # Log the error with different severity levels
        logger = logging.getLogger('game')
        if error_type in ["ValidationError", "ValueError"]:
            logger.warning(json.dumps(error_details))
        else:
            logger.error(json.dumps(error_details))
            
        # Alert on frequent errors
        if self.error_counts[error_type] >= 5:
            logger.critical(f"Frequent {error_type} errors detected: {self.error_counts[error_type]} occurrences")
            
        return f"Error: {friendly_message} - {str(error)}"
        
    def log_warning(self, message: str, context: Optional[Dict] = None) -> None:
        """Enhanced warning logging.
        
        Args:
            message: Warning message
            context: Optional dictionary with contextual information
        """
        logger = logging.getLogger('game')
        warning_details = {
            "time": datetime.now().isoformat(),
            "message": message,
            "context": context or {}
        }
        logger.warning(json.dumps(warning_details))
    
    def recover_from_error(self, error_type: str, key=None) -> bool:
        """Attempt to recover from common errors.
        
        Args:
            error_type: Type of error to recover from
            
        Returns:
            bool: True if recovery was successful
        """
        recovery_strategies = {
            "ZeroDivisionError": lambda: True,  # Return safe default
            "ValueError": lambda: self.handle_value_error(),
            "KeyError": lambda: self.handle_missing_key(key),
            "IndexError": lambda: True  # Return safe default
        }
        
        if error_type in recovery_strategies:
            return recovery_strategies[error_type]()
        return False
        
    def handle_value_error(self) -> bool:
        """Handle invalid value errors."""
        try:
            # Log the error
            self.log_warning("Attempting to recover from value error")
            return True
        except Exception:
            return False
            
    def handle_missing_key(self, key):
        """Handle missing key errors consistently."""
        try:
            self.log_warning(f"Attempting to recover from missing key: {key}")
            return True
        except Exception as e:
            self.log_warning(f"Error in error recovery: {str(e)}")
            return False

# Create a global instance
error_handler = ErrorHandler()