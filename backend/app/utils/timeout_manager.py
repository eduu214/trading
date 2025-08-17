"""
Timeout management for scans and long-running operations
"""
import asyncio
import time
from typing import Any, Optional, Callable, Dict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class TimeoutType(Enum):
    API_CALL = "api_call"
    SCAN_OPERATION = "scan_operation"
    DATA_PROCESSING = "data_processing"
    VALIDATION = "validation"

class TimeoutConfig:
    """Configuration for different timeout scenarios"""
    
    DEFAULT_TIMEOUTS = {
        TimeoutType.API_CALL: 30,      # 30 seconds for API calls
        TimeoutType.SCAN_OPERATION: 300,  # 5 minutes for full scan
        TimeoutType.DATA_PROCESSING: 60,  # 1 minute for processing
        TimeoutType.VALIDATION: 10,    # 10 seconds for validation
    }
    
    def __init__(self, custom_timeouts: Dict[TimeoutType, int] = None):
        self.timeouts = self.DEFAULT_TIMEOUTS.copy()
        if custom_timeouts:
            self.timeouts.update(custom_timeouts)
    
    def get_timeout(self, timeout_type: TimeoutType) -> int:
        return self.timeouts.get(timeout_type, 30)

class OperationTracker:
    """Track long-running operations"""
    
    def __init__(self):
        self.operations: Dict[str, Dict] = {}
        self.next_id = 1
    
    def start_operation(self, 
                       operation_type: str,
                       timeout: int,
                       metadata: Dict = None) -> str:
        """Start tracking an operation"""
        operation_id = f"op_{self.next_id}"
        self.next_id += 1
        
        self.operations[operation_id] = {
            "type": operation_type,
            "start_time": datetime.now(),
            "timeout": timeout,
            "deadline": datetime.now() + timedelta(seconds=timeout),
            "metadata": metadata or {},
            "status": "running"
        }
        
        logger.info(
            f"Started operation {operation_id} ({operation_type}) "
            f"with {timeout}s timeout"
        )
        
        return operation_id
    
    def finish_operation(self, operation_id: str, status: str = "completed"):
        """Mark operation as finished"""
        if operation_id in self.operations:
            self.operations[operation_id]["status"] = status
            self.operations[operation_id]["end_time"] = datetime.now()
            
            duration = (
                self.operations[operation_id]["end_time"] - 
                self.operations[operation_id]["start_time"]
            ).total_seconds()
            
            logger.info(
                f"Operation {operation_id} {status} after {duration:.2f}s"
            )
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict]:
        """Get status of an operation"""
        return self.operations.get(operation_id)
    
    def check_timeout(self, operation_id: str) -> bool:
        """Check if operation has timed out"""
        if operation_id in self.operations:
            op = self.operations[operation_id]
            if op["status"] == "running":
                return datetime.now() > op["deadline"]
        return False
    
    def get_remaining_time(self, operation_id: str) -> Optional[float]:
        """Get remaining time for operation"""
        if operation_id in self.operations:
            op = self.operations[operation_id]
            if op["status"] == "running":
                remaining = (op["deadline"] - datetime.now()).total_seconds()
                return max(0, remaining)
        return None
    
    def cleanup_finished_operations(self, max_age_hours: int = 24):
        """Clean up old finished operations"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for op_id, op_data in self.operations.items():
            if (op_data["status"] != "running" and 
                op_data.get("end_time", datetime.now()) < cutoff):
                to_remove.append(op_id)
        
        for op_id in to_remove:
            del self.operations[op_id]

class TimeoutManager:
    """Manage timeouts for various operations"""
    
    def __init__(self, config: TimeoutConfig = None):
        self.config = config or TimeoutConfig()
        self.tracker = OperationTracker()
    
    @asynccontextmanager
    async def timeout_operation(self, 
                               timeout_type: TimeoutType,
                               operation_name: str = None,
                               custom_timeout: int = None):
        """Context manager for timeout operations"""
        timeout_seconds = custom_timeout or self.config.get_timeout(timeout_type)
        op_name = operation_name or timeout_type.value
        
        operation_id = self.tracker.start_operation(
            op_name, 
            timeout_seconds,
            {"timeout_type": timeout_type.value}
        )
        
        try:
            async with asyncio.timeout(timeout_seconds):
                yield operation_id
            
            self.tracker.finish_operation(operation_id, "completed")
            
        except asyncio.TimeoutError:
            self.tracker.finish_operation(operation_id, "timeout")
            logger.error(f"Operation {operation_id} timed out after {timeout_seconds}s")
            raise
        except Exception as e:
            self.tracker.finish_operation(operation_id, "error")
            logger.error(f"Operation {operation_id} failed: {e}")
            raise
    
    async def with_timeout(self,
                          coro,
                          timeout_type: TimeoutType,
                          operation_name: str = None,
                          custom_timeout: int = None) -> Any:
        """Execute coroutine with timeout"""
        async with self.timeout_operation(
            timeout_type, operation_name, custom_timeout
        ) as operation_id:
            return await coro
    
    def check_operation_timeout(self, operation_id: str) -> bool:
        """Check if specific operation has timed out"""
        return self.tracker.check_timeout(operation_id)
    
    def get_operation_progress(self, operation_id: str) -> Optional[Dict]:
        """Get progress information for operation"""
        op_data = self.tracker.get_operation_status(operation_id)
        if not op_data:
            return None
        
        remaining = self.tracker.get_remaining_time(operation_id)
        elapsed = (datetime.now() - op_data["start_time"]).total_seconds()
        
        return {
            "operation_id": operation_id,
            "type": op_data["type"],
            "status": op_data["status"],
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "timeout_seconds": op_data["timeout"],
            "progress_percent": min(100, (elapsed / op_data["timeout"]) * 100) if remaining else 100
        }

class ScanTimeoutManager:
    """Specialized timeout manager for market scans"""
    
    def __init__(self):
        self.timeout_manager = TimeoutManager()
        self.scan_stages = {
            "initialization": 30,      # 30 seconds to start
            "data_collection": 180,    # 3 minutes to collect data
            "analysis": 120,           # 2 minutes for analysis
            "correlation": 60,         # 1 minute for correlation
            "ranking": 30,             # 30 seconds for ranking
            "finalization": 30,        # 30 seconds to finish
        }
    
    async def execute_scan_with_timeouts(self, 
                                       scan_func: Callable,
                                       scan_config: Dict,
                                       progress_callback: Callable = None) -> Any:
        """Execute a scan with per-stage timeouts"""
        
        total_timeout = sum(self.scan_stages.values())
        
        async with self.timeout_manager.timeout_operation(
            TimeoutType.SCAN_OPERATION,
            "full_market_scan",
            total_timeout
        ) as scan_id:
            
            if progress_callback:
                await progress_callback({
                    "stage": "starting",
                    "progress": 0,
                    "scan_id": scan_id
                })
            
            try:
                result = await scan_func(scan_config, scan_id, progress_callback)
                
                if progress_callback:
                    await progress_callback({
                        "stage": "completed",
                        "progress": 100,
                        "scan_id": scan_id
                    })
                
                return result
                
            except asyncio.TimeoutError:
                if progress_callback:
                    await progress_callback({
                        "stage": "timeout",
                        "progress": -1,
                        "scan_id": scan_id,
                        "error": f"Scan timed out after {total_timeout} seconds"
                    })
                raise
    
    async def execute_stage_with_timeout(self,
                                       stage_name: str,
                                       stage_func: Callable,
                                       *args,
                                       **kwargs) -> Any:
        """Execute a scan stage with specific timeout"""
        timeout = self.scan_stages.get(stage_name, 60)
        
        async with self.timeout_manager.timeout_operation(
            TimeoutType.DATA_PROCESSING,
            f"scan_stage_{stage_name}",
            timeout
        ):
            return await stage_func(*args, **kwargs)

# Global timeout manager
timeout_manager = TimeoutManager()
scan_timeout_manager = ScanTimeoutManager()

async def with_timeout(coro, timeout_seconds: int, operation_name: str = None):
    """Simple timeout wrapper"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"Operation '{operation_name or 'unknown'}' timed out after {timeout_seconds}s")
        raise

async def timeout_after(seconds: int):
    """Simple timeout utility"""
    await asyncio.sleep(seconds)
    raise asyncio.TimeoutError(f"Operation timed out after {seconds} seconds")