#!/bin/bash

echo "=== FlowPlane App Status Check ==="
echo ""

# Check if ports are listening
echo "Checking port status..."
echo "------------------------"
ss -tuln | grep -E "(3000|8000|5432|6379)" | while read line; do
    if echo "$line" | grep -q ":3000"; then
        echo "✓ Frontend (port 3000): LISTENING"
    elif echo "$line" | grep -q ":8000"; then
        echo "✓ Backend API (port 8000): LISTENING"
    elif echo "$line" | grep -q ":5432"; then
        echo "✓ PostgreSQL (port 5432): LISTENING"
    elif echo "$line" | grep -q ":6379"; then
        echo "✓ Redis (port 6379): LISTENING"
    fi
done

echo ""
echo "Testing service endpoints..."
echo "----------------------------"

# Test Frontend
echo -n "Frontend (http://localhost:3000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ | grep -q "200"; then
    echo "✓ WORKING"
else
    echo "✗ NOT RESPONDING"
fi

# Test Backend API
echo -n "Backend API (http://localhost:8000): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✓ WORKING"
elif [ "$response" = "000" ]; then
    echo "✗ CONNECTION REFUSED/RESET"
else
    echo "✗ HTTP $response"
fi

# Test API Docs
echo -n "API Docs (http://localhost:8000/docs): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✓ WORKING"
elif [ "$response" = "000" ]; then
    echo "✗ CONNECTION REFUSED/RESET"
else
    echo "✗ HTTP $response"
fi

echo ""
echo "Docker commands to check logs (run in a terminal with Docker access):"
echo "----------------------------------------------------------------------"
echo "docker logs flowplane-backend       # Check backend logs"
echo "docker logs flowplane-frontend      # Check frontend logs"
echo "docker logs flowplane-postgres      # Check database logs"
echo "docker logs flowplane-redis         # Check Redis logs"
echo ""
echo "docker-compose logs backend         # Alternative: Check backend logs"
echo "docker-compose restart backend      # Restart backend if needed"
echo ""
echo "=== Status Check Complete ===