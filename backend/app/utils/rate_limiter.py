"""
Rate limiting and queue management for API calls
"""
import time
import asyncio
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter with queuing for API calls
    """
    def __init__(self, 
                 calls_per_minute: int = 5,
                 calls_per_second: Optional[int] = None,
                 burst_size: int = 10):
        self.calls_per_minute = calls_per_minute
        self.calls_per_second = calls_per_second or calls_per_minute // 60
        self.burst_size = burst_size
        
        # Track call times
        self.call_times: deque = deque(maxlen=calls_per_minute)
        self.queue: deque = deque()
        self.processing = False
        
        # Rate limit tracking
        self.last_reset = datetime.now()
        self.calls_this_minute = 0
        self.calls_this_second = 0
        self.last_second = time.time()
        
    def is_rate_limited(self) -> bool:
        """Check if we're currently rate limited"""
        now = time.time()
        
        # Check per-second limit
        if now - self.last_second >= 1:
            self.calls_this_second = 0
            self.last_second = now
        
        if self.calls_this_second >= self.calls_per_second:
            return True
        
        # Check per-minute limit
        if datetime.now() - self.last_reset >= timedelta(minutes=1):
            self.calls_this_minute = 0
            self.last_reset = datetime.now()
        
        if self.calls_this_minute >= self.calls_per_minute:
            return True
        
        return False
    
    async def acquire(self, priority: int = 0) -> bool:
        """
        Acquire permission to make an API call
        Higher priority = processed first
        """
        if not self.is_rate_limited():
            self.calls_this_minute += 1
            self.calls_this_second += 1
            self.call_times.append(time.time())
            return True
        
        # Add to queue
        future = asyncio.Future()
        self.queue.append((priority, time.time(), future))
        
        # Sort queue by priority
        self.queue = deque(sorted(self.queue, key=lambda x: (-x[0], x[1])))
        
        # Start processing queue if not already
        if not self.processing:
            asyncio.create_task(self._process_queue())
        
        return await future
    
    async def _process_queue(self):
        """Process queued requests"""
        self.processing = True
        
        while self.queue:
            if not self.is_rate_limited():
                priority, timestamp, future = self.queue.popleft()
                
                # Check if request is too old (timeout)
                if time.time() - timestamp > 30:  # 30 second timeout
                    future.set_exception(TimeoutError("Request timed out in rate limit queue"))
                    continue
                
                self.calls_this_minute += 1
                self.calls_this_second += 1
                self.call_times.append(time.time())
                future.set_result(True)
            else:
                # Wait before checking again
                await asyncio.sleep(0.1)
        
        self.processing = False
    
    def get_wait_time(self) -> float:
        """Get estimated wait time until next available slot"""
        if not self.is_rate_limited():
            return 0.0
        
        # Calculate based on oldest call
        if self.call_times:
            oldest_call = self.call_times[0]
            time_since_oldest = time.time() - oldest_call
            
            if time_since_oldest < 60:
                return 60 - time_since_oldest
        
        return 1.0  # Default wait

class PolygonRateLimiter(RateLimiter):
    """
    Specific rate limiter for Polygon.io API
    Free tier: 5 API calls/minute
    """
    def __init__(self):
        super().__init__(
            calls_per_minute=5,
            calls_per_second=1,
            burst_size=2
        )
        self.last_429 = None
        self.consecutive_429s = 0
    
    def handle_429_response(self):
        """Handle 429 (Too Many Requests) response"""
        self.last_429 = datetime.now()
        self.consecutive_429s += 1
        
        # Exponential backoff
        wait_time = min(60, 2 ** self.consecutive_429s)
        
        logger.warning(
            f"Received 429 response. Consecutive 429s: {self.consecutive_429s}. "
            f"Waiting {wait_time} seconds"
        )
        
        return wait_time
    
    def reset_429_counter(self):
        """Reset 429 counter after successful request"""
        if self.consecutive_429s > 0:
            logger.info(f"Resetting 429 counter from {self.consecutive_429s}")
            self.consecutive_429s = 0

class AlpacaRateLimiter(RateLimiter):
    """
    Specific rate limiter for Alpaca API
    Paper trading: 200 requests/minute
    """
    def __init__(self):
        super().__init__(
            calls_per_minute=200,
            calls_per_second=5,
            burst_size=20
        )

# Global rate limiters
polygon_limiter = PolygonRateLimiter()
alpaca_limiter = AlpacaRateLimiter()

async def rate_limited_call(
    func: Callable,
    limiter: RateLimiter,
    *args,
    priority: int = 0,
    **kwargs
) -> Any:
    """
    Make a rate-limited API call
    
    Args:
        func: The function to call
        limiter: The rate limiter to use
        priority: Priority in queue (higher = first)
        *args, **kwargs: Arguments for the function
    """
    # Wait for rate limit
    await limiter.acquire(priority)
    
    try:
        # Make the actual call
        result = await func(*args, **kwargs)
        
        # Reset 429 counter on success if applicable
        if hasattr(limiter, 'reset_429_counter'):
            limiter.reset_429_counter()
        
        return result
    except Exception as e:
        # Handle 429 responses
        if hasattr(e, 'status_code') and e.status_code == 429:
            if hasattr(limiter, 'handle_429_response'):
                wait_time = limiter.handle_429_response()
                await asyncio.sleep(wait_time)
                # Retry with higher priority
                return await rate_limited_call(
                    func, limiter, *args, 
                    priority=priority + 1, **kwargs
                )
        raise