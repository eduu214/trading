#!/usr/bin/env python3
"""
Test script for complexity optimization functionality
"""
import sys
import os
sys.path.append('/home/jack/dev/trading/backend')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Import the complexity analyzer
from backend.app.core.complexity_analyzer import (
    ComplexityAnalyzer,
    ComplexityLevel,
    ComplexityMetrics,
    ComplexityScore
)

def generate_sample_returns(days=252, volatility=0.15, drift=0.08):
    """Generate sample return data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Generate random returns with drift
    daily_returns = np.random.normal(drift/252, volatility/np.sqrt(252), days)
    
    # Convert to price series
    prices = pd.Series(100 * np.exp(np.cumsum(daily_returns)), index=dates)
    
    return prices

def test_complexity_analyzer():
    """Test the complexity analyzer with sample data"""
    print("="*60)
    print("Testing Complexity Analyzer")
    print("="*60)
    
    # Initialize analyzer
    analyzer = ComplexityAnalyzer()
    print("✓ Analyzer initialized")
    
    # Generate sample returns for different complexity levels
    print("\nGenerating sample data for different complexity levels...")
    
    # Low complexity strategy (lower returns, lower risk)
    low_complexity_returns = generate_sample_returns(volatility=0.10, drift=0.06)
    print(f"  Low complexity: {len(low_complexity_returns)} days of data")
    
    # Medium complexity strategy (moderate returns, moderate risk)
    med_complexity_returns = generate_sample_returns(volatility=0.15, drift=0.10)
    print(f"  Medium complexity: {len(med_complexity_returns)} days of data")
    
    # High complexity strategy (higher returns, higher risk)
    high_complexity_returns = generate_sample_returns(volatility=0.25, drift=0.15)
    print(f"  High complexity: {len(high_complexity_returns)} days of data")
    
    # Test analyzing each complexity level
    print("\n" + "="*60)
    print("Analyzing Different Complexity Levels")
    print("="*60)
    
    strategy_params = {
        'indicators': ['SMA', 'RSI', 'MACD'],
        'rules': ['crossover', 'divergence'],
        'filters': ['volume', 'volatility']
    }
    
    # Analyze low complexity
    print("\n1. Low Complexity Strategy:")
    print("-" * 40)
    low_score = analyzer.analyze_complexity(low_complexity_returns, strategy_params)
    print(f"   Level: {low_score.level}")
    print(f"   Overall Score: {low_score.overall_score:.2f}")
    print(f"   Sharpe Ratio: {low_score.metrics.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {low_score.metrics.max_drawdown:.2%}")
    print(f"   Volatility: {low_score.metrics.volatility:.2%}")
    print(f"   Win Rate: {low_score.metrics.win_rate:.2%}")
    print(f"   Confidence: {low_score.confidence:.1f}%")
    print(f"   Recommendation: {low_score.recommendation[:100]}...")
    
    # Analyze medium complexity
    print("\n2. Medium Complexity Strategy:")
    print("-" * 40)
    med_score = analyzer.analyze_complexity(med_complexity_returns, strategy_params)
    print(f"   Level: {med_score.level}")
    print(f"   Overall Score: {med_score.overall_score:.2f}")
    print(f"   Sharpe Ratio: {med_score.metrics.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {med_score.metrics.max_drawdown:.2%}")
    print(f"   Volatility: {med_score.metrics.volatility:.2%}")
    print(f"   Win Rate: {med_score.metrics.win_rate:.2%}")
    print(f"   Confidence: {med_score.confidence:.1f}%")
    print(f"   Recommendation: {med_score.recommendation[:100]}...")
    
    # Analyze high complexity
    print("\n3. High Complexity Strategy:")
    print("-" * 40)
    high_score = analyzer.analyze_complexity(high_complexity_returns, strategy_params)
    print(f"   Level: {high_score.level}")
    print(f"   Overall Score: {high_score.overall_score:.2f}")
    print(f"   Sharpe Ratio: {high_score.metrics.sharpe_ratio:.2f}")
    print(f"   Max Drawdown: {high_score.metrics.max_drawdown:.2%}")
    print(f"   Volatility: {high_score.metrics.volatility:.2%}")
    print(f"   Win Rate: {high_score.metrics.win_rate:.2%}")
    print(f"   Confidence: {high_score.confidence:.1f}%")
    print(f"   Recommendation: {high_score.recommendation[:100]}...")
    
    # Test comparison functionality
    print("\n" + "="*60)
    print("Testing Complexity Comparison")
    print("="*60)
    
    returns_dict = {
        3: low_complexity_returns,
        5: med_complexity_returns,
        7: high_complexity_returns
    }
    
    comparison_results = analyzer.compare_complexity_levels(returns_dict, strategy_params)
    
    print("\nComparison Results:")
    print("-" * 40)
    for level, score in comparison_results.items():
        print(f"Level {level}: Score={score.overall_score:.2f}, Sharpe={score.metrics.sharpe_ratio:.2f}")
    
    # Find optimal complexity
    optimal_level, optimal_score = analyzer.find_optimal_complexity(
        returns_dict, strategy_params, risk_preference='balanced'
    )
    
    print(f"\n✓ Optimal Complexity Level: {optimal_level}")
    print(f"  Score: {optimal_score.overall_score:.2f}")
    print(f"  Confidence: {optimal_score.confidence:.1f}%")
    
    print("\n" + "="*60)
    print("✅ All tests passed successfully!")
    print("="*60)
    
    return True

def test_risk_calculator():
    """Test risk-adjusted return calculations"""
    print("\n" + "="*60)
    print("Testing Risk-Adjusted Calculator")
    print("="*60)
    
    from backend.app.services.complexity_optimization_service import RiskAdjustedCalculator
    
    calculator = RiskAdjustedCalculator()
    print("✓ Calculator initialized")
    
    # Generate sample returns
    returns = generate_sample_returns(days=252, volatility=0.20, drift=0.12)
    
    # Calculate risk-adjusted metrics
    metrics = calculator.calculate_risk_adjusted_return(returns)
    
    print("\nRisk-Adjusted Metrics:")
    print("-" * 40)
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'return' in key or 'ratio' in key:
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value:.2%}")
    
    print("\n✅ Risk calculator test passed!")
    return True

if __name__ == "__main__":
    try:
        # Test complexity analyzer
        test_complexity_analyzer()
        
        # Test risk calculator
        test_risk_calculator()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)