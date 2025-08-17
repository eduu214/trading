"""
Memory management utilities for handling large datasets efficiently
"""
import gc
import psutil
import time
import asyncio
import weakref
from typing import Any, Dict, List, Optional, Generator, Iterator, Callable
from dataclasses import dataclass
from contextlib import contextmanager
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_mb: float
    available_mb: float
    used_mb: float
    used_percent: float
    process_mb: float
    process_percent: float

class MemoryMonitor:
    """Monitor system and process memory usage"""
    
    def __init__(self, alert_threshold: float = 80.0):
        self.alert_threshold = alert_threshold
        self.process = psutil.Process()
        self.history: deque = deque(maxlen=100)  # Keep last 100 measurements
        
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        # System memory
        system_mem = psutil.virtual_memory()
        
        # Process memory
        process_mem = self.process.memory_info()
        
        stats = MemoryStats(
            total_mb=system_mem.total / (1024 * 1024),
            available_mb=system_mem.available / (1024 * 1024),
            used_mb=system_mem.used / (1024 * 1024),
            used_percent=system_mem.percent,
            process_mb=process_mem.rss / (1024 * 1024),
            process_percent=self.process.memory_percent()
        )
        
        # Add to history
        self.history.append((time.time(), stats))
        
        # Check for memory pressure
        if stats.used_percent > self.alert_threshold:
            logger.warning(
                f"High memory usage: {stats.used_percent:.1f}% "
                f"(process: {stats.process_mb:.1f}MB)"
            )
        
        return stats
    
    def get_memory_trend(self, minutes: int = 10) -> Dict:
        """Get memory usage trend over time"""
        if not self.history:
            return {"trend": "no_data"}
        
        cutoff_time = time.time() - (minutes * 60)
        recent_stats = [
            (timestamp, stats) for timestamp, stats in self.history
            if timestamp >= cutoff_time
        ]
        
        if len(recent_stats) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate trend
        start_usage = recent_stats[0][1].used_percent
        end_usage = recent_stats[-1][1].used_percent
        change = end_usage - start_usage
        
        return {
            "trend": "increasing" if change > 5 else "decreasing" if change < -5 else "stable",
            "change_percent": change,
            "start_usage": start_usage,
            "end_usage": end_usage,
            "samples": len(recent_stats)
        }

class DataFrameManager:
    """Efficient management of large Pandas DataFrames"""
    
    def __init__(self, memory_limit_mb: float = 1000):
        self.memory_limit_mb = memory_limit_mb
        self.cached_frames: Dict[str, weakref.ref] = {}
        self.frame_sizes: Dict[str, float] = {}
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage"""
        initial_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype
            
            if col_type == 'object':
                # Try to convert to category if few unique values
                unique_ratio = len(optimized_df[col].unique()) / len(optimized_df[col])
                if unique_ratio < 0.5:  # Less than 50% unique values
                    optimized_df[col] = optimized_df[col].astype('category')
            
            elif 'int' in str(col_type):
                # Downcast integers
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='integer')
            
            elif 'float' in str(col_type):
                # Downcast floats
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')
        
        final_memory = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
        reduction = ((initial_memory - final_memory) / initial_memory) * 100
        
        logger.info(
            f"DataFrame optimized: {initial_memory:.1f}MB -> {final_memory:.1f}MB "
            f"({reduction:.1f}% reduction)"
        )
        
        return optimized_df
    
    def cache_dataframe(self, key: str, df: pd.DataFrame):
        """Cache DataFrame with memory tracking"""
        # Remove existing cached frame
        if key in self.cached_frames:
            self.remove_cached_frame(key)
        
        # Check memory limit
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if memory_mb > self.memory_limit_mb:
            logger.warning(
                f"DataFrame {key} ({memory_mb:.1f}MB) exceeds limit "
                f"({self.memory_limit_mb}MB) - not caching"
            )
            return
        
        # Cache with weak reference
        self.cached_frames[key] = weakref.ref(df, self._cleanup_callback(key))
        self.frame_sizes[key] = memory_mb
        
        logger.debug(f"Cached DataFrame {key}: {memory_mb:.1f}MB")
    
    def get_cached_frame(self, key: str) -> Optional[pd.DataFrame]:
        """Get cached DataFrame"""
        if key not in self.cached_frames:
            return None
        
        frame_ref = self.cached_frames[key]
        frame = frame_ref()
        
        if frame is None:
            # Frame was garbage collected
            self.remove_cached_frame(key)
            return None
        
        return frame
    
    def remove_cached_frame(self, key: str):
        """Remove cached DataFrame"""
        if key in self.cached_frames:
            del self.cached_frames[key]
        if key in self.frame_sizes:
            del self.frame_sizes[key]
    
    def _cleanup_callback(self, key: str):
        """Callback for when DataFrame is garbage collected"""
        def callback(ref):
            self.remove_cached_frame(key)
            logger.debug(f"DataFrame {key} garbage collected")
        return callback
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_memory = sum(self.frame_sizes.values())
        active_frames = len([
            key for key in self.cached_frames 
            if self.cached_frames[key]() is not None
        ])
        
        return {
            "active_frames": active_frames,
            "total_cached_frames": len(self.cached_frames),
            "total_memory_mb": total_memory,
            "memory_limit_mb": self.memory_limit_mb,
            "memory_usage_percent": (total_memory / self.memory_limit_mb) * 100
        }

class ChunkedDataProcessor:
    """Process large datasets in chunks to manage memory"""
    
    def __init__(self, chunk_size: int = 10000):
        self.chunk_size = chunk_size
        
    def process_dataframe_chunks(self, 
                                df: pd.DataFrame,
                                processor_func: Callable,
                                **kwargs) -> List[Any]:
        """Process DataFrame in chunks"""
        results = []
        total_chunks = len(df) // self.chunk_size + (1 if len(df) % self.chunk_size else 0)
        
        logger.info(f"Processing {len(df)} rows in {total_chunks} chunks of {self.chunk_size}")
        
        for i in range(0, len(df), self.chunk_size):
            chunk = df.iloc[i:i + self.chunk_size]
            
            try:
                result = processor_func(chunk, **kwargs)
                results.append(result)
                
                # Log progress
                chunk_num = (i // self.chunk_size) + 1
                if chunk_num % 10 == 0 or chunk_num == total_chunks:
                    logger.info(f"Processed chunk {chunk_num}/{total_chunks}")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}-{i + self.chunk_size}: {e}")
                # Continue with next chunk
        
        return results
    
    async def process_async_chunks(self,
                                  data: List[Any],
                                  processor_func: Callable,
                                  max_concurrent: int = 5,
                                  **kwargs) -> List[Any]:
        """Process data chunks asynchronously"""
        chunks = [
            data[i:i + self.chunk_size]
            for i in range(0, len(data), self.chunk_size)
        ]
        
        logger.info(f"Processing {len(data)} items in {len(chunks)} async chunks")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_chunk(chunk_data):
            async with semaphore:
                return await processor_func(chunk_data, **kwargs)
        
        results = await asyncio.gather(
            *[process_chunk(chunk) for chunk in chunks],
            return_exceptions=True
        )
        
        # Filter out exceptions
        successful_results = [
            result for result in results
            if not isinstance(result, Exception)
        ]
        
        failed_count = len(results) - len(successful_results)
        if failed_count > 0:
            logger.warning(f"{failed_count} chunks failed processing")
        
        return successful_results

class MemoryEfficientIterator:
    """Memory-efficient iterator for large datasets"""
    
    def __init__(self, data_source: Any, batch_size: int = 1000):
        self.data_source = data_source
        self.batch_size = batch_size
        
    def __iter__(self):
        return self
    
    def __next__(self):
        # This is a base implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement __next__")

class DatabaseIterator(MemoryEfficientIterator):
    """Memory-efficient iterator for database queries"""
    
    def __init__(self, query, session, batch_size: int = 1000):
        super().__init__(query, batch_size)
        self.query = query
        self.session = session
        self.offset = 0
        self.exhausted = False
    
    def __next__(self):
        if self.exhausted:
            raise StopIteration
        
        # Execute query with limit and offset
        paginated_query = self.query.offset(self.offset).limit(self.batch_size)
        result = self.session.execute(paginated_query)
        batch = result.fetchall()
        
        if not batch:
            self.exhausted = True
            raise StopIteration
        
        self.offset += len(batch)
        
        # Convert to list of dicts if needed
        if hasattr(batch[0], '_asdict'):
            return [row._asdict() for row in batch]
        
        return batch

class ArrayProcessor:
    """Efficient processing of large numpy arrays"""
    
    @staticmethod
    def process_in_blocks(array: np.ndarray,
                         processor_func: Callable,
                         block_size: int = 1000000) -> np.ndarray:
        """Process large array in blocks"""
        if array.size <= block_size:
            return processor_func(array)
        
        results = []
        total_blocks = (array.size + block_size - 1) // block_size
        
        logger.info(f"Processing array of {array.size} elements in {total_blocks} blocks")
        
        for i in range(0, array.size, block_size):
            block = array.flat[i:i + block_size]
            
            try:
                result = processor_func(block)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing block {i//block_size + 1}: {e}")
                # Create placeholder result
                results.append(np.zeros_like(block))
        
        return np.concatenate(results)
    
    @staticmethod
    def efficient_correlation(arrays: List[np.ndarray], 
                            chunk_size: int = 10000) -> np.ndarray:
        """Calculate correlation matrix efficiently for large arrays"""
        n_arrays = len(arrays)
        correlation_matrix = np.eye(n_arrays)
        
        for i in range(n_arrays):
            for j in range(i + 1, n_arrays):
                # Calculate correlation in chunks if arrays are large
                if len(arrays[i]) > chunk_size:
                    correlations = []
                    
                    for start in range(0, len(arrays[i]), chunk_size):
                        end = start + chunk_size
                        chunk_i = arrays[i][start:end]
                        chunk_j = arrays[j][start:end]
                        
                        if len(chunk_i) > 1:  # Need at least 2 points for correlation
                            corr = np.corrcoef(chunk_i, chunk_j)[0, 1]
                            if not np.isnan(corr):
                                correlations.append(corr)
                    
                    # Average correlations from chunks
                    if correlations:
                        final_corr = np.mean(correlations)
                    else:
                        final_corr = 0.0
                else:
                    final_corr = np.corrcoef(arrays[i], arrays[j])[0, 1]
                    if np.isnan(final_corr):
                        final_corr = 0.0
                
                correlation_matrix[i, j] = final_corr
                correlation_matrix[j, i] = final_corr
        
        return correlation_matrix

@contextmanager
def memory_profiler(operation_name: str):
    """Context manager to profile memory usage of operations"""
    monitor = MemoryMonitor()
    
    # Get initial memory
    initial_stats = monitor.get_memory_stats()
    start_time = time.time()
    
    logger.info(
        f"Starting {operation_name} - "
        f"Memory: {initial_stats.process_mb:.1f}MB "
        f"({initial_stats.used_percent:.1f}%)"
    )
    
    try:
        yield monitor
    finally:
        # Get final memory
        final_stats = monitor.get_memory_stats()
        duration = time.time() - start_time
        
        memory_delta = final_stats.process_mb - initial_stats.process_mb
        
        logger.info(
            f"Completed {operation_name} in {duration:.2f}s - "
            f"Memory: {final_stats.process_mb:.1f}MB "
            f"(Δ{memory_delta:+.1f}MB)"
        )
        
        # Force garbage collection if memory increased significantly
        if memory_delta > 100:  # 100MB increase
            logger.info("Forcing garbage collection due to memory increase")
            gc.collect()

def force_garbage_collection():
    """Force garbage collection and log results"""
    initial_stats = MemoryMonitor().get_memory_stats()
    
    # Run garbage collection
    collected = gc.collect()
    
    final_stats = MemoryMonitor().get_memory_stats()
    memory_freed = initial_stats.process_mb - final_stats.process_mb
    
    logger.info(
        f"Garbage collection: collected {collected} objects, "
        f"freed {memory_freed:.1f}MB"
    )

def optimize_for_memory():
    """Apply general memory optimizations"""
    # Configure garbage collection
    gc.set_threshold(700, 10, 10)  # More aggressive collection
    
    # Enable garbage collection debugging in development
    # gc.set_debug(gc.DEBUG_STATS)
    
    logger.info("Applied memory optimizations")

# Global instances
memory_monitor = MemoryMonitor()
dataframe_manager = DataFrameManager()
chunked_processor = ChunkedDataProcessor()

# Utility functions
def get_object_size(obj: Any) -> float:
    """Get approximate size of object in MB"""
    try:
        import sys
        return sys.getsizeof(obj) / (1024 * 1024)
    except:
        return 0.0

def log_memory_usage(func: Callable) -> Callable:
    """Decorator to log memory usage of functions"""
    def wrapper(*args, **kwargs):
        with memory_profiler(func.__name__):
            return func(*args, **kwargs)
    return wrapper