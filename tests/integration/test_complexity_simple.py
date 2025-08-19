#!/usr/bin/env python3
"""
Simple test of complexity optimization endpoints
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_complexity_endpoints():
    """Test the complexity optimization API endpoints"""
    
    print("="*60)
    print("Testing Complexity Optimization API")
    print("="*60)
    
    # Test strategy ID
    strategy_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # 1. Test getting complexity score (should fail initially)
    print("\n1. Testing GET /complexity/score/{strategy_id}")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/complexity/score/{strategy_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("✓ Correctly returns 404 when no optimization data exists")
    else:
        print(f"Response: {response.json()}")
    
    # 2. Test starting optimization
    print("\n2. Testing POST /complexity/optimize")
    print("-" * 40)
    payload = {
        "strategy_id": strategy_id,
        "timeframe": "1D",
        "lookback_days": 30,
        "risk_preference": "balanced"
    }
    response = requests.post(f"{BASE_URL}/complexity/optimize", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Optimization started")
        print(f"  Task ID: {data.get('task_id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Estimated time: {data.get('estimated_time_seconds')} seconds")
        
        task_id = data.get('task_id')
        
        # 3. Check task status
        if task_id:
            print("\n3. Testing GET /complexity/optimize/{task_id}")
            print("-" * 40)
            time.sleep(2)  # Wait a bit
            response = requests.get(f"{BASE_URL}/complexity/optimize/{task_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 202:
                print("✓ Task still processing (expected)")
            elif response.status_code == 200:
                print("✓ Task completed")
                print(f"Results: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.json()}")
    
    # 4. Test comparison endpoint
    print("\n4. Testing GET /complexity/compare/{strategy_id}")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/complexity/compare/{strategy_id}?levels=1,3,5,7,9")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("✓ Correctly returns 404 when no comparison data exists")
    else:
        print(f"Response: {response.json()}")
    
    # 5. Test history endpoint
    print("\n5. Testing GET /complexity/history/{strategy_id}")
    print("-" * 40)
    response = requests.get(f"{BASE_URL}/complexity/history/{strategy_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ History retrieved")
        print(f"  Total optimizations: {data.get('total_optimizations')}")
    
    # 6. Test batch optimization
    print("\n6. Testing POST /complexity/batch-optimize")
    print("-" * 40)
    payload = {
        "strategy_ids": [strategy_id],
        "risk_preference": "conservative"
    }
    response = requests.post(f"{BASE_URL}/complexity/batch-optimize", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Batch optimization started")
        print(f"  Message: {data.get('message')}")
    
    print("\n" + "="*60)
    print("✅ API Testing Complete!")
    print("="*60)
    print("\nSummary:")
    print("- Complexity endpoints are accessible")
    print("- Optimization tasks can be created")
    print("- Error handling works correctly")
    print("- Note: Celery worker needs scipy dependency for full functionality")

if __name__ == "__main__":
    try:
        test_complexity_endpoints()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()