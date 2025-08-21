#!/usr/bin/env python3
"""
Test the MPT optimization engine directly
"""
import sys
import os

# Add the backend directory to Python path
sys.path.append('/home/jack/dev/trading/backend')

from app.services.mpt_optimization_engine import get_mpt_engine

def test_mpt_optimization():
    """Test MPT optimization functionality"""
    print("Testing MPT Optimization Engine...")
    
    try:
        # Get the engine
        mpt_engine = get_mpt_engine()
        print("✅ MPT engine initialized")
        
        # Get sample strategy returns
        strategy_returns = mpt_engine.get_strategy_returns_data("main", window_days=100)
        print(f"✅ Strategy returns data: {strategy_returns.shape}")
        print(f"   Strategies: {list(strategy_returns.columns)}")
        
        # Test portfolio optimization
        result = mpt_engine.optimize_portfolio(
            strategy_returns=strategy_returns,
            optimization_method="max_sharpe"
        )
        
        if result.get('success'):
            print("✅ Portfolio optimization successful")
            print(f"   Optimal weights: {result['optimal_weights']}")
            print(f"   Expected return: {result['performance_metrics']['expected_annual_return']:.2%}")
            print(f"   Volatility: {result['performance_metrics']['annual_volatility']:.2%}")
            print(f"   Sharpe ratio: {result['performance_metrics']['sharpe_ratio']:.2f}")
        else:
            print(f"❌ Portfolio optimization failed: {result.get('error')}")
            return False
        
        # Test efficient frontier calculation
        print("\nTesting efficient frontier calculation...")
        frontier_result = mpt_engine.calculate_efficient_frontier(
            strategy_returns=strategy_returns,
            n_points=3
        )
        
        print(f"✅ Efficient frontier calculated")
        print(f"   Frontier points: {len(frontier_result['frontier_points'])}")
        print(f"   Optimal portfolios: {list(frontier_result['optimal_portfolios'].keys())}")
        
        # Show sample frontier point
        if frontier_result['frontier_points']:
            sample_point = frontier_result['frontier_points'][0]
            print(f"   Sample point - Return: {sample_point['expected_return']:.2%}, Vol: {sample_point['volatility']:.2%}")
        
        print("\n🎉 All MPT tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MPT test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mpt_optimization()
    sys.exit(0 if success else 1)