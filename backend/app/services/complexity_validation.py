"""
Data validation and error handling for complexity optimization
F001-US002 Slice 3: Error Handling
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ErrorCode(str, Enum):
    """Standard error codes for complexity optimization"""
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_TIMEFRAME = "INVALID_TIMEFRAME"
    CONFLICTING_CONSTRAINTS = "CONFLICTING_CONSTRAINTS"
    OPTIMIZATION_TIMEOUT = "OPTIMIZATION_TIMEOUT"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    DATA_QUALITY_ISSUE = "DATA_QUALITY_ISSUE"
    CONSTRAINT_IMPOSSIBLE = "CONSTRAINT_IMPOSSIBLE"
    MARKET_DATA_UNAVAILABLE = "MARKET_DATA_UNAVAILABLE"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class DataSufficiencyValidator:
    """Validates data sufficiency for complexity analysis"""
    
    # Minimum data requirements per timeframe
    MIN_DATA_POINTS = {
        "1m": 1440,    # 1 day of minute data
        "5m": 288,     # 1 day of 5-minute data
        "15m": 96,     # 1 day of 15-minute data
        "30m": 48,     # 1 day of 30-minute data
        "1H": 168,     # 1 week of hourly data
        "4H": 42,      # 1 week of 4-hour data
        "1D": 30,      # 30 days of daily data
        "1W": 12,      # 12 weeks of weekly data
        "1M": 6        # 6 months of monthly data
    }
    
    # Minimum lookback periods for reliable analysis (in days)
    MIN_LOOKBACK_DAYS = {
        "1m": 5,
        "5m": 10,
        "15m": 15,
        "30m": 20,
        "1H": 30,
        "4H": 60,
        "1D": 90,
        "1W": 180,
        "1M": 365
    }
    
    @staticmethod
    def validate_data_sufficiency(
        data: pd.DataFrame,
        timeframe: str,
        lookback_days: int
    ) -> Tuple[bool, Optional[ValidationError]]:
        """
        Validate if data is sufficient for analysis
        
        Returns:
            Tuple of (is_valid, error)
        """
        try:
            # Check if data is empty
            if data.empty:
                return False, ValidationError(
                    "No data available for analysis",
                    ErrorCode.INSUFFICIENT_DATA,
                    {"rows": 0, "required": DataSufficiencyValidator.MIN_DATA_POINTS.get(timeframe, 30)}
                )
            
            # Check minimum data points
            min_points = DataSufficiencyValidator.MIN_DATA_POINTS.get(timeframe, 30)
            if len(data) < min_points:
                return False, ValidationError(
                    f"Insufficient data points: {len(data)} < {min_points}",
                    ErrorCode.INSUFFICIENT_DATA,
                    {
                        "actual_points": len(data),
                        "required_points": min_points,
                        "timeframe": timeframe
                    }
                )
            
            # Check lookback period
            min_lookback = DataSufficiencyValidator.MIN_LOOKBACK_DAYS.get(timeframe, 30)
            if lookback_days < min_lookback:
                return False, ValidationError(
                    f"Lookback period too short: {lookback_days} < {min_lookback} days",
                    ErrorCode.INSUFFICIENT_DATA,
                    {
                        "actual_lookback": lookback_days,
                        "required_lookback": min_lookback,
                        "timeframe": timeframe
                    }
                )
            
            # Check data quality
            null_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
            if null_ratio > 0.1:  # More than 10% missing data
                return False, ValidationError(
                    f"Too many missing values: {null_ratio:.1%}",
                    ErrorCode.DATA_QUALITY_ISSUE,
                    {
                        "null_ratio": null_ratio,
                        "threshold": 0.1
                    }
                )
            
            # Check for required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return False, ValidationError(
                    f"Missing required columns: {missing_columns}",
                    ErrorCode.DATA_QUALITY_ISSUE,
                    {"missing_columns": missing_columns}
                )
            
            # Check for data continuity (no large gaps)
            if hasattr(data.index, 'to_series'):
                time_diffs = data.index.to_series().diff()
                if len(time_diffs) > 1:
                    median_diff = time_diffs.median()
                    max_gap = time_diffs.max()
                    if max_gap > median_diff * 10:  # Gap is 10x larger than normal
                        return False, ValidationError(
                            "Large gaps detected in data",
                            ErrorCode.DATA_QUALITY_ISSUE,
                            {
                                "max_gap": str(max_gap),
                                "median_interval": str(median_diff)
                            }
                        )
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating data sufficiency: {str(e)}")
            return False, ValidationError(
                f"Validation error: {str(e)}",
                ErrorCode.CALCULATION_ERROR,
                {"exception": str(e)}
            )
    
    @staticmethod
    def validate_returns_data(
        returns: pd.Series,
        min_periods: int = 20
    ) -> Tuple[bool, Optional[ValidationError]]:
        """Validate returns data for metric calculation"""
        
        if returns.empty or len(returns) < min_periods:
            return False, ValidationError(
                f"Insufficient returns data: {len(returns)} < {min_periods}",
                ErrorCode.INSUFFICIENT_DATA,
                {"actual": len(returns), "required": min_periods}
            )
        
        # Check for extreme values
        if returns.std() == 0:
            return False, ValidationError(
                "No variance in returns data",
                ErrorCode.DATA_QUALITY_ISSUE,
                {"std": 0}
            )
        
        # Check for infinite or NaN values
        if returns.isnull().any() or np.isinf(returns).any():
            return False, ValidationError(
                "Invalid values in returns data",
                ErrorCode.DATA_QUALITY_ISSUE,
                {"nulls": returns.isnull().sum(), "inf": np.isinf(returns).sum()}
            )
        
        return True, None


class ConstraintValidator:
    """Validates complexity constraints"""
    
    @staticmethod
    def validate_constraint_compatibility(
        constraints: List[Dict]
    ) -> Tuple[bool, Optional[ValidationError]]:
        """
        Check if constraints are compatible with each other
        """
        try:
            # Check for conflicting complexity bounds
            max_complexity = None
            min_complexity = None
            
            for constraint in constraints:
                if constraint.get("type") == "MAX_COMPLEXITY":
                    max_complexity = constraint.get("value")
                elif constraint.get("type") == "MIN_COMPLEXITY":
                    min_complexity = constraint.get("value")
            
            if max_complexity is not None and min_complexity is not None:
                if max_complexity < min_complexity:
                    return False, ValidationError(
                        f"Conflicting complexity constraints: max({max_complexity}) < min({min_complexity})",
                        ErrorCode.CONFLICTING_CONSTRAINTS,
                        {
                            "max_complexity": max_complexity,
                            "min_complexity": min_complexity
                        }
                    )
            
            # Check for impossible combinations
            impossible_combinations = [
                ("MIN_SHARPE", 3.0),      # Extremely high Sharpe
                ("MAX_DRAWDOWN", -0.01),  # Unrealistic drawdown limit
                ("MIN_WIN_RATE", 0.95),   # Unrealistic win rate
                ("TARGET_RETURN", 5.0)    # 500% annual return
            ]
            
            for constraint in constraints:
                constraint_type = constraint.get("type")
                value = constraint.get("value")
                is_hard = constraint.get("is_hard_constraint", False)
                
                for impossible_type, impossible_value in impossible_combinations:
                    if constraint_type == impossible_type and is_hard:
                        if (impossible_type.startswith("MIN") and value >= impossible_value) or \
                           (impossible_type.startswith("MAX") and value <= impossible_value):
                            return False, ValidationError(
                                f"Constraint likely impossible to satisfy: {constraint_type} {value}",
                                ErrorCode.CONSTRAINT_IMPOSSIBLE,
                                {
                                    "constraint_type": constraint_type,
                                    "value": value,
                                    "threshold": impossible_value
                                }
                            )
            
            # Check for too many hard constraints
            hard_count = sum(1 for c in constraints if c.get("is_hard_constraint", False))
            if hard_count > 5:
                logger.warning(f"High number of hard constraints: {hard_count}")
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating constraints: {str(e)}")
            return False, ValidationError(
                f"Constraint validation error: {str(e)}",
                ErrorCode.CALCULATION_ERROR,
                {"exception": str(e)}
            )
    
    @staticmethod
    def validate_constraint_values(
        constraint_type: str,
        operator: str,
        value: float
    ) -> Tuple[bool, Optional[ValidationError]]:
        """Validate individual constraint values"""
        
        # Define valid ranges for each constraint type
        valid_ranges = {
            "MIN_SHARPE": (-2, 5),
            "MAX_DRAWDOWN": (-1, 0),
            "MAX_VOLATILITY": (0, 2),
            "MIN_WIN_RATE": (0, 1),
            "MIN_PROFIT_FACTOR": (0, 10),
            "MAX_COMPLEXITY": (1, 10),
            "MIN_COMPLEXITY": (1, 10),
            "TARGET_RETURN": (-1, 10),
            "RISK_LIMIT": (0, 1)
        }
        
        if constraint_type in valid_ranges:
            min_val, max_val = valid_ranges[constraint_type]
            if not (min_val <= value <= max_val):
                return False, ValidationError(
                    f"Constraint value out of range: {value} not in [{min_val}, {max_val}]",
                    ErrorCode.INVALID_PARAMETERS,
                    {
                        "constraint_type": constraint_type,
                        "value": value,
                        "valid_range": [min_val, max_val]
                    }
                )
        
        # Validate operators
        valid_operators = ["<", "<=", ">", ">=", "=="]
        if operator not in valid_operators:
            return False, ValidationError(
                f"Invalid operator: {operator}",
                ErrorCode.INVALID_PARAMETERS,
                {
                    "operator": operator,
                    "valid_operators": valid_operators
                }
            )
        
        return True, None


class OptimizationErrorHandler:
    """Handles errors during optimization with retry logic"""
    
    MAX_RETRIES = 3
    RETRY_DELAYS = [5, 15, 30]  # Seconds
    
    @staticmethod
    def handle_optimization_error(
        error: Exception,
        context: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Handle optimization errors with appropriate response
        
        Returns:
            Dict with error details and recovery suggestions
        """
        error_response = {
            "success": False,
            "error_code": ErrorCode.CALCULATION_ERROR,
            "message": str(error),
            "retry_count": retry_count,
            "can_retry": retry_count < OptimizationErrorHandler.MAX_RETRIES,
            "recovery_suggestions": []
        }
        
        # Classify error and provide specific handling
        if isinstance(error, ValidationError):
            error_response["error_code"] = error.error_code
            error_response["details"] = error.details
            
            # Provide specific recovery suggestions
            if error.error_code == ErrorCode.INSUFFICIENT_DATA:
                error_response["recovery_suggestions"] = [
                    "Increase lookback period",
                    "Use a different timeframe with more data",
                    "Wait for more data to accumulate"
                ]
            elif error.error_code == ErrorCode.CONFLICTING_CONSTRAINTS:
                error_response["recovery_suggestions"] = [
                    "Review and adjust constraint values",
                    "Remove conflicting constraints",
                    "Use soft constraints instead of hard constraints"
                ]
            elif error.error_code == ErrorCode.OPTIMIZATION_TIMEOUT:
                error_response["recovery_suggestions"] = [
                    "Reduce the number of timeframes",
                    "Simplify constraints",
                    "Try again with fewer complexity levels"
                ]
        
        elif "timeout" in str(error).lower():
            error_response["error_code"] = ErrorCode.OPTIMIZATION_TIMEOUT
            error_response["recovery_suggestions"] = [
                "The optimization is taking longer than expected",
                "Try with fewer timeframes or constraints",
                "Check system resources"
            ]
        
        elif "database" in str(error).lower() or "connection" in str(error).lower():
            error_response["error_code"] = ErrorCode.DATABASE_ERROR
            error_response["recovery_suggestions"] = [
                "Check database connection",
                "Verify database service is running",
                "Contact administrator if issue persists"
            ]
        
        else:
            error_response["recovery_suggestions"] = [
                "Try again in a few moments",
                "Check input parameters",
                "Contact support if issue persists"
            ]
        
        # Log error for monitoring
        logger.error(
            f"Optimization error: {error_response['error_code']} - {error_response['message']}",
            extra={
                "context": context,
                "retry_count": retry_count,
                "error_details": error_response.get("details", {})
            }
        )
        
        return error_response
    
    @staticmethod
    def create_user_friendly_message(error_code: ErrorCode, details: Dict = None) -> str:
        """Create user-friendly error messages"""
        
        messages = {
            ErrorCode.INSUFFICIENT_DATA: "Not enough historical data available for analysis. Please try with a shorter timeframe or wait for more data.",
            ErrorCode.INVALID_TIMEFRAME: "The selected timeframe is not supported. Please choose from the available options.",
            ErrorCode.CONFLICTING_CONSTRAINTS: "Some constraints conflict with each other. Please review and adjust your requirements.",
            ErrorCode.OPTIMIZATION_TIMEOUT: "The optimization is taking too long. Try with simpler parameters or fewer timeframes.",
            ErrorCode.INVALID_PARAMETERS: "Invalid parameters provided. Please check your inputs and try again.",
            ErrorCode.DATA_QUALITY_ISSUE: "Data quality issues detected. Some data points may be missing or invalid.",
            ErrorCode.CONSTRAINT_IMPOSSIBLE: "The constraints appear impossible to satisfy. Please relax some requirements.",
            ErrorCode.MARKET_DATA_UNAVAILABLE: "Market data is temporarily unavailable. Please try again later.",
            ErrorCode.CALCULATION_ERROR: "An error occurred during calculation. Please try again or contact support.",
            ErrorCode.DATABASE_ERROR: "Database connection issue. Please try again or contact administrator."
        }
        
        base_message = messages.get(error_code, "An unexpected error occurred. Please try again.")
        
        # Add specific details if available
        if details:
            if "actual_points" in details and "required_points" in details:
                base_message += f" (Need {details['required_points']} data points, have {details['actual_points']})"
            elif "max_complexity" in details and "min_complexity" in details:
                base_message += f" (Max: {details['max_complexity']}, Min: {details['min_complexity']})"
        
        return base_message


class FallbackComplexityScorer:
    """Provides fallback scoring when optimization fails"""
    
    @staticmethod
    def calculate_fallback_score(
        strategy_params: Dict,
        available_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Calculate a simple fallback complexity score
        
        Returns:
            Dict with fallback scores and metrics
        """
        fallback_result = {
            "is_fallback": True,
            "complexity_level": 5,  # Default middle complexity
            "confidence": 0.3,      # Low confidence
            "score": 50,            # Middle score
            "metrics": {
                "sharpe_ratio": 0.0,
                "max_drawdown": -0.20,
                "volatility": 0.25,
                "win_rate": 0.5,
                "profit_factor": 1.0
            },
            "message": "Using fallback scoring due to optimization failure"
        }
        
        # Try to estimate based on strategy parameters
        if strategy_params:
            # Estimate complexity based on number of parameters
            param_count = len(strategy_params)
            if param_count < 5:
                fallback_result["complexity_level"] = 3
            elif param_count < 10:
                fallback_result["complexity_level"] = 5
            else:
                fallback_result["complexity_level"] = 7
        
        # If we have some data, try basic calculations
        if available_data is not None and not available_data.empty:
            try:
                if 'close' in available_data.columns:
                    returns = available_data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        fallback_result["metrics"]["volatility"] = float(returns.std())
                        
                        # Simple Sharpe approximation
                        if returns.std() > 0:
                            fallback_result["metrics"]["sharpe_ratio"] = float(
                                returns.mean() / returns.std() * np.sqrt(252)
                            )
                        
                        # Simple max drawdown
                        cumulative = (1 + returns).cumprod()
                        running_max = cumulative.expanding().max()
                        drawdown = (cumulative - running_max) / running_max
                        fallback_result["metrics"]["max_drawdown"] = float(drawdown.min())
                        
                        # Update confidence based on data availability
                        fallback_result["confidence"] = min(0.5, len(returns) / 1000)
                        
            except Exception as e:
                logger.warning(f"Error in fallback calculation: {str(e)}")
        
        return fallback_result