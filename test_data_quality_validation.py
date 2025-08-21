#!/usr/bin/env python3
"""
Test script for data quality validation
F002-US001 Slice 3 Task 17: Verify data quality validation implementation
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.append('/home/jack/dev/trading/backend')

from app.services.historical_data_service import HistoricalDataService, DataQualityError

async def create_test_data():
    """Create test datasets with various quality issues"""
    
    # Test 1: Good quality data (6+ months, no gaps)
    start_date = datetime.now() - timedelta(days=200)
    dates = pd.bdate_range(start=start_date, periods=130)  # 130 trading days
    
    good_data = pd.DataFrame({
        'open': 100 + np.random.randn(130) * 2,
        'high': 102 + np.random.randn(130) * 2,
        'low': 98 + np.random.randn(130) * 2,
        'close': 100 + np.random.randn(130) * 2,
        'volume': np.random.randint(1000000, 5000000, 130)
    }, index=dates)
    
    # Ensure price relationships are correct
    good_data['high'] = good_data[['open', 'close']].max(axis=1) + 1
    good_data['low'] = good_data[['open', 'close']].min(axis=1) - 1
    
    # Test 2: Insufficient data (too short period)
    short_dates = pd.bdate_range(start=datetime.now() - timedelta(days=60), periods=40)
    short_data = pd.DataFrame({
        'open': 100 + np.random.randn(40) * 2,
        'high': 102 + np.random.randn(40) * 2,
        'low': 98 + np.random.randn(40) * 2,
        'close': 100 + np.random.randn(40) * 2,
        'volume': np.random.randint(1000000, 5000000, 40)
    }, index=short_dates)
    
    # Test 3: Data with gaps
    gap_dates = pd.bdate_range(start=datetime.now() - timedelta(days=200), periods=130)
    # Remove 10 consecutive days to create a critical gap
    gap_dates = gap_dates.drop(gap_dates[50:60])  # Remove 10 days
    
    gap_data = pd.DataFrame({
        'open': 100 + np.random.randn(120) * 2,
        'high': 102 + np.random.randn(120) * 2,
        'low': 98 + np.random.randn(120) * 2,
        'close': 100 + np.random.randn(120) * 2,
        'volume': np.random.randint(1000000, 5000000, 120)
    }, index=gap_dates)
    
    # Test 4: Data with integrity issues
    integrity_dates = pd.bdate_range(start=datetime.now() - timedelta(days=200), periods=130)
    integrity_data = pd.DataFrame({
        'open': 100 + np.random.randn(130) * 2,
        'high': 102 + np.random.randn(130) * 2,
        'low': 98 + np.random.randn(130) * 2,
        'close': 100 + np.random.randn(130) * 2,
        'volume': np.random.randint(1000000, 5000000, 130)
    }, index=integrity_dates)
    
    # Add integrity issues
    integrity_data.loc[integrity_data.index[10], 'high'] = 50  # High < Low
    integrity_data.loc[integrity_data.index[10], 'low'] = 100
    integrity_data.loc[integrity_data.index[20], 'close'] = 1000  # Extreme price change
    
    return {
        'good_data': good_data,
        'short_data': short_data,
        'gap_data': gap_data,
        'integrity_data': integrity_data
    }

async def test_data_quality_validation():
    """Test the data quality validation implementation"""
    
    print("🧪 Testing Data Quality Validation (F002-US001 Task 17)")
    print("=" * 60)
    
    # Create test data
    test_datasets = await create_test_data()
    
    # Initialize service
    service = HistoricalDataService()
    
    # Test each dataset
    for test_name, data in test_datasets.items():
        print(f"\n📊 Testing: {test_name}")
        print("-" * 40)
        
        start_date = data.index[0]
        end_date = data.index[-1]
        
        try:
            # Validate data quality
            quality_result = await service._validate_data_quality(
                data, 
                f"TEST_{test_name.upper()}", 
                start_date, 
                end_date
            )
            
            # Print results
            print(f"✅ Data Quality Passed: {quality_result['data_quality_passed']}")
            print(f"📈 Trading Days: {quality_result['validation_details'].get('summary', {}).get('trading_days', 'N/A')}")
            print(f"📊 Data Completeness: {quality_result['validation_details'].get('summary', {}).get('data_completeness', 0):.1f}%")
            print(f"🔍 Gaps Detected: {quality_result['validation_details'].get('summary', {}).get('gaps_detected', 0)}")
            print(f"⚠️  Critical Gaps: {quality_result['validation_details'].get('summary', {}).get('critical_gaps', 0)}")
            
            if quality_result['quality_errors']:
                print(f"❌ Errors: {quality_result['quality_errors']}")
            
            if quality_result['quality_warnings']:
                print(f"⚠️  Warnings: {quality_result['quality_warnings']}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print(f"\n🎯 Data Quality Validation Tests Complete")
    print("=" * 60)

async def test_gap_detection():
    """Test gap detection specifically"""
    
    print("\n🔍 Testing Gap Detection Logic")
    print("-" * 40)
    
    service = HistoricalDataService()
    
    # Create data with known gaps
    base_dates = pd.bdate_range(start='2024-01-01', end='2024-06-30')
    # Remove some dates to create gaps
    gap_dates = base_dates.drop([
        base_dates[10:13],  # 3-day gap (minor)
        base_dates[50:58],  # 8-day gap (critical)
    ])
    
    test_data = pd.DataFrame({
        'close': 100 + np.random.randn(len(gap_dates)) * 2
    }, index=gap_dates)
    
    gap_analysis = await service._detect_data_gaps(test_data, "GAP_TEST")
    
    print(f"Total Gaps: {gap_analysis['total_gaps']}")
    print(f"Critical Gaps: {gap_analysis['critical_gaps']}")
    print(f"Max Gap Days: {gap_analysis['max_gap_days']}")
    print(f"Expected Trading Days: {gap_analysis['expected_trading_days']}")
    print(f"Actual Trading Days: {gap_analysis['actual_trading_days']}")
    
    for i, gap in enumerate(gap_analysis['gap_details']):
        print(f"Gap {i+1}: {gap['days']} days ({'Critical' if gap['is_critical'] else 'Minor'})")

async def test_integrity_check():
    """Test data integrity validation"""
    
    print("\n🔍 Testing Data Integrity Validation")
    print("-" * 40)
    
    service = HistoricalDataService()
    
    # Create data with integrity issues
    dates = pd.bdate_range(start='2024-01-01', periods=50)
    test_data = pd.DataFrame({
        'open': 100 + np.random.randn(50) * 2,
        'high': 102 + np.random.randn(50) * 2,
        'low': 98 + np.random.randn(50) * 2,
        'close': 100 + np.random.randn(50) * 2,
        'volume': np.random.randint(1000000, 5000000, 50)
    }, index=dates)
    
    # Add specific integrity issues
    test_data.loc[dates[5], 'high'] = 50  # High < Low
    test_data.loc[dates[5], 'low'] = 100
    test_data.loc[dates[10], 'close'] = 200  # Close outside high/low
    test_data.loc[dates[10], 'high'] = 105
    test_data.loc[dates[10], 'low'] = 95
    
    integrity_result = await service._check_data_integrity(test_data)
    
    print(f"Integrity Valid: {integrity_result['valid']}")
    if integrity_result['issues']:
        print("Issues found:")
        for issue in integrity_result['issues']:
            print(f"  - {issue}")

if __name__ == "__main__":
    asyncio.run(test_data_quality_validation())
    asyncio.run(test_gap_detection())
    asyncio.run(test_integrity_check())