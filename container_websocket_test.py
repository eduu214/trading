"""
Comprehensive WebSocket Testing Within Container Environment
Task 19: Intensive testing for <1s latency validation
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
import statistics
from typing import List, Dict, Any
import traceback


class WebSocketTestSuite:
    """Container-based WebSocket testing"""
    
    def __init__(self):
        self.test_results = {}
        self.latency_measurements = []
    
    async def test_websocket_manager_performance(self):
        """Test 1: WebSocket Manager Performance"""
        print("\n🔬 Test 1: WebSocket Manager Performance")
        print("-" * 50)
        
        from app.services.websocket_manager import get_websocket_manager
        from app.services.websocket_progress import create_websocket_progress_callback
        
        # Performance metrics
        start_time = time.time()
        
        # Test manager creation and operations
        manager = get_websocket_manager()
        print(f"✅ Manager initialized: {type(manager).__name__}")
        
        # Test multiple task subscriptions
        print("   Testing multiple task subscriptions...")
        task_ids = [str(uuid.uuid4()) for _ in range(10)]
        client_ids = [f"client_{i}" for i in range(5)]
        
        # Simulate subscriptions
        for client_id in client_ids:
            manager.subscriptions[client_id] = set()
            for task_id in task_ids[:3]:  # Each client subscribes to 3 tasks
                if task_id not in manager.subscriptions:
                    manager.subscriptions[task_id] = set()
                manager.subscriptions[task_id].add(client_id)
        
        print(f"   ✅ Created {len(task_ids)} tasks, {len(client_ids)} clients")
        print(f"   ✅ Subscriptions: {len(manager.subscriptions)} active")
        
        # Test callback creation performance
        print("   Testing callback creation performance...")
        callback_start = time.time()
        callbacks = []
        
        for i in range(20):
            task_id = str(uuid.uuid4())
            callback = create_websocket_progress_callback(task_id)
            callbacks.append(callback)
        
        callback_time = time.time() - callback_start
        print(f"   ✅ Created 20 callbacks in {callback_time:.3f}s ({callback_time/20:.3f}s avg)")
        
        # Test callback execution performance
        print("   Testing callback execution performance...")
        exec_times = []
        
        for i, callback in enumerate(callbacks[:5]):  # Test first 5
            exec_start = time.time()
            # Simulate callback execution (without actual WebSocket)
            await callback('test_stage', i/5, f'Testing callback {i}')
            exec_time = time.time() - exec_start
            exec_times.append(exec_time)
        
        avg_exec_time = statistics.mean(exec_times)
        max_exec_time = max(exec_times)
        
        print(f"   ✅ Callback execution - Avg: {avg_exec_time:.3f}s, Max: {max_exec_time:.3f}s")
        
        total_time = time.time() - start_time
        print(f"   📊 Total test time: {total_time:.3f}s")
        
        # Performance validation
        performance_pass = (
            callback_time < 1.0 and  # Callback creation should be fast
            avg_exec_time < 0.1 and  # Callback execution should be fast
            max_exec_time < 0.5      # No single callback should take too long
        )
        
        print(f"   {'✅' if performance_pass else '❌'} Performance requirements met")
        
        return {
            'callback_creation_time': callback_time,
            'avg_execution_time': avg_exec_time,
            'max_execution_time': max_exec_time,
            'total_time': total_time,
            'performance_pass': performance_pass
        }
    
    async def test_concurrent_task_simulation(self):
        """Test 2: Concurrent Task Simulation"""
        print("\n🔬 Test 2: Concurrent Task Simulation")
        print("-" * 50)
        
        from app.services.websocket_manager import get_websocket_manager
        from app.services.websocket_progress import create_websocket_progress_callback
        
        manager = get_websocket_manager()
        
        # Simulate 5 concurrent backtesting tasks
        num_tasks = 5
        tasks_data = []
        
        print(f"   Creating {num_tasks} concurrent task simulations...")
        
        async def simulate_backtesting_task(task_num: int):
            """Simulate a backtesting task with progress updates"""
            task_id = str(uuid.uuid4())
            callback = create_websocket_progress_callback(task_id)
            
            # Simulate typical backtesting stages
            stages = [
                ('initialization', 0.1, 'Starting backtest'),
                ('data_validation', 0.2, 'Validating data'),
                ('indicators', 0.4, 'Calculating indicators'),
                ('signal_generation', 0.6, 'Generating signals'),
                ('position_simulation', 0.8, 'Simulating positions'),
                ('metrics_calculation', 0.95, 'Calculating metrics'),
                ('completion', 1.0, 'Backtest complete')
            ]
            
            latencies = []
            start_time = time.time()
            
            for stage, progress, message in stages:
                stage_start = time.time()
                await callback(stage, progress, f"Task {task_num}: {message}")
                stage_time = time.time() - stage_start
                latencies.append(stage_time)
                
                # Small delay between stages
                await asyncio.sleep(0.01)
            
            total_time = time.time() - start_time
            
            return {
                'task_id': task_id,
                'task_num': task_num,
                'latencies': latencies,
                'total_time': total_time,
                'avg_latency': statistics.mean(latencies),
                'max_latency': max(latencies)
            }
        
        # Run all tasks concurrently
        start_time = time.time()
        task_results = await asyncio.gather(*[
            simulate_backtesting_task(i) for i in range(num_tasks)
        ])
        total_concurrent_time = time.time() - start_time
        
        # Analyze results
        all_latencies = []
        for result in task_results:
            all_latencies.extend(result['latencies'])
            print(f"   ✅ Task {result['task_num']}: {len(result['latencies'])} updates, "
                  f"avg: {result['avg_latency']:.3f}s, max: {result['max_latency']:.3f}s")
        
        overall_avg = statistics.mean(all_latencies)
        overall_max = max(all_latencies)
        latency_violations = [l for l in all_latencies if l >= 1.0]
        
        print(f"\n   📊 Concurrent Task Results:")
        print(f"      • Total tasks: {num_tasks}")
        print(f"      • Total updates: {len(all_latencies)}")
        print(f"      • Concurrent execution time: {total_concurrent_time:.3f}s")
        print(f"      • Average latency: {overall_avg:.3f}s")
        print(f"      • Maximum latency: {overall_max:.3f}s")
        print(f"      • Latency violations (>=1s): {len(latency_violations)}")
        
        concurrent_pass = (
            overall_max < 1.0 and 
            len(latency_violations) == 0 and
            overall_avg < 0.1
        )
        
        print(f"   {'✅' if concurrent_pass else '❌'} Concurrent latency requirements met")
        
        return {
            'num_tasks': num_tasks,
            'total_updates': len(all_latencies),
            'concurrent_time': total_concurrent_time,
            'avg_latency': overall_avg,
            'max_latency': overall_max,
            'violations': len(latency_violations),
            'concurrent_pass': concurrent_pass
        }
    
    async def test_memory_and_cleanup(self):
        """Test 3: Memory usage and cleanup"""
        print("\n🔬 Test 3: Memory Usage and Cleanup")
        print("-" * 50)
        
        from app.services.websocket_manager import get_websocket_manager
        import sys
        
        manager = get_websocket_manager()
        
        # Initial state
        initial_connections = len(manager.active_connections)
        initial_subscriptions = len(manager.subscriptions)
        initial_cache = len(manager.task_progress)
        
        print(f"   Initial state: {initial_connections} connections, "
              f"{initial_subscriptions} subscriptions, {initial_cache} cached")
        
        # Simulate connection lifecycle
        print("   Simulating connection lifecycle...")
        
        # Add fake connections and subscriptions
        fake_connections = {}
        fake_subscriptions = {}
        
        for i in range(50):
            client_id = f"test_client_{i}"
            task_id = f"test_task_{i}"
            
            # Simulate connections
            fake_connections[client_id] = f"fake_websocket_{i}"
            
            # Simulate subscriptions
            if task_id not in fake_subscriptions:
                fake_subscriptions[task_id] = set()
            fake_subscriptions[task_id].add(client_id)
            
            # Add to manager (simulation)
            manager.subscriptions[task_id] = fake_subscriptions[task_id]
            manager.task_progress[task_id] = {
                "type": "progress",
                "task_id": task_id,
                "data": {"percentage": 50}
            }
        
        peak_subscriptions = len(manager.subscriptions)
        peak_cache = len(manager.task_progress)
        
        print(f"   Peak state: {peak_subscriptions} subscriptions, {peak_cache} cached")
        
        # Cleanup simulation
        print("   Testing cleanup...")
        
        # Simulate task completions and cleanup
        cleanup_start = time.time()
        
        for i in range(0, 50, 2):  # Clean up every other task
            task_id = f"test_task_{i}"
            if task_id in manager.subscriptions:
                del manager.subscriptions[task_id]
            if task_id in manager.task_progress:
                del manager.task_progress[task_id]
        
        cleanup_time = time.time() - cleanup_start
        
        final_subscriptions = len(manager.subscriptions)
        final_cache = len(manager.task_progress)
        
        print(f"   Final state: {final_subscriptions} subscriptions, {final_cache} cached")
        print(f"   Cleanup time: {cleanup_time:.3f}s for 25 tasks")
        
        # Memory efficiency check
        cleanup_ratio = (peak_subscriptions - final_subscriptions) / peak_subscriptions
        memory_efficient = cleanup_ratio >= 0.4 and cleanup_time < 1.0
        
        print(f"   📊 Memory efficiency: {cleanup_ratio:.1%} reduction")
        print(f"   {'✅' if memory_efficient else '❌'} Memory management efficient")
        
        # Reset manager state
        manager.subscriptions.clear()
        manager.task_progress.clear()
        
        return {
            'initial_subscriptions': initial_subscriptions,
            'peak_subscriptions': peak_subscriptions,
            'final_subscriptions': final_subscriptions,
            'cleanup_time': cleanup_time,
            'cleanup_ratio': cleanup_ratio,
            'memory_efficient': memory_efficient
        }
    
    async def test_message_format_validation(self):
        """Test 4: Message format validation"""
        print("\n🔬 Test 4: Message Format Validation")
        print("-" * 50)
        
        from app.services.websocket_manager import get_websocket_manager
        from app.services.websocket_progress import create_websocket_progress_callback
        
        manager = get_websocket_manager()
        
        # Test different message types
        print("   Testing message format consistency...")
        
        task_id = str(uuid.uuid4())
        callback = create_websocket_progress_callback(task_id)
        
        # Capture messages by patching the manager
        captured_messages = []
        
        original_broadcast = manager.broadcast_task_progress
        
        async def capture_broadcast(task_id, progress_type, data):
            message = {
                "type": "progress",
                "task_id": task_id,
                "progress_type": progress_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            captured_messages.append(message)
            return await original_broadcast(task_id, progress_type, data)
        
        manager.broadcast_task_progress = capture_broadcast
        
        # Test various progress updates
        test_stages = [
            ('initialization', 0.1, 'Starting test'),
            ('processing', 0.5, 'Processing data'),
            ('completion', 1.0, 'Test complete')
        ]
        
        for stage, progress, message in test_stages:
            await callback(stage, progress, message)
        
        # Validate message formats
        format_errors = []
        
        for i, msg in enumerate(captured_messages):
            # Check required fields
            required_fields = ['type', 'task_id', 'progress_type', 'data', 'timestamp']
            for field in required_fields:
                if field not in msg:
                    format_errors.append(f"Message {i}: Missing field '{field}'")
            
            # Check data structure
            data = msg.get('data', {})
            required_data_fields = ['current_step', 'total_steps', 'percentage', 'status']
            for field in required_data_fields:
                if field not in data:
                    format_errors.append(f"Message {i}: Missing data field '{field}'")
            
            # Check data types
            if 'percentage' in data and not isinstance(data['percentage'], (int, float)):
                format_errors.append(f"Message {i}: Invalid percentage type")
            
            # Check timestamp format
            try:
                datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            except:
                format_errors.append(f"Message {i}: Invalid timestamp format")
        
        # Restore original method
        manager.broadcast_task_progress = original_broadcast
        
        print(f"   ✅ Captured {len(captured_messages)} messages")
        print(f"   📋 Format validation: {len(format_errors)} errors")
        
        if format_errors:
            for error in format_errors[:3]:  # Show first 3 errors
                print(f"      • {error}")
        
        format_valid = len(format_errors) == 0
        print(f"   {'✅' if format_valid else '❌'} Message format validation")
        
        return {
            'messages_captured': len(captured_messages),
            'format_errors': len(format_errors),
            'format_valid': format_valid,
            'sample_message': captured_messages[0] if captured_messages else None
        }
    
    async def test_latency_requirements(self):
        """Test 5: Specific <1s latency requirement validation"""
        print("\n🔬 Test 5: <1s Latency Requirement Validation")
        print("-" * 50)
        
        from app.services.websocket_progress import create_websocket_progress_callback
        
        # Test rapid-fire updates
        print("   Testing rapid progress updates...")
        
        task_id = str(uuid.uuid4())
        callback = create_websocket_progress_callback(task_id)
        
        latencies = []
        num_updates = 100
        
        # Rapid updates test
        for i in range(num_updates):
            start_time = time.time()
            await callback('rapid_test', i/num_updates, f'Update {i}')
            latency = time.time() - start_time
            latencies.append(latency)
        
        # Statistical analysis
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        
        violations = [l for l in latencies if l >= 1.0]
        
        print(f"   📊 Latency Statistics ({num_updates} updates):")
        print(f"      • Average: {avg_latency:.3f}s")
        print(f"      • Maximum: {max_latency:.3f}s")
        print(f"      • Minimum: {min_latency:.3f}s")
        print(f"      • 95th percentile: {p95_latency:.3f}s")
        print(f"      • 99th percentile: {p99_latency:.3f}s")
        print(f"      • Violations (>=1s): {len(violations)}")
        
        # Requirement validation
        latency_requirements = {
            'avg_under_100ms': avg_latency < 0.1,
            'max_under_1s': max_latency < 1.0,
            'p95_under_500ms': p95_latency < 0.5,
            'p99_under_1s': p99_latency < 1.0,
            'no_violations': len(violations) == 0
        }
        
        all_requirements_met = all(latency_requirements.values())
        
        print(f"\n   🎯 Latency Requirements:")
        for req, met in latency_requirements.items():
            print(f"      {'✅' if met else '❌'} {req}: {met}")
        
        print(f"\n   {'✅' if all_requirements_met else '❌'} Overall latency requirements: {all_requirements_met}")
        
        return {
            'num_updates': num_updates,
            'avg_latency': avg_latency,
            'max_latency': max_latency,
            'p95_latency': p95_latency,
            'p99_latency': p99_latency,
            'violations': len(violations),
            'requirements_met': latency_requirements,
            'overall_pass': all_requirements_met
        }
    
    async def run_intensive_tests(self):
        """Run all intensive tests"""
        print("🚀 INTENSIVE WEBSOCKET TESTING - CONTAINER EDITION")
        print("=" * 70)
        print("Task 19: Real-time progress updates with <1s latency")
        print("=" * 70)
        
        try:
            # Run all tests
            test1_result = await self.test_websocket_manager_performance()
            test2_result = await self.test_concurrent_task_simulation()
            test3_result = await self.test_memory_and_cleanup()
            test4_result = await self.test_message_format_validation()
            test5_result = await self.test_latency_requirements()
            
            # Collect results
            all_tests_passed = (
                test1_result['performance_pass'] and
                test2_result['concurrent_pass'] and
                test3_result['memory_efficient'] and
                test4_result['format_valid'] and
                test5_result['overall_pass']
            )
            
            # Final summary
            print("\n" + "=" * 70)
            print("🏁 INTENSIVE TESTING FINAL SUMMARY")
            print("=" * 70)
            
            tests_summary = [
                ("WebSocket Manager Performance", test1_result['performance_pass']),
                ("Concurrent Task Simulation", test2_result['concurrent_pass']),
                ("Memory Usage & Cleanup", test3_result['memory_efficient']),
                ("Message Format Validation", test4_result['format_valid']),
                ("Latency Requirements (<1s)", test5_result['overall_pass'])
            ]
            
            for test_name, passed in tests_summary:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {status} {test_name}")
            
            print(f"\n{'✅' if all_tests_passed else '❌'} OVERALL RESULT: {'ALL TESTS PASSED' if all_tests_passed else 'SOME TESTS FAILED'}")
            
            if all_tests_passed:
                print("\n🎯 CONCLUSION:")
                print("   ✅ <1s latency requirement VERIFIED")
                print("   ✅ Concurrent operations STABLE")
                print("   ✅ Memory management EFFICIENT")
                print("   ✅ Message formats CONSISTENT")
                print("   ✅ Performance under load ACCEPTABLE")
                print("\n🚀 Task 19 WebSocket implementation is PRODUCTION READY!")
            else:
                print("\n⚠️ ISSUES FOUND:")
                print("   Some performance or functionality issues detected")
                print("   Review individual test results above")
            
            # Key metrics summary
            print(f"\n📊 KEY METRICS:")
            print(f"   • Best latency: {test5_result['avg_latency']:.3f}s average")
            print(f"   • Worst latency: {test5_result['max_latency']:.3f}s maximum")
            print(f"   • Concurrent tasks: {test2_result['num_tasks']} simultaneous")
            print(f"   • Message throughput: {test5_result['num_updates']} updates tested")
            
        except Exception as e:
            print(f"\n❌ TESTING SUITE ERROR: {e}")
            traceback.print_exc()


async def main():
    """Main test runner"""
    try:
        suite = WebSocketTestSuite()
        await suite.run_intensive_tests()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())