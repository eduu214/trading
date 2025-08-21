#!/usr/bin/env python3
"""
Test script for WebSocket real-time progress updates
Task 19: Validates <1s latency requirement
"""
import asyncio
import json
import websockets
import aiohttp
import sys
from datetime import datetime


async def test_websocket_progress():
    """Test WebSocket progress updates for backtesting"""
    
    print("🚀 Testing WebSocket Progress Updates (Task 19)")
    print("=" * 50)
    
    # Step 1: Start a backtest with progress
    print("\n1️⃣ Starting backtest with progress tracking...")
    
    async with aiohttp.ClientSession() as session:
        # Start backtest
        url = "http://localhost:8000/api/v1/strategies/rsi_mean_reversion/backtest-with-progress?symbol=AAPL"
        
        try:
            async with session.post(url) as response:
                if response.status != 200:
                    text = await response.text()
                    print(f"❌ Failed to start backtest: {text}")
                    return
                    
                data = await response.json()
                task_id = data.get("task_id")
                print(f"✅ Backtest started with task_id: {task_id}")
                print(f"   Strategy: {data.get('strategy')}")
                print(f"   Symbol: {data.get('symbol')}")
        except Exception as e:
            print(f"❌ Error starting backtest: {e}")
            return
    
    # Step 2: Connect to WebSocket and subscribe
    print("\n2️⃣ Connecting to WebSocket for real-time updates...")
    
    ws_url = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected to WebSocket")
            
            # Wait for connection confirmation
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"   Connection confirmed: {connection_data.get('status')}")
            client_id = connection_data.get('client_id')
            
            # Subscribe to task progress
            print(f"\n3️⃣ Subscribing to task {task_id}...")
            subscribe_msg = json.dumps({
                "type": "subscribe",
                "task_id": task_id
            })
            await websocket.send(subscribe_msg)
            
            # Track latency
            last_update = datetime.now()
            update_count = 0
            max_latency = 0
            
            print("\n4️⃣ Receiving real-time progress updates:")
            print("-" * 40)
            
            # Receive progress updates
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    # Calculate latency
                    now = datetime.now()
                    latency = (now - last_update).total_seconds()
                    max_latency = max(max_latency, latency)
                    last_update = now
                    update_count += 1
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "subscription_confirmed":
                        print(f"✅ Subscription confirmed for task {data.get('task_id')}")
                    
                    elif msg_type == "progress":
                        progress_data = data.get("data", {})
                        percentage = progress_data.get("percentage", 0)
                        status = progress_data.get("status", "")
                        details = progress_data.get("details", {})
                        
                        # Progress bar
                        bar_length = 30
                        filled = int(bar_length * percentage / 100)
                        bar = "█" * filled + "░" * (bar_length - filled)
                        
                        print(f"⏳ [{bar}] {percentage:5.1f}% - {status}")
                        
                        if details.get("message"):
                            print(f"   📝 {details['message']}")
                        
                        # Show latency (should be <1s per requirement)
                        latency_status = "✅" if latency < 1.0 else "⚠️"
                        print(f"   {latency_status} Latency: {latency:.3f}s")
                    
                    elif msg_type == "completion":
                        print("\n" + "=" * 40)
                        if data.get("success"):
                            print("✅ BACKTEST COMPLETED SUCCESSFULLY!")
                            result = data.get("result", {})
                            metrics = result.get("metrics", {})
                            
                            print(f"\n📊 Results for {result.get('strategy')} on {result.get('symbol')}:")
                            print(f"   • Total Return: {metrics.get('total_return', 0):.2%}")
                            print(f"   • Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                            print(f"   • Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                            print(f"   • Win Rate: {metrics.get('win_rate', 0):.2%}")
                            print(f"   • Total Trades: {metrics.get('total_trades', 0)}")
                            print(f"   • Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                            
                            validation = "✅ PASSED" if result.get("validation_passed") else "❌ FAILED"
                            print(f"\n   Validation (Sharpe > 1.0): {validation}")
                        else:
                            print(f"❌ BACKTEST FAILED: {data.get('error')}")
                        
                        # Final latency report
                        print(f"\n📈 WebSocket Performance Stats:")
                        print(f"   • Total Updates: {update_count}")
                        print(f"   • Max Latency: {max_latency:.3f}s")
                        print(f"   • Requirement: <1s latency")
                        
                        if max_latency < 1.0:
                            print(f"   ✅ LATENCY REQUIREMENT MET!")
                        else:
                            print(f"   ⚠️ Latency exceeded 1s (max: {max_latency:.3f}s)")
                        
                        break
                        
                except asyncio.TimeoutError:
                    print("\n⚠️ Timeout waiting for updates (30s)")
                    break
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    print("=" * 50)
    print("WebSocket Real-Time Progress Test")
    print("Task 19: <1s Latency Requirement")
    print("=" * 50)
    
    try:
        asyncio.run(test_websocket_progress())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)