#!/bin/bash

echo "========================================="
echo "Testing AlphaStrat Scanner"
echo "========================================="

# Test 1: Check scanner status
echo -e "\n1. Checking scanner status..."
curl -s http://localhost:8000/api/v1/scanner/status | python3 -m json.tool

# Test 2: Get mock opportunities
echo -e "\n2. Fetching mock opportunities..."
curl -s http://localhost:8000/api/v1/scanner/test-mock | python3 -c "
import json
import sys
data = json.load(sys.stdin)
print(f\"Status: {data['status']}\")
print(f\"Opportunities found: {data['opportunities_found']}\")
print(f\"\\nTop 3 opportunities:\")
for opp in data['opportunities'][:3]:
    print(f\"  - {opp['ticker']} ({opp['asset_class']}): {opp['signal_strength']:.1f}% signal\")
print(f\"\\nUncorrelated pairs: {len(data.get('uncorrelated_pairs', []))}\")
"

# Test 3: Trigger a scan
echo -e "\n3. Triggering a market scan..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/scanner/scan \
  -H "Content-Type: application/json" \
  -d '{
    "asset_classes": ["equities", "futures", "fx"],
    "min_volume": 500000,
    "min_price_change": 0.01,
    "correlation_threshold": 0.3
  }')

echo "$RESPONSE" | python3 -m json.tool

# Test 4: Check frontend
echo -e "\n4. Checking frontend status..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/scanner)
if [ "$FRONTEND_STATUS" == "200" ]; then
    echo "✅ Frontend scanner page is accessible"
else
    echo "❌ Frontend scanner page returned status: $FRONTEND_STATUS"
fi

echo -e "\n========================================="
echo "Testing Complete!"
echo "========================================="
echo ""
echo "Access the scanner at:"
echo "  Frontend: http://localhost:3000/scanner"
echo "  API Docs: http://localhost:8000/docs"
echo ""