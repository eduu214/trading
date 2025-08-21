"""
WebSocket Progress Callback for Backtesting
Task 19: Real-time progress updates with <1s latency
"""
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.websocket_manager import get_websocket_manager
import asyncio


class WebSocketProgressCallback:
    """Progress callback that sends updates via WebSocket"""
    
    def __init__(self, task_id: str):
        """
        Initialize WebSocket progress callback
        
        Args:
            task_id: Unique identifier for the backtesting task
        """
        self.task_id = task_id
        self.manager = get_websocket_manager()
        self.start_time = datetime.utcnow()
        self.current_step = 0
        self.total_steps = 100  # Percentage based
        
        # Stage to step mapping
        self.stage_steps = {
            "initialization": 10,
            "data_validation": 20,
            "indicators": 40,
            "signal_generation": 60,
            "position_simulation": 80,
            "metrics_calculation": 90,
            "completion": 100
        }
    
    async def __call__(self, stage: str, progress: float, details: str = ""):
        """
        Send progress update via WebSocket
        
        Args:
            stage: Current stage of backtesting
            progress: Progress percentage (0.0 to 1.0)
            details: Additional details about current operation
        """
        # Calculate current step based on stage
        if stage in self.stage_steps:
            self.current_step = self.stage_steps[stage]
        else:
            # Use progress percentage if stage not mapped
            self.current_step = int(progress * 100)
        
        # Calculate elapsed time
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Prepare progress data
        progress_details = {
            "stage": stage,
            "message": details,
            "elapsed_seconds": round(elapsed, 2),
            "estimated_remaining": self._estimate_remaining_time(elapsed, progress)
        }
        
        # Send via WebSocket (ensures <1s latency)
        await self.manager.send_backtesting_progress(
            task_id=self.task_id,
            current_step=self.current_step,
            total_steps=self.total_steps,
            status=stage,
            details=progress_details
        )
    
    def _estimate_remaining_time(self, elapsed: float, progress: float) -> Optional[float]:
        """Estimate remaining time based on current progress"""
        if progress > 0 and progress < 1:
            total_estimated = elapsed / progress
            remaining = total_estimated - elapsed
            return round(remaining, 2)
        return None
    
    async def send_completion(
        self,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Send completion notification"""
        await self.manager.send_completion_notification(
            task_id=self.task_id,
            success=success,
            result=result,
            error=error
        )


class IndicatorProgressCallback:
    """Progress callback for indicator calculations"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.manager = get_websocket_manager()
    
    async def __call__(self, indicator: str, symbol: str, percentage: float):
        """Send indicator calculation progress"""
        await self.manager.send_indicator_calculation_progress(
            task_id=self.task_id,
            indicator=indicator,
            symbol=symbol,
            percentage=percentage
        )


class ValidationProgressCallback:
    """Progress callback for strategy validation"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.manager = get_websocket_manager()
    
    async def __call__(
        self,
        validation_type: str,
        passed: bool,
        message: str,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Send validation progress update"""
        await self.manager.send_validation_progress(
            task_id=self.task_id,
            validation_type=validation_type,
            passed=passed,
            message=message,
            metrics=metrics
        )


def create_websocket_progress_callback(task_id: str) -> WebSocketProgressCallback:
    """Factory function to create WebSocket progress callback"""
    return WebSocketProgressCallback(task_id)