"""
High-performance batch processing system for market data operations
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
import queue
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

class BatchProcessingMode(Enum):
    SEQUENTIAL = "sequential"
    ASYNC_CONCURRENT = "async_concurrent"
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"

@dataclass
class BatchJob:
    """Represents a batch processing job"""
    id: str
    data: List[Any]
    processor_func: Callable
    mode: BatchProcessingMode
    priority: int = 0
    created_at: datetime = None
    batch_size: int = 100
    max_workers: int = 4
    timeout: float = 300  # 5 minutes
    retry_count: int = 3
    metadata: Dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class BatchResult:
    """Result from batch processing"""
    job_id: str
    success: bool
    processed_count: int
    failed_count: int
    total_count: int
    results: List[Any] = None
    errors: List[str] = None
    duration: float = 0
    start_time: datetime = None
    end_time: datetime = None
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.processed_count / self.total_count) * 100

class BatchProcessor(Generic[T, R]):
    """High-performance batch processor with multiple execution modes"""
    
    def __init__(self, 
                 default_batch_size: int = 100,
                 max_concurrent_jobs: int = 10):
        self.default_batch_size = default_batch_size
        self.max_concurrent_jobs = max_concurrent_jobs
        self.active_jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: Dict[str, BatchResult] = {}
        self.job_queue = asyncio.Queue()
        self.processing = False
        self.processor_task = None
        self.thread_pool = ThreadPoolExecutor(max_workers=mp.cpu_count())
        self.process_pool = ProcessPoolExecutor(max_workers=mp.cpu_count())
        
    async def start(self):
        """Start the batch processor"""
        if self.processing:
            return
        
        self.processing = True
        self.processor_task = asyncio.create_task(self._process_jobs())
        logger.info("Batch processor started")
    
    async def stop(self):
        """Stop the batch processor"""
        self.processing = False
        
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown executors
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        logger.info("Batch processor stopped")
    
    async def submit_job(self, job: BatchJob) -> str:
        """Submit a batch job for processing"""
        await self.job_queue.put(job)
        self.active_jobs[job.id] = job
        
        logger.info(
            f"Submitted batch job {job.id}: {len(job.data)} items, "
            f"mode={job.mode.value}, batch_size={job.batch_size}"
        )
        
        return job.id
    
    async def get_result(self, job_id: str, timeout: float = None) -> Optional[BatchResult]:
        """Get result for a specific job"""
        start_time = time.time()
        timeout = timeout or 300  # 5 minutes default
        
        while time.time() - start_time < timeout:
            if job_id in self.completed_jobs:
                return self.completed_jobs.pop(job_id)
            
            await asyncio.sleep(0.1)
        
        return None  # Timeout
    
    async def _process_jobs(self):
        """Main job processing loop"""
        while self.processing:
            try:
                # Get job from queue
                job = await asyncio.wait_for(
                    self.job_queue.get(),
                    timeout=1.0
                )
                
                # Check if we have room for another job
                if len(self.active_jobs) >= self.max_concurrent_jobs:
                    # Put job back and wait
                    await self.job_queue.put(job)
                    await asyncio.sleep(0.1)
                    continue
                
                # Process job based on mode
                result = await self._execute_job(job)
                
                # Store result and clean up
                self.completed_jobs[job.id] = result
                if job.id in self.active_jobs:
                    del self.active_jobs[job.id]
                
                logger.info(
                    f"Completed job {job.id}: {result.processed_count}/{result.total_count} "
                    f"items in {result.duration:.2f}s ({result.success_rate:.1f}% success)"
                )
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Job processing error: {e}")
    
    async def _execute_job(self, job: BatchJob) -> BatchResult:
        """Execute a batch job"""
        start_time = datetime.now()
        
        try:
            if job.mode == BatchProcessingMode.SEQUENTIAL:
                result = await self._process_sequential(job)
            elif job.mode == BatchProcessingMode.ASYNC_CONCURRENT:
                result = await self._process_async_concurrent(job)
            elif job.mode == BatchProcessingMode.THREAD_POOL:
                result = await self._process_thread_pool(job)
            elif job.mode == BatchProcessingMode.PROCESS_POOL:
                result = await self._process_process_pool(job)
            else:
                raise ValueError(f"Unknown processing mode: {job.mode}")
            
            result.start_time = start_time
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"Job {job.id} execution failed: {e}")
            
            return BatchResult(
                job_id=job.id,
                success=False,
                processed_count=0,
                failed_count=len(job.data),
                total_count=len(job.data),
                errors=[str(e)],
                start_time=start_time,
                end_time=datetime.now()
            )
    
    async def _process_sequential(self, job: BatchJob) -> BatchResult:
        """Process items sequentially"""
        results = []
        errors = []
        processed_count = 0
        
        # Process in batches
        for i in range(0, len(job.data), job.batch_size):
            batch = job.data[i:i + job.batch_size]
            
            for item in batch:
                try:
                    result = await self._safe_execute(job.processor_func, item)
                    results.append(result)
                    processed_count += 1
                except Exception as e:
                    errors.append(f"Item {i}: {str(e)}")
        
        return BatchResult(
            job_id=job.id,
            success=len(errors) == 0,
            processed_count=processed_count,
            failed_count=len(errors),
            total_count=len(job.data),
            results=results,
            errors=errors
        )
    
    async def _process_async_concurrent(self, job: BatchJob) -> BatchResult:
        """Process items using async concurrency"""
        semaphore = asyncio.Semaphore(job.max_workers)
        
        async def process_item(item, index):
            async with semaphore:
                try:
                    result = await self._safe_execute(job.processor_func, item)
                    return {"index": index, "result": result, "error": None}
                except Exception as e:
                    return {"index": index, "result": None, "error": str(e)}
        
        # Create tasks for all items
        tasks = [
            process_item(item, i) 
            for i, item in enumerate(job.data)
        ]
        
        # Execute with timeout
        try:
            task_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=job.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Job {job.id} timed out after {job.timeout}s")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            task_results = []
        
        # Process results
        results = []
        errors = []
        processed_count = 0
        
        for task_result in task_results:
            if isinstance(task_result, Exception):
                errors.append(str(task_result))
            elif task_result["error"]:
                errors.append(f"Item {task_result['index']}: {task_result['error']}")
            else:
                results.append(task_result["result"])
                processed_count += 1
        
        return BatchResult(
            job_id=job.id,
            success=len(errors) == 0,
            processed_count=processed_count,
            failed_count=len(errors),
            total_count=len(job.data),
            results=results,
            errors=errors
        )
    
    async def _process_thread_pool(self, job: BatchJob) -> BatchResult:
        """Process items using thread pool"""
        loop = asyncio.get_event_loop()
        
        def process_batch(batch):
            batch_results = []
            batch_errors = []
            
            for i, item in enumerate(batch):
                try:
                    # For thread pool, function must be synchronous
                    if asyncio.iscoroutinefunction(job.processor_func):
                        # Can't run async function in thread pool
                        raise ValueError("Cannot use async function with thread pool mode")
                    
                    result = job.processor_func(item)
                    batch_results.append(result)
                except Exception as e:
                    batch_errors.append(f"Item {i}: {str(e)}")
            
            return batch_results, batch_errors
        
        # Split into batches and process in parallel
        batches = [
            job.data[i:i + job.batch_size]
            for i in range(0, len(job.data), job.batch_size)
        ]
        
        # Submit batches to thread pool
        futures = [
            loop.run_in_executor(self.thread_pool, process_batch, batch)
            for batch in batches
        ]
        
        # Wait for completion with timeout
        try:
            batch_results = await asyncio.wait_for(
                asyncio.gather(*futures),
                timeout=job.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Job {job.id} timed out in thread pool")
            batch_results = []
        
        # Combine results
        all_results = []
        all_errors = []
        processed_count = 0
        
        for results, errors in batch_results:
            all_results.extend(results)
            all_errors.extend(errors)
            processed_count += len(results)
        
        return BatchResult(
            job_id=job.id,
            success=len(all_errors) == 0,
            processed_count=processed_count,
            failed_count=len(all_errors),
            total_count=len(job.data),
            results=all_results,
            errors=all_errors
        )
    
    async def _process_process_pool(self, job: BatchJob) -> BatchResult:
        """Process items using process pool"""
        loop = asyncio.get_event_loop()
        
        # For process pool, function must be picklable
        if not callable(job.processor_func):
            raise ValueError("Processor function must be callable for process pool")
        
        # Split into batches
        batches = [
            job.data[i:i + job.batch_size]
            for i in range(0, len(job.data), job.batch_size)
        ]
        
        # Submit batches to process pool
        futures = [
            loop.run_in_executor(
                self.process_pool, 
                self._process_batch_in_process, 
                batch, 
                job.processor_func
            )
            for batch in batches
        ]
        
        # Wait for completion with timeout
        try:
            batch_results = await asyncio.wait_for(
                asyncio.gather(*futures),
                timeout=job.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Job {job.id} timed out in process pool")
            batch_results = []
        
        # Combine results
        all_results = []
        all_errors = []
        processed_count = 0
        
        for results, errors in batch_results:
            all_results.extend(results)
            all_errors.extend(errors)
            processed_count += len(results)
        
        return BatchResult(
            job_id=job.id,
            success=len(all_errors) == 0,
            processed_count=processed_count,
            failed_count=len(all_errors),
            total_count=len(job.data),
            results=all_results,
            errors=all_errors
        )
    
    @staticmethod
    def _process_batch_in_process(batch, processor_func):
        """Process batch in separate process"""
        results = []
        errors = []
        
        for i, item in enumerate(batch):
            try:
                result = processor_func(item)
                results.append(result)
            except Exception as e:
                errors.append(f"Item {i}: {str(e)}")
        
        return results, errors
    
    async def _safe_execute(self, func: Callable, *args, **kwargs):
        """Safely execute function (async or sync)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def get_stats(self) -> Dict:
        """Get batch processor statistics"""
        return {
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "queue_size": self.job_queue.qsize(),
            "thread_pool_workers": self.thread_pool._max_workers,
            "process_pool_workers": self.process_pool._max_workers,
            "processing": self.processing
        }

class MarketDataBatchProcessor:
    """Specialized batch processor for market data operations"""
    
    def __init__(self):
        self.processor = BatchProcessor()
        
    async def start(self):
        await self.processor.start()
    
    async def stop(self):
        await self.processor.stop()
    
    async def batch_analyze_tickers(self, 
                                   tickers: List[str],
                                   analyzer_func: Callable,
                                   batch_size: int = 50,
                                   mode: BatchProcessingMode = BatchProcessingMode.ASYNC_CONCURRENT) -> str:
        """Batch analyze multiple tickers"""
        job = BatchJob(
            id=f"analyze_tickers_{int(time.time())}",
            data=tickers,
            processor_func=analyzer_func,
            mode=mode,
            batch_size=batch_size,
            max_workers=10,
            timeout=600  # 10 minutes
        )
        
        return await self.processor.submit_job(job)
    
    async def batch_fetch_market_data(self,
                                    requests: List[Dict],
                                    fetcher_func: Callable,
                                    batch_size: int = 20) -> str:
        """Batch fetch market data"""
        job = BatchJob(
            id=f"fetch_data_{int(time.time())}",
            data=requests,
            processor_func=fetcher_func,
            mode=BatchProcessingMode.ASYNC_CONCURRENT,
            batch_size=batch_size,
            max_workers=5,  # Respect rate limits
            timeout=900  # 15 minutes
        )
        
        return await self.processor.submit_job(job)
    
    async def batch_calculate_correlations(self,
                                         price_data: List[Dict],
                                         correlation_func: Callable,
                                         batch_size: int = 100) -> str:
        """Batch calculate correlations"""
        job = BatchJob(
            id=f"correlations_{int(time.time())}",
            data=price_data,
            processor_func=correlation_func,
            mode=BatchProcessingMode.PROCESS_POOL,  # CPU intensive
            batch_size=batch_size,
            max_workers=mp.cpu_count(),
            timeout=1200  # 20 minutes
        )
        
        return await self.processor.submit_job(job)
    
    async def get_result(self, job_id: str, timeout: float = 300) -> Optional[BatchResult]:
        """Get result for batch job"""
        return await self.processor.get_result(job_id, timeout)

class StreamBatchProcessor:
    """Process streaming data in batches"""
    
    def __init__(self, 
                 batch_size: int = 100,
                 flush_interval: float = 5.0,
                 processor_func: Callable = None):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.processor_func = processor_func
        self.current_batch = []
        self.last_flush = time.time()
        self.processing = False
        self.flush_task = None
        
    async def start(self):
        """Start stream batch processor"""
        if self.processing:
            return
        
        self.processing = True
        self.flush_task = asyncio.create_task(self._periodic_flush())
        logger.info("Stream batch processor started")
    
    async def stop(self):
        """Stop stream batch processor"""
        self.processing = False
        
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining items
        if self.current_batch:
            await self._flush_batch()
        
        logger.info("Stream batch processor stopped")
    
    async def add_item(self, item: Any):
        """Add item to current batch"""
        self.current_batch.append(item)
        
        # Flush if batch is full
        if len(self.current_batch) >= self.batch_size:
            await self._flush_batch()
    
    async def _periodic_flush(self):
        """Periodically flush batches"""
        while self.processing:
            try:
                await asyncio.sleep(self.flush_interval)
                
                if (self.current_batch and 
                    time.time() - self.last_flush >= self.flush_interval):
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic flush error: {e}")
    
    async def _flush_batch(self):
        """Flush current batch"""
        if not self.current_batch:
            return
        
        batch = self.current_batch.copy()
        self.current_batch.clear()
        self.last_flush = time.time()
        
        if self.processor_func:
            try:
                await self._safe_execute(self.processor_func, batch)
                logger.debug(f"Processed batch of {len(batch)} items")
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
    
    async def _safe_execute(self, func: Callable, *args, **kwargs):
        """Safely execute function"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

# Global instances
market_batch_processor = MarketDataBatchProcessor()

# Utility functions
def create_cpu_intensive_job(data: List[Any], 
                           processor_func: Callable,
                           batch_size: int = None) -> BatchJob:
    """Create job optimized for CPU-intensive processing"""
    return BatchJob(
        id=f"cpu_job_{int(time.time())}",
        data=data,
        processor_func=processor_func,
        mode=BatchProcessingMode.PROCESS_POOL,
        batch_size=batch_size or max(1, len(data) // mp.cpu_count()),
        max_workers=mp.cpu_count(),
        timeout=3600  # 1 hour for CPU intensive tasks
    )

def create_io_intensive_job(data: List[Any],
                          processor_func: Callable,
                          batch_size: int = 50) -> BatchJob:
    """Create job optimized for I/O-intensive processing"""
    return BatchJob(
        id=f"io_job_{int(time.time())}",
        data=data,
        processor_func=processor_func,
        mode=BatchProcessingMode.ASYNC_CONCURRENT,
        batch_size=batch_size,
        max_workers=20,  # Higher concurrency for I/O
        timeout=1800  # 30 minutes
    )