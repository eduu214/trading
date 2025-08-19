#!/bin/bash

echo "=========================================="
echo "Testing Complexity Optimization API"
echo "=========================================="

# Base URL
BASE_URL="http://localhost:8000/api/v1"

# First, create a test strategy
echo -e "\n1. Creating a test strategy..."
STRATEGY_RESPONSE=$(curl -s -X POST "$BASE_URL/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Complexity Strategy",
    "type": "momentum",
    "status": "discovered",
    "parameters": {
      "indicators": ["SMA", "RSI", "MACD", "BB"],
      "rules": ["crossover", "divergence"],
      "filters": ["volume", "volatility"]
    },
    "total_return": 0.15,
    "sharpe_ratio": 1.2,
    "max_drawdown": -0.08,
    "win_rate": 0.58
  }')

# Extract strategy ID if creation successful
if echo "$STRATEGY_RESPONSE" | grep -q "id"; then
    STRATEGY_ID=$(echo "$STRATEGY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
    echo "✓ Strategy created with ID: $STRATEGY_ID"
else
    echo "Using test ID: 123e4567-e89b-12d3-a456-426614174000"
    STRATEGY_ID="123e4567-e89b-12d3-a456-426614174000"
fi

echo -e "\n2. Testing complexity optimization endpoint..."
OPTIMIZE_RESPONSE=$(curl -s -X POST "$BASE_URL/complexity/optimize" \
  -H "Content-Type: application/json" \
  -d "{
    \"strategy_id\": \"$STRATEGY_ID\",
    \"timeframe\": \"1D\",
    \"lookback_days\": 30,
    \"risk_preference\": \"balanced\"
  }")

echo "Response:"
echo "$OPTIMIZE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$OPTIMIZE_RESPONSE"

# Extract task ID if available
if echo "$OPTIMIZE_RESPONSE" | grep -q "task_id"; then
    TASK_ID=$(echo "$OPTIMIZE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))")
    echo -e "\n✓ Optimization task started with ID: $TASK_ID"
    
    echo -e "\n3. Checking optimization status..."
    sleep 2
    STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/complexity/optimize/$TASK_ID")
    echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
fi

echo -e "\n4. Testing complexity score endpoint..."
SCORE_RESPONSE=$(curl -s -X GET "$BASE_URL/complexity/score/$STRATEGY_ID")
echo "$SCORE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCORE_RESPONSE"

echo -e "\n5. Testing complexity comparison endpoint..."
COMPARE_RESPONSE=$(curl -s -X GET "$BASE_URL/complexity/compare/$STRATEGY_ID?levels=1,3,5,7,9")
echo "$COMPARE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$COMPARE_RESPONSE"

echo -e "\n=========================================="
echo "API Testing Complete"
echo "=========================================="