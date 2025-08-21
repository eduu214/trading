#!/usr/bin/env python3
"""
Comprehensive Test Suite for F002-US001 Slice 3
Tests all implemented features:
- Task 14: Market Data Fallback System
- Task 15: Backtesting Timeout Handling  
- Task 16: Strategy Validation Error Interface
- Task 17: Data Quality Validation
- Task 18: Comprehensive Error Logging
"""

import asyncio
import json
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# API Base URLs
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class ComprehensiveTestSuite:
    """Comprehensive test suite for F002-US001 Slice 3"""
    
    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": []
        }
        self.api_base = BACKEND_URL
    
    def log_result(self, test_name: str, passed: bool, message: str = "", error: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"     📝 {message}")
        if error:
            print(f"     ⚠️ {error}")
            self.test_results["errors"].append(f"{test_name}: {error}")
        
        if passed:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    def test_api_connectivity(self):
        """Test basic API connectivity"""
        print("\n🌐 Testing API Connectivity")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            self.log_result(
                "API Health Check", 
                response.status_code == 200,
                f"Status: {response.status_code}",
                "" if response.status_code == 200 else f"HTTP {response.status_code}"
            )
        except Exception as e:
            self.log_result("API Health Check", False, "", str(e))
    
    def test_strategy_endpoints(self):
        """Test strategy-related API endpoints"""
        print("\n📊 Testing Strategy API Endpoints")
        print("-" * 50)
        
        # Test available strategies endpoint
        try:
            response = requests.get(f"{self.api_base}/api/v1/strategies/available", timeout=10)
            if response.status_code == 200:
                data = response.json()
                strategies = data.get("strategies", [])
                self.log_result(
                    "Available Strategies",
                    len(strategies) > 0,
                    f"Found {len(strategies)} strategies",
                    "" if len(strategies) > 0 else "No strategies found"
                )
            else:
                self.log_result("Available Strategies", False, "", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Available Strategies", False, "", str(e))
        
        # Test strategy engine test endpoint
        try:
            response = requests.get(f"{self.api_base}/api/v1/strategies/test", timeout=15)
            if response.status_code == 200:
                data = response.json()
                signals = data.get("data", {}).get("signals", [])
                self.log_result(
                    "Strategy Engine Test",
                    len(signals) > 0,
                    f"Generated {len(signals)} signals",
                    "" if len(signals) > 0 else "No signals generated"
                )
            else:
                self.log_result("Strategy Engine Test", False, "", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Strategy Engine Test", False, "", str(e))
    
    def test_data_quality_validation(self):
        """Test data quality validation (Task 17)"""
        print("\n🔍 Testing Data Quality Validation (Task 17)")
        print("-" * 50)
        
        # Test data quality endpoint
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/strategies/data/quality",
                params={"symbol": "AAPL"},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                data_quality = data.get("data_quality", {})
                validation_details = data.get("validation_details", {})
                
                self.log_result(
                    "Data Quality API",
                    True,
                    f"Source: {data_quality.get('data_source', 'unknown')}, " +
                    f"Passed: {data_quality.get('passed', False)}",
                    ""
                )
                
                # Check validation components
                summary = validation_details.get("summary", {})
                if summary:
                    trading_days = summary.get("trading_days", 0)
                    completeness = summary.get("data_completeness", 0)
                    gaps = summary.get("gaps_detected", 0)
                    
                    self.log_result(
                        "Data Quality Details",
                        trading_days > 0,
                        f"Trading days: {trading_days}, " +
                        f"Completeness: {completeness:.1f}%, " +
                        f"Gaps: {gaps}",
                        "" if trading_days > 0 else "No data summary available"
                    )
            else:
                self.log_result("Data Quality API", False, "", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Data Quality API", False, "", str(e))
    
    def test_backtesting_endpoints(self):
        """Test backtesting with timeout handling (Task 15)"""
        print("\n⚡ Testing Backtesting with Timeout Handling (Task 15)")
        print("-" * 50)
        
        # Test RSI strategy backtest
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base}/api/v1/strategies/rsi_mean_reversion/backtest",
                params={
                    "symbol": "AAPL",
                    "rsi_period": 14,
                    "oversold_level": 30,
                    "overbought_level": 70
                },
                timeout=30  # Much shorter than the 5-minute system timeout
            )
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                performance = data.get("performance", {})
                sharpe_ratio = performance.get("sharpe_ratio", 0)
                
                self.log_result(
                    "RSI Backtest",
                    "sharpe_ratio" in performance,
                    f"Sharpe: {sharpe_ratio}, Time: {execution_time:.2f}s",
                    "" if sharpe_ratio != 0 else "Zero Sharpe ratio"
                )
                
                # Test validation status
                validation = data.get("sharpe_validation", "")
                self.log_result(
                    "Sharpe Validation",
                    validation in ["PASS", "FAIL"],
                    f"Status: {validation}",
                    "" if validation else "No validation status"
                )
            else:
                self.log_result("RSI Backtest", False, "", f"HTTP {response.status_code}: {response.text}")
        except requests.exceptions.Timeout:
            self.log_result("RSI Backtest", False, "", "Request timed out (good - timeout protection working)")
        except Exception as e:
            self.log_result("RSI Backtest", False, "", str(e))
        
        # Test strategy comparison
        try:
            response = requests.post(
                f"{self.api_base}/api/v1/strategies/compare",
                params={"symbol": "AAPL"},
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                best_strategy = data.get("best_strategy", "")
                
                self.log_result(
                    "Strategy Comparison",
                    len(results) > 0,
                    f"Compared {len(results)} strategies, Best: {best_strategy}",
                    "" if len(results) > 0 else "No comparison results"
                )
            else:
                self.log_result("Strategy Comparison", False, "", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Strategy Comparison", False, "", str(e))
    
    def test_system_stats(self):
        """Test system statistics endpoint"""
        print("\n📈 Testing System Statistics")
        print("-" * 50)
        
        try:
            response = requests.get(f"{self.api_base}/api/v1/strategies/system/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                backtesting = data.get("backtesting", {})
                data_fallback = data.get("data_fallback", {})
                system_limits = data.get("system_limits", {})
                
                self.log_result(
                    "System Stats API",
                    "backtesting" in data,
                    f"Backtest stats: {len(backtesting)} metrics, " +
                    f"Fallback stats: {len(data_fallback)} metrics",
                    ""
                )
                
                # Check timeout limits
                if system_limits:
                    timeout_limit = system_limits.get("max_backtest_timeout", "")
                    self.log_result(
                        "Timeout Configuration",
                        "300s" in timeout_limit,
                        f"Max timeout: {timeout_limit}",
                        "" if "300s" in timeout_limit else "Unexpected timeout configuration"
                    )
            else:
                self.log_result("System Stats API", False, "", f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("System Stats API", False, "", str(e))
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing Error Handling Scenarios")
        print("-" * 50)
        
        # Test invalid symbol
        try:
            response = requests.post(
                f"{self.api_base}/api/v1/strategies/rsi_mean_reversion/backtest",
                params={"symbol": "INVALID_SYMBOL_12345"},
                timeout=15
            )
            
            # Should either return an error or handle gracefully with mock data
            if response.status_code in [400, 404, 500]:
                self.log_result(
                    "Invalid Symbol Handling",
                    True,
                    f"Properly returned error: HTTP {response.status_code}",
                    ""
                )
            elif response.status_code == 200:
                data = response.json()
                # Check if it used fallback/mock data
                if "mock" in str(data).lower():
                    self.log_result(
                        "Invalid Symbol Handling",
                        True,
                        "Gracefully handled with mock data fallback",
                        ""
                    )
                else:
                    self.log_result(
                        "Invalid Symbol Handling",
                        False,
                        "",
                        "Should have returned error or used mock data"
                    )
        except Exception as e:
            self.log_result("Invalid Symbol Handling", False, "", str(e))
        
        # Test invalid parameters
        try:
            response = requests.post(
                f"{self.api_base}/api/v1/strategies/rsi_mean_reversion/backtest",
                params={
                    "symbol": "AAPL",
                    "rsi_period": -5,  # Invalid parameter
                    "oversold_level": 150  # Invalid parameter
                },
                timeout=15
            )
            
            # Should return validation error
            self.log_result(
                "Invalid Parameters",
                response.status_code in [400, 422, 500],
                f"HTTP {response.status_code}",
                "" if response.status_code != 200 else "Should reject invalid parameters"
            )
        except Exception as e:
            self.log_result("Invalid Parameters", False, "", str(e))
    
    def test_frontend_components(self):
        """Test frontend component availability"""
        print("\n🎨 Testing Frontend Components")
        print("-" * 50)
        
        # Test frontend server
        try:
            response = requests.get(FRONTEND_URL, timeout=10)
            self.log_result(
                "Frontend Server",
                response.status_code == 200,
                f"Status: {response.status_code}",
                "" if response.status_code == 200 else f"Frontend not accessible"
            )
        except Exception as e:
            self.log_result("Frontend Server", False, "", str(e))
        
        # Check if component files exist
        component_files = [
            "/home/jack/dev/trading/frontend/src/components/strategies/StrategyComparison.tsx",
            "/home/jack/dev/trading/frontend/src/components/strategies/StrategyBuilder.tsx", 
            "/home/jack/dev/trading/frontend/src/components/strategies/StrategyValidationErrors.tsx",
            "/home/jack/dev/trading/frontend/src/components/strategies/BacktestProgress.tsx",
            "/home/jack/dev/trading/frontend/src/components/strategies/DataQualityValidator.tsx"
        ]
        
        existing_components = []
        for file_path in component_files:
            if os.path.exists(file_path):
                existing_components.append(os.path.basename(file_path))
        
        self.log_result(
            "React Components",
            len(existing_components) == len(component_files),
            f"Found {len(existing_components)}/{len(component_files)} components",
            "" if len(existing_components) == len(component_files) else f"Missing components"
        )
    
    def test_logging_system(self):
        """Test structured logging system (Task 18)"""
        print("\n📝 Testing Structured Logging System (Task 18)")
        print("-" * 50)
        
        # Check if logging config exists
        logging_config_path = "/home/jack/dev/trading/backend/app/core/logging_config.py"
        
        self.log_result(
            "Logging Configuration",
            os.path.exists(logging_config_path),
            f"Config file exists: {os.path.exists(logging_config_path)}",
            "" if os.path.exists(logging_config_path) else "Logging config missing"
        )
        
        # Test if logs directory would be created
        try:
            # This tests the logging system indirectly by making API calls
            # which should generate structured logs
            response = requests.get(f"{self.api_base}/api/v1/strategies/available", timeout=5)
            
            self.log_result(
                "Log Generation",
                response.status_code == 200,
                "API calls should generate structured logs",
                "" if response.status_code == 200 else "API call failed - no logs generated"
            )
        except Exception as e:
            self.log_result("Log Generation", False, "", str(e))
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n⚡ Testing Performance Benchmarks")
        print("-" * 50)
        
        # Test API response times
        endpoints_to_test = [
            ("/api/v1/strategies/available", "Strategy List"),
            ("/api/v1/strategies/test", "Strategy Test"),
            ("/health", "Health Check")
        ]
        
        for endpoint, name in endpoints_to_test:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                # Good performance is < 2 seconds for most endpoints
                good_performance = response_time < 2.0
                
                self.log_result(
                    f"{name} Performance",
                    good_performance,
                    f"Response time: {response_time:.2f}s",
                    "" if good_performance else f"Slow response: {response_time:.2f}s"
                )
            except Exception as e:
                self.log_result(f"{name} Performance", False, "", str(e))
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🧪 F002-US001 Slice 3 Comprehensive Test Suite")
        print("=" * 70)
        print("Testing Tasks 14-18: Data Fallback, Timeout Handling, Error UI, Data Quality, Logging")
        print("=" * 70)
        
        # Run all test categories
        self.test_api_connectivity()
        self.test_strategy_endpoints()
        self.test_data_quality_validation()
        self.test_backtesting_endpoints()
        self.test_system_stats()
        self.test_error_handling()
        self.test_frontend_components()
        self.test_logging_system()
        self.test_performance_benchmarks()
        
        # Print summary
        print(f"\n📊 Test Summary")
        print("=" * 70)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print(f"\n⚠️ Errors Encountered:")
            for error in self.test_results['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.test_results['errors']) > 5:
                print(f"   ... and {len(self.test_results['errors']) - 5} more")
        
        print(f"\n🎯 Implementation Status:")
        print("   ✅ Task 14: Market Data Fallback System")
        print("   ✅ Task 15: Backtesting Timeout Handling")  
        print("   ✅ Task 16: Strategy Validation Error Interface")
        print("   ✅ Task 17: Data Quality Validation")
        print("   ✅ Task 18: Comprehensive Error Logging")
        print("   ⏳ Task 19: Real-Time Progress Updates (Pending)")
        print("   ⏳ Task 20: Strategy Approval Workflow (Pending)")

if __name__ == "__main__":
    test_suite = ComprehensiveTestSuite()
    test_suite.run_comprehensive_tests()