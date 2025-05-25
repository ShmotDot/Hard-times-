
"""
Data validation utilities for Hard Times: Ottawa.
"""
from typing import Any, Dict, Optional
from .error_handler import ValidationError

class Validator:
    """Data validation utility class."""
    
    @staticmethod
    def validate_numeric(value: Any, field_name: str) -> None:
        """Validate numeric values."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be numeric")
            
    @staticmethod
    def validate_progress(value: float, field_name: str) -> None:
        """Validate progress percentage."""
        if not 0 <= value <= 100:
            raise ValidationError(f"{field_name} must be between 0 and 100")
            
    @staticmethod
    def validate_positive(value: float, field_name: str) -> None:
        """Validate positive numbers."""
        if value < 0:
            raise ValidationError(f"{field_name} cannot be negative")
    
    @staticmethod
    def validate_range(value: float, min_val: float, max_val: float, name: str) -> None:
        """Validate a value is within range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name of the value being validated
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{name} must be a number")
        if value < min_val or value > max_val:
            raise ValidationError(f"{name} must be between {min_val} and {max_val}")
            
    @staticmethod
    def validate_stats(stats: Dict[str, float]) -> None:
        """Validate player stats.
        
        Args:
            stats: Dictionary of stats to validate
            
        Raises:
            ValidationError: If validation fails
        """
        required_stats = ['health', 'satiety', 'energy', 'mental', 'hygiene']
        for stat in required_stats:
            if stat not in stats:
                raise ValidationError(f"Missing required stat: {stat}")
            Validator.validate_range(stats[stat], 0, 100, stat)
            
    @staticmethod
    def validate_item(item: Dict[str, Any]) -> None:
        """Validate item data.
        
        Args:
            item: Item data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['name', 'weight', 'value']
        for field in required_fields:
            if field not in item:
                raise ValidationError(f"Missing required item field: {field}")
                
        if not isinstance(item['name'], str):
            raise ValidationError("Item name must be a string")
        if not isinstance(item['weight'], (int, float)):
            raise ValidationError("Item weight must be a number")
        if not isinstance(item['value'], (int, float)):
            raise ValidationError("Item value must be a number")
