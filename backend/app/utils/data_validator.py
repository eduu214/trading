"""
Data validation pipeline for market data and API responses
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class DataQuality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"

class PriceDataValidator(BaseModel):
    """Validator for price data"""
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    timestamp: datetime
    
    @validator('high')
    def high_must_be_highest(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('High must be >= low')
        if 'open' in values and v < values['open']:
            logger.warning(f"High {v} is less than open {values['open']}")
        if 'close' in values and v < values['close']:
            logger.warning(f"High {v} is less than close {values['close']}")
        return v
    
    @validator('low')
    def low_must_be_lowest(cls, v, values):
        if 'high' in values and v > values['high']:
            raise ValueError('Low must be <= high')
        if 'open' in values and v > values['open']:
            logger.warning(f"Low {v} is greater than open {values['open']}")
        if 'close' in values and v > values['close']:
            logger.warning(f"Low {v} is greater than close {values['close']}")
        return v
    
    @validator('timestamp')
    def timestamp_must_be_reasonable(cls, v):
        now = datetime.now()
        if v > now + timedelta(days=1):
            raise ValueError('Timestamp is in the future')
        if v < now - timedelta(days=365 * 10):
            raise ValueError('Timestamp is too old (>10 years)')
        return v

class MarketDataValidator:
    """
    Comprehensive market data validation
    """
    
    @staticmethod
    def validate_price_data(data: Dict) -> tuple[bool, List[str]]:
        """
        Validate price data (OHLCV)
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Basic field presence
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            if errors:
                return False, errors
            
            # Validate using Pydantic model
            PriceDataValidator(
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                volume=data['volume'],
                timestamp=data.get('timestamp', datetime.now())
            )
            
            # Additional business logic validations
            
            # Check for suspicious price movements (>50% in a bar)
            price_change = abs(data['close'] - data['open']) / data['open']
            if price_change > 0.5:
                errors.append(f"Suspicious price movement: {price_change*100:.1f}%")
            
            # Check for zero volume on price movement
            if data['volume'] == 0 and data['close'] != data['open']:
                errors.append("Price changed with zero volume")
            
            # Check for price outliers (using high/low spread)
            spread = (data['high'] - data['low']) / data['low'] if data['low'] > 0 else 0
            if spread > 0.3:  # 30% spread is unusual
                errors.append(f"Unusual price spread: {spread*100:.1f}%")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(str(e))
            return False, errors
    
    @staticmethod
    def validate_ticker_data(data: Dict) -> tuple[bool, List[str]]:
        """Validate ticker/symbol data"""
        errors = []
        
        required_fields = ['ticker', 'name', 'market', 'currency']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if 'ticker' in data:
            ticker = data['ticker']
            # Check ticker format
            if not ticker or len(ticker) > 10:
                errors.append(f"Invalid ticker format: {ticker}")
            
            # Check for suspicious characters
            if not ticker.replace('.', '').replace('-', '').isalnum():
                errors.append(f"Ticker contains invalid characters: {ticker}")
        
        if 'market' in data:
            valid_markets = ['stocks', 'crypto', 'fx', 'futures', 'options']
            if data['market'] not in valid_markets:
                errors.append(f"Invalid market: {data['market']}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def assess_data_quality(data: List[Dict]) -> DataQuality:
        """
        Assess overall quality of dataset
        """
        if not data:
            return DataQuality.INVALID
        
        valid_count = 0
        total_count = len(data)
        gaps_count = 0
        
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', 0))
        
        for i, item in enumerate(sorted_data):
            is_valid, _ = MarketDataValidator.validate_price_data(item)
            if is_valid:
                valid_count += 1
            
            # Check for time gaps
            if i > 0:
                prev_time = sorted_data[i-1].get('timestamp')
                curr_time = item.get('timestamp')
                if prev_time and curr_time:
                    # Assuming daily data, gap > 3 days is suspicious
                    if (curr_time - prev_time).days > 3:
                        gaps_count += 1
        
        validity_ratio = valid_count / total_count
        
        if validity_ratio >= 0.95 and gaps_count == 0:
            return DataQuality.HIGH
        elif validity_ratio >= 0.80:
            return DataQuality.MEDIUM
        elif validity_ratio >= 0.50:
            return DataQuality.LOW
        else:
            return DataQuality.INVALID

class ScanConfigValidator:
    """Validate scan configuration"""
    
    @staticmethod
    def validate(config: Dict) -> tuple[bool, List[str]]:
        """Validate scan configuration"""
        errors = []
        
        # Asset classes
        if 'asset_classes' in config:
            valid_classes = ['equities', 'futures', 'fx', 'crypto', 'options']
            for ac in config['asset_classes']:
                if ac not in valid_classes:
                    errors.append(f"Invalid asset class: {ac}")
        
        # Numeric parameters
        numeric_params = {
            'min_volume': (0, 1e12),
            'min_price_change': (0, 1),
            'correlation_threshold': (0, 1),
            'min_opportunity_score': (0, 1),
            'max_results': (1, 1000)
        }
        
        for param, (min_val, max_val) in numeric_params.items():
            if param in config:
                value = config[param]
                if not isinstance(value, (int, float)):
                    errors.append(f"{param} must be numeric")
                elif value < min_val or value > max_val:
                    errors.append(f"{param} must be between {min_val} and {max_val}")
        
        return len(errors) == 0, errors

class DataSanitizer:
    """Sanitize and clean data"""
    
    @staticmethod
    def sanitize_price_data(data: Dict) -> Dict:
        """Clean and sanitize price data"""
        sanitized = {}
        
        # Convert to proper types
        for field in ['open', 'high', 'low', 'close']:
            if field in data:
                try:
                    sanitized[field] = float(data[field])
                    # Ensure positive prices
                    if sanitized[field] < 0:
                        sanitized[field] = abs(sanitized[field])
                except (TypeError, ValueError):
                    logger.warning(f"Could not convert {field} to float: {data[field]}")
                    sanitized[field] = 0.0
        
        # Volume should be integer
        if 'volume' in data:
            try:
                sanitized['volume'] = int(float(data['volume']))
                if sanitized['volume'] < 0:
                    sanitized['volume'] = 0
            except (TypeError, ValueError):
                sanitized['volume'] = 0
        
        # Fix OHLC relationships
        if all(k in sanitized for k in ['open', 'high', 'low', 'close']):
            # Ensure high is highest
            sanitized['high'] = max(
                sanitized['high'],
                sanitized['open'],
                sanitized['close'],
                sanitized['low']
            )
            # Ensure low is lowest
            sanitized['low'] = min(
                sanitized['low'],
                sanitized['open'],
                sanitized['close'],
                sanitized['high']
            )
        
        # Copy other fields
        for key, value in data.items():
            if key not in sanitized:
                sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def remove_outliers(data: List[Dict], std_devs: float = 3) -> List[Dict]:
        """Remove statistical outliers from dataset"""
        if len(data) < 10:
            return data  # Need enough data for statistics
        
        import numpy as np
        
        # Calculate price changes
        changes = []
        for i in range(1, len(data)):
            if data[i]['close'] > 0 and data[i-1]['close'] > 0:
                change = (data[i]['close'] - data[i-1]['close']) / data[i-1]['close']
                changes.append(change)
        
        if not changes:
            return data
        
        # Calculate statistics
        mean_change = np.mean(changes)
        std_change = np.std(changes)
        
        # Filter outliers
        filtered = [data[0]]  # Keep first item
        for i in range(1, len(data)):
            if data[i]['close'] > 0 and data[i-1]['close'] > 0:
                change = (data[i]['close'] - data[i-1]['close']) / data[i-1]['close']
                if abs(change - mean_change) <= std_devs * std_change:
                    filtered.append(data[i])
                else:
                    logger.warning(f"Removing outlier with {change*100:.1f}% change")
            else:
                filtered.append(data[i])
        
        return filtered

def validate_api_response(response: Dict, expected_schema: Dict) -> bool:
    """
    Validate API response against expected schema
    
    Args:
        response: API response to validate
        expected_schema: Expected structure
    
    Returns:
        True if valid, raises ValidationError if not
    """
    def check_schema(data, schema, path=""):
        if isinstance(schema, dict):
            if not isinstance(data, dict):
                raise ValidationError(f"Expected dict at {path}, got {type(data)}")
            
            for key, expected_type in schema.items():
                if key not in data:
                    raise ValidationError(f"Missing required field: {path}.{key}")
                
                check_schema(data[key], expected_type, f"{path}.{key}")
        
        elif isinstance(schema, list):
            if not isinstance(data, list):
                raise ValidationError(f"Expected list at {path}, got {type(data)}")
            
            if schema:  # If schema has example element
                for i, item in enumerate(data):
                    check_schema(item, schema[0], f"{path}[{i}]")
        
        elif isinstance(schema, type):
            if not isinstance(data, schema):
                raise ValidationError(
                    f"Expected {schema.__name__} at {path}, got {type(data).__name__}"
                )
    
    try:
        check_schema(response, expected_schema)
        return True
    except ValidationError:
        raise