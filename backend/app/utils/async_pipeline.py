"""
High-performance async processing pipelines for market data and analysis
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    DATA_FETCH = "data_fetch"
    VALIDATION = "validation"
    ANALYSIS = "analysis"
    CORRELATION = "correlation"
    RANKING = "ranking"
    STORAGE = "storage"

@dataclass
class PipelineTask:
    """Represents a task in the processing pipeline"""
    id: str
    data: Any
    stage: PipelineStage
    priority: int = 0
    created_at: float = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PipelineResult:
    """Result from pipeline processing"""
    task_id: str
    success: bool
    data: Any = None
    error: str = None
    duration: float = 0
    stage: PipelineStage = None

class AsyncQueue:
    """High-performance async queue with priority support"""
    
    def __init__(self, maxsize: int = 0):
        self.maxsize = maxsize
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
        self._task_counter = 0
        self._stats = {
            "items_processed": 0,
            "total_wait_time": 0,
            "avg_wait_time": 0
        }
    
    async def put(self, item: PipelineTask):
        """Put item in queue with priority"""
        # Use negative priority for descending order (higher priority first)
        priority_item = (-item.priority, self._task_counter, item)
        self._task_counter += 1
        await self._queue.put(priority_item)
    
    async def get(self) -> PipelineTask:
        """Get highest priority item from queue"""
        start_wait = time.time()
        _, _, item = await self._queue.get()
        
        wait_time = time.time() - start_wait
        self._stats["items_processed"] += 1
        self._stats["total_wait_time"] += wait_time
        self._stats["avg_wait_time"] = (
            self._stats["total_wait_time"] / self._stats["items_processed"]
        )
        
        return item
    
    def task_done(self):
        """Mark task as done"""
        self._queue.task_done()
    
    async def join(self):
        """Wait for all tasks to complete"""
        await self._queue.join()
    
    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return self._stats.copy()

class WorkerPool:
    """Pool of async workers for parallel processing"""
    
    def __init__(self, 
                 worker_count: int = 4,
                 worker_func: Callable = None,
                 name: str = "worker_pool"):
        self.worker_count = worker_count
        self.worker_func = worker_func
        self.name = name
        self.workers: List[asyncio.Task] = []
        self.input_queue = AsyncQueue()
        self.output_queue = AsyncQueue()
        self.running = False
        self.stats = {
            "tasks_processed": 0,
            "total_processing_time": 0,
            "errors": 0,
            "avg_processing_time": 0
        }
    
    async def start(self):
        """Start worker pool"""
        if self.running:
            return
        
        self.running = True
        self.workers = []
        
        for i in range(self.worker_count):
            worker = asyncio.create_task(
                self._worker(f"{self.name}_worker_{i}")
            )
            self.workers.append(worker)
        
        logger.info(f"Started {self.worker_count} workers for {self.name}")
    
    async def stop(self):
        """Stop worker pool"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info(f"Stopped worker pool {self.name}")
    
    async def _worker(self, worker_name: str):
        """Individual worker function"""
        logger.debug(f"Worker {worker_name} started")
        
        while self.running:
            try:
                # Get task from input queue
                task = await asyncio.wait_for(
                    self.input_queue.get(), 
                    timeout=1.0
                )
                
                start_time = time.time()
                
                try:
                    # Process task
                    if self.worker_func:
                        result_data = await self.worker_func(task)
                    else:
                        result_data = await self._default_worker(task)
                    
                    # Create success result
                    result = PipelineResult(
                        task_id=task.id,
                        success=True,
                        data=result_data,
                        duration=time.time() - start_time,
                        stage=task.stage
                    )
                    
                except Exception as e:
                    # Create error result
                    result = PipelineResult(
                        task_id=task.id,
                        success=False,
                        error=str(e),
                        duration=time.time() - start_time,
                        stage=task.stage
                    )
                    self.stats["errors"] += 1
                    logger.error(f"Worker {worker_name} task {task.id} failed: {e}")
                
                # Update stats
                processing_time = result.duration
                self.stats["tasks_processed"] += 1
                self.stats["total_processing_time"] += processing_time
                self.stats["avg_processing_time"] = (
                    self.stats["total_processing_time"] / 
                    self.stats["tasks_processed"]
                )
                
                # Put result in output queue
                await self.output_queue.put(PipelineTask(
                    id=result.task_id,
                    data=result,
                    stage=task.stage
                ))
                
                self.input_queue.task_done()
                
            except asyncio.TimeoutError:
                # Timeout waiting for task - continue
                continue
            except asyncio.CancelledError:
                # Worker cancelled - exit
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} unexpected error: {e}")
        
        logger.debug(f"Worker {worker_name} stopped")
    
    async def _default_worker(self, task: PipelineTask) -> Any:
        """Default worker that just returns task data"""
        await asyncio.sleep(0.1)  # Simulate processing
        return task.data
    
    async def submit_task(self, task: PipelineTask):
        """Submit task to worker pool"""
        await self.input_queue.put(task)
    
    async def get_result(self) -> PipelineResult:
        """Get processed result"""
        result_task = await self.output_queue.get()
        self.output_queue.task_done()
        return result_task.data
    
    def get_stats(self) -> Dict:
        """Get worker pool statistics"""
        return {
            "worker_count": self.worker_count,
            "running": self.running,
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "processing_stats": self.stats,
            "queue_stats": {
                "input": self.input_queue.get_stats(),
                "output": self.output_queue.get_stats()
            }
        }

class AsyncPipeline:
    """Main async processing pipeline"""
    
    def __init__(self, name: str = "pipeline"):
        self.name = name
        self.stages: Dict[PipelineStage, WorkerPool] = {}
        self.running = False
        self.coordinator_task = None
        self.results: Dict[str, PipelineResult] = {}
        self.completion_callbacks: List[Callable] = []
        
    def add_stage(self, 
                  stage: PipelineStage,
                  worker_func: Callable,
                  worker_count: int = 2):
        """Add processing stage to pipeline"""
        pool = WorkerPool(
            worker_count=worker_count,
            worker_func=worker_func,
            name=f"{self.name}_{stage.value}"
        )
        self.stages[stage] = pool
    
    def add_completion_callback(self, callback: Callable):
        """Add callback for when tasks complete"""
        self.completion_callbacks.append(callback)
    
    async def start(self):
        """Start pipeline"""
        if self.running:
            return
        
        self.running = True
        
        # Start all worker pools
        for stage, pool in self.stages.items():
            await pool.start()
        
        # Start coordinator
        self.coordinator_task = asyncio.create_task(self._coordinator())
        
        logger.info(f"Pipeline {self.name} started with {len(self.stages)} stages")
    
    async def stop(self):
        """Stop pipeline"""
        self.running = False
        
        # Stop coordinator
        if self.coordinator_task:
            self.coordinator_task.cancel()
            try:
                await self.coordinator_task
            except asyncio.CancelledError:
                pass
        
        # Stop all worker pools
        for pool in self.stages.values():
            await pool.stop()
        
        logger.info(f"Pipeline {self.name} stopped")
    
    async def _coordinator(self):
        """Coordinate task flow between stages"""
        stage_order = [
            PipelineStage.DATA_FETCH,
            PipelineStage.VALIDATION,
            PipelineStage.ANALYSIS,
            PipelineStage.CORRELATION,
            PipelineStage.RANKING,
            PipelineStage.STORAGE
        ]
        
        while self.running:
            try:
                # Check for completed tasks from each stage
                for i, stage in enumerate(stage_order):
                    if stage not in self.stages:
                        continue
                    
                    pool = self.stages[stage]
                    
                    # Process all available results from this stage
                    while pool.output_queue.qsize() > 0:
                        try:
                            result = await asyncio.wait_for(
                                pool.get_result(), 
                                timeout=0.1
                            )
                            
                            if not result.success:
                                # Task failed - store error result
                                self.results[result.task_id] = result
                                await self._notify_completion(result)
                                continue
                            
                            # Find next stage
                            next_stage_index = i + 1
                            if next_stage_index < len(stage_order):
                                next_stage = stage_order[next_stage_index]
                                
                                if next_stage in self.stages:
                                    # Create task for next stage
                                    next_task = PipelineTask(
                                        id=result.task_id,
                                        data=result.data,
                                        stage=next_stage,
                                        metadata=result.__dict__
                                    )
                                    
                                    await self.stages[next_stage].submit_task(next_task)
                                else:
                                    # No next stage - task complete
                                    self.results[result.task_id] = result
                                    await self._notify_completion(result)
                            else:
                                # Final stage - task complete
                                self.results[result.task_id] = result
                                await self._notify_completion(result)
                        
                        except asyncio.TimeoutError:
                            break
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pipeline coordinator error: {e}")
    
    async def _notify_completion(self, result: PipelineResult):
        """Notify completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Completion callback error: {e}")
    
    async def submit_task(self, 
                         task_id: str,
                         data: Any,
                         priority: int = 0) -> str:
        """Submit task to pipeline"""
        if not self.running:
            raise RuntimeError("Pipeline not running")
        
        # Start with first stage
        first_stage = PipelineStage.DATA_FETCH
        if first_stage not in self.stages:
            raise RuntimeError(f"First stage {first_stage} not configured")
        
        task = PipelineTask(
            id=task_id,
            data=data,
            stage=first_stage,
            priority=priority
        )
        
        await self.stages[first_stage].submit_task(task)
        return task_id
    
    async def get_result(self, task_id: str, timeout: float = 30.0) -> Optional[PipelineResult]:
        """Get result for specific task"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.results:
                return self.results.pop(task_id)
            
            await asyncio.sleep(0.1)
        
        return None  # Timeout
    
    def get_stats(self) -> Dict:
        """Get comprehensive pipeline statistics"""
        stats = {
            "name": self.name,
            "running": self.running,
            "stages": {}
        }
        
        for stage, pool in self.stages.items():
            stats["stages"][stage.value] = pool.get_stats()
        
        stats["pending_results"] = len(self.results)
        
        return stats

class MarketDataPipeline(AsyncPipeline):
    """Specialized pipeline for market data processing"""
    
    def __init__(self):
        super().__init__("market_data_pipeline")
        self._setup_stages()
    
    def _setup_stages(self):
        """Setup market data processing stages"""
        from app.utils.data_validator import MarketDataValidator
        from app.services.inefficiency_detector import InefficiencyDetector
        from app.services.correlation_analyzer import CorrelationAnalyzer
        
        # Data validation stage
        async def validate_data(task: PipelineTask) -> Any:
            data = task.data
            if isinstance(data, dict) and 'market_data' in data:
                # Validate each data point
                validated_data = []
                for item in data['market_data']:
                    is_valid, errors = MarketDataValidator.validate_price_data(item)
                    if is_valid:
                        validated_data.append(item)
                    else:
                        logger.warning(f"Invalid data point: {errors}")
                
                return {**data, 'market_data': validated_data}
            return data
        
        # Analysis stage
        async def analyze_data(task: PipelineTask) -> Any:
            data = task.data
            if isinstance(data, dict) and 'market_data' in data:
                detector = InefficiencyDetector()
                
                # Analyze each ticker
                opportunities = []
                for ticker_data in data['market_data']:
                    ticker = ticker_data.get('ticker', 'UNKNOWN')
                    try:
                        inefficiencies = detector.detect_all_inefficiencies(
                            ticker, [ticker_data], ticker_data
                        )
                        opportunities.extend(inefficiencies)
                    except Exception as e:
                        logger.error(f"Analysis failed for {ticker}: {e}")
                
                return {**data, 'opportunities': opportunities}
            return data
        
        # Correlation stage
        async def correlate_data(task: PipelineTask) -> Any:
            data = task.data
            if isinstance(data, dict) and 'opportunities' in data:
                analyzer = CorrelationAnalyzer()
                
                # Find uncorrelated pairs
                opportunities = data['opportunities']
                if len(opportunities) >= 2:
                    pairs = analyzer.find_uncorrelated_pairs(
                        opportunities, 
                        correlation_threshold=0.3
                    )
                    return {**data, 'uncorrelated_pairs': pairs}
            
            return data
        
        # Ranking stage
        async def rank_opportunities(task: PipelineTask) -> Any:
            data = task.data
            if isinstance(data, dict) and 'opportunities' in data:
                # Sort by inefficiency score
                opportunities = data['opportunities']
                ranked = sorted(
                    opportunities,
                    key=lambda x: x.get('inefficiency_score', 0),
                    reverse=True
                )
                return {**data, 'opportunities': ranked}
            return data
        
        # Add stages to pipeline
        self.add_stage(PipelineStage.VALIDATION, validate_data, worker_count=2)
        self.add_stage(PipelineStage.ANALYSIS, analyze_data, worker_count=4)
        self.add_stage(PipelineStage.CORRELATION, correlate_data, worker_count=2)
        self.add_stage(PipelineStage.RANKING, rank_opportunities, worker_count=1)

# Global pipeline instances
market_pipeline = MarketDataPipeline()

class StreamProcessor:
    """Process streaming data with backpressure handling"""
    
    def __init__(self, 
                 processor_func: Callable,
                 buffer_size: int = 1000,
                 batch_size: int = 100):
        self.processor_func = processor_func
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.buffer = asyncio.Queue(maxsize=buffer_size)
        self.processing = False
        self.processor_task = None
        
    async def start(self):
        """Start stream processing"""
        if self.processing:
            return
        
        self.processing = True
        self.processor_task = asyncio.create_task(self._process_stream())
    
    async def stop(self):
        """Stop stream processing"""
        self.processing = False
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
    
    async def add_data(self, data: Any):
        """Add data to processing stream"""
        try:
            await asyncio.wait_for(self.buffer.put(data), timeout=1.0)
        except asyncio.TimeoutError:
            logger.warning("Stream buffer full - dropping data")
    
    async def _process_stream(self):
        """Process streaming data in batches"""
        while self.processing:
            try:
                batch = []
                
                # Collect batch
                for _ in range(self.batch_size):
                    try:
                        data = await asyncio.wait_for(
                            self.buffer.get(), 
                            timeout=0.1
                        )
                        batch.append(data)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if not empty
                if batch:
                    try:
                        await self.processor_func(batch)
                    except Exception as e:
                        logger.error(f"Stream processing error: {e}")
                
                # Small delay if no data
                if not batch:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream processor error: {e}")

# Utility functions
async def run_parallel_tasks(tasks: List[Callable], max_concurrent: int = 10) -> List[Any]:
    """Run multiple async tasks in parallel with concurrency limit"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_task(task_func):
        async with semaphore:
            return await task_func()
    
    results = await asyncio.gather(
        *[limited_task(task) for task in tasks],
        return_exceptions=True
    )
    
    return results