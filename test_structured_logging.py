#!/usr/bin/env python3
"""
Test script for structured logging system
F002-US001 Slice 3 Task 18: Verify comprehensive error logging implementation
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/home/jack/dev/trading/backend')

from app.core.logging_config import structured_logger

async def test_structured_logging():
    """Test all structured logging functionality"""
    
    print("🧪 Testing Structured Logging System (F002-US001 Task 18)")
    print("=" * 60)
    
    # Test 1: Correlation ID generation
    print("\n📝 Testing Correlation ID Generation")
    print("-" * 40)
    
    correlation_ids = []
    for i in range(5):
        corr_id = structured_logger.generate_correlation_id()
        correlation_ids.append(corr_id)
        print(f"Generated ID {i+1}: {corr_id}")
    
    # Verify uniqueness
    unique_ids = set(correlation_ids)
    print(f"✅ All IDs unique: {len(unique_ids) == len(correlation_ids)}")
    
    # Test 2: Backtest logging
    print("\n📊 Testing Backtest Operation Logging")
    print("-" * 40)
    
    test_correlation_id = structured_logger.generate_correlation_id()
    
    # Log backtest start
    structured_logger.log_backtest_start(
        correlation_id=test_correlation_id,
        symbol="TEST",
        strategy="RSI_MEAN_REVERSION",
        parameters={
            "rsi_period": 14,
            "oversold_level": 30,
            "overbought_level": 70
        },
        data_period={
            "start": "2024-01-01",
            "end": "2024-06-30",
            "data_points": 130
        }
    )
    print("✅ Backtest start logged")
    
    # Log successful completion
    structured_logger.log_backtest_success(
        correlation_id=test_correlation_id,
        symbol="TEST",
        strategy="RSI_MEAN_REVERSION",
        performance_metrics={
            "sharpe_ratio": 1.25,
            "total_return_pct": 15.5,
            "max_drawdown_pct": -8.2,
            "win_rate": 0.65,
            "total_trades": 25
        },
        execution_time=2.3
    )
    print("✅ Backtest success logged")
    
    # Log backtest error
    test_error = Exception("Test calculation error")
    structured_logger.log_backtest_error(
        correlation_id=test_correlation_id,
        symbol="TEST",
        strategy="RSI_MEAN_REVERSION",
        error=test_error,
        error_category="CALCULATION_ERROR",
        context={"additional_info": "Test error context"}
    )
    print("✅ Backtest error logged")
    
    # Test 3: Indicator logging
    print("\n📈 Testing Technical Indicator Logging")
    print("-" * 40)
    
    indicator_correlation_id = structured_logger.generate_correlation_id()
    
    # Log successful indicator calculation
    structured_logger.log_indicator_calculation(
        correlation_id=indicator_correlation_id,
        indicator_name="RSI",
        symbol="TEST",
        parameters={"period": 14},
        data_points=130,
        execution_time=0.05
    )
    print("✅ Indicator calculation logged")
    
    # Log indicator error
    indicator_error = Exception("Invalid period parameter")
    structured_logger.log_indicator_error(
        correlation_id=indicator_correlation_id,
        indicator_name="MACD",
        symbol="TEST",
        error=indicator_error,
        parameters={"fast_period": 12, "slow_period": 26},
        data_points=130
    )
    print("✅ Indicator error logged")
    
    # Test 4: Data quality validation logging
    print("\n🔍 Testing Data Quality Validation Logging")
    print("-" * 40)
    
    validation_correlation_id = structured_logger.generate_correlation_id()
    
    validation_result = {
        'data_quality_passed': True,
        'quality_errors': [],
        'quality_warnings': ['Minor gap detected']
    }
    
    structured_logger.log_data_quality_validation(
        correlation_id=validation_correlation_id,
        symbol="TEST",
        validation_result=validation_result,
        data_source="yfinance",
        execution_time=0.15
    )
    print("✅ Data quality validation logged")
    
    # Test 5: Data fetch error logging
    print("\n📡 Testing Data Fetch Error Logging")
    print("-" * 40)
    
    fetch_error = Exception("API rate limit exceeded")
    structured_logger.log_data_fetch_error(
        correlation_id=validation_correlation_id,
        symbol="TEST",
        data_source="polygon",
        error=fetch_error,
        fallback_used=True,
        retry_attempt=2
    )
    print("✅ Data fetch error logged")
    
    # Test 6: Timeout error logging
    print("\n⏱️  Testing Timeout Error Logging")
    print("-" * 40)
    
    timeout_correlation_id = structured_logger.generate_correlation_id()
    
    structured_logger.log_timeout_error(
        correlation_id=timeout_correlation_id,
        operation="backtest_rsi_strategy",
        timeout_seconds=300.0,
        elapsed_seconds=315.2,
        context={
            "symbol": "TEST",
            "strategy": "RSI_MEAN_REVERSION",
            "data_points": 500
        }
    )
    print("✅ Timeout error logged")
    
    # Test 7: Performance metrics logging
    print("\n📊 Testing Performance Metrics Logging")
    print("-" * 40)
    
    performance_correlation_id = structured_logger.generate_correlation_id()
    
    structured_logger.log_performance_metrics(
        correlation_id=performance_correlation_id,
        operation="full_backtest_pipeline",
        metrics={
            "total_execution_time": 45.2,
            "data_fetch_time": 2.1,
            "indicator_calculation_time": 0.8,
            "backtesting_time": 42.3,
            "memory_usage_mb": 156.7,
            "cpu_usage_percent": 78.5
        }
    )
    print("✅ Performance metrics logged")
    
    # Test 8: API error logging
    print("\n🌐 Testing API Error Logging")
    print("-" * 40)
    
    api_correlation_id = structured_logger.generate_correlation_id()
    
    api_error = Exception("Authentication failed")
    structured_logger.log_api_error(
        correlation_id=api_correlation_id,
        api_name="Polygon.io",
        endpoint="/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-06-30",
        status_code=401,
        error=api_error,
        response_time=1.2
    )
    print("✅ API error logged")
    
    print(f"\n🎯 Structured Logging System Tests Complete")
    print("=" * 60)
    print("\n📝 Log files should be created in:")
    print("  - logs/trading_platform.json (all logs)")
    print("  - logs/errors.json (errors only)")
    print("\n💡 To view logs in development:")
    print("  tail -f logs/trading_platform.json | jq '.'")

def test_error_categories():
    """Test error categorization system"""
    
    print("\n🏷️  Testing Error Categories")
    print("-" * 40)
    
    for category, description in structured_logger.error_categories.items():
        print(f"  {category}: {description}")
    
    print(f"✅ {len(structured_logger.error_categories)} error categories defined")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    asyncio.run(test_structured_logging())
    test_error_categories()
    
    print("\n🔍 Sample log entry structure:")
    print("-" * 40)
    print(json.dumps({
        "timestamp": "2024-01-01T12:00:00.000000",
        "level": "INFO",
        "logger": "app.services.backtesting_engine",
        "function": "backtest_rsi_strategy",
        "line": 245,
        "message": "Backtest operation started",
        "context": {
            "correlation_id": "req_1704110400000_0001",
            "operation": "backtest_start",
            "symbol": "AAPL",
            "strategy": "RSI_MEAN_REVERSION",
            "category": "BACKTEST_OPERATION"
        }
    }, indent=2))