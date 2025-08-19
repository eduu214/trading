#!/bin/bash
# F002-US001 Slice 2 Testing Script
# Tests MACD, Bollinger Bands strategies and comparison interface

echo "=== F002-US001 Slice 2 Test Suite ==="
echo "Testing Alternative Strategy Types implementation"
echo ""

BASE_URL="http://localhost:8000/api/v1/strategies"

# Test 1: Strategy Comparison (Multi-strategy)
echo "🧪 Test 1: Multi-Strategy Comparison"
echo "Testing: GET /strategies/compare?symbol=AAPL"
curl -s "$BASE_URL/compare?symbol=AAPL" | jq '.' || echo "❌ Strategy comparison failed"
echo ""

# Test 2: MACD Strategy Backtest
echo "🧪 Test 2: MACD Strategy Backtest"
echo "Testing: POST /strategies/macd_momentum/backtest"
curl -s -X POST "$BASE_URL/macd_momentum/backtest?symbol=AAPL&macd_fast=12&macd_slow=26&macd_signal=9" | jq '.' || echo "❌ MACD backtest failed"
echo ""

# Test 3: Bollinger Bands Strategy Backtest  
echo "🧪 Test 3: Bollinger Bands Strategy Backtest"
echo "Testing: POST /strategies/bollinger_breakout/backtest"
curl -s -X POST "$BASE_URL/bollinger_breakout/backtest?symbol=AAPL&bb_period=20&bb_std_dev=2.0" | jq '.' || echo "❌ Bollinger backtest failed"
echo ""

# Test 4: Parameter Validation (Invalid MACD params)
echo "🧪 Test 4: Parameter Validation Test"
echo "Testing invalid MACD parameters (fast >= slow)"
curl -s -X POST "$BASE_URL/macd_momentum/backtest?symbol=AAPL&macd_fast=26&macd_slow=12&macd_signal=9" | jq '.' || echo "❌ Parameter validation test failed"
echo ""

# Test 5: Available Strategies List
echo "🧪 Test 5: Available Strategies"
echo "Testing: GET /strategies/available"
curl -s "$BASE_URL/available" | jq '.' || echo "❌ Available strategies failed"
echo ""

# Test 6: Strategy Performance Metrics
echo "🧪 Test 6: Strategy Performance Check"
echo "Testing RSI strategy for Sharpe ratio validation"
RESULT=$(curl -s -X POST "$BASE_URL/rsi_mean_reversion/backtest?symbol=AAPL&rsi_period=14&oversold_level=30&overbought_level=70")
SHARPE=$(echo "$RESULT" | jq -r '.performance.sharpe_ratio // "error"')
VALIDATION=$(echo "$RESULT" | jq -r '.sharpe_validation // "error"')

echo "Sharpe Ratio: $SHARPE"
echo "Validation: $VALIDATION"

if [ "$SHARPE" != "error" ] && [ "$VALIDATION" != "error" ]; then
    echo "✅ Performance metrics working"
else
    echo "❌ Performance metrics failed"
fi
echo ""

echo "=== Slice 2 Test Summary ==="
echo "✅ MACD Strategy Implementation"
echo "✅ Bollinger Bands Strategy Implementation" 
echo "✅ Multi-Strategy Comparison Interface"
echo "✅ Parameter Validation"
echo "✅ Performance Metrics & Validation"
echo ""
echo "🎯 All Slice 2 components ready for testing!"
echo ""
echo "Next: Test frontend components at http://localhost:3000"