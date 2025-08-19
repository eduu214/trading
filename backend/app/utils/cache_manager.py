"""
High-performance caching layer for market data and API responses
"""
import asyncio
import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
import pickle
import gzip
import logging

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"       # In-memory cache (fastest)
    L2_REDIS = "l2_redis"         # Redis cache (fast)
    L3_DATABASE = "l3_database"   # Database cache (slower)

class CacheStrategy(Enum):
    LRU = "lru"                   # Least Recently Used
    LFU = "lfu"                   # Least Frequently Used
    TTL = "ttl"                   # Time To Live only
    ADAPTIVE = "adaptive"         # Adaptive based on access patterns

@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""
    key: str
    data: Any
    created_at: float
    accessed_at: float
    access_count: int
    ttl: float
    size_bytes: int
    compressed: bool = False
    
    @property
    def age(self) -> float:
        return time.time() - self.created_at
    
    @property
    def is_expired(self) -> bool:
        return self.ttl > 0 and self.age > self.ttl
    
    @property
    def access_frequency(self) -> float:
        """Calculate access frequency (accesses per hour)"""
        if self.age == 0:
            return float(self.access_count)
        return self.access_count / (self.age / 3600)

class MemoryCache:
    """High-performance in-memory cache (L1)"""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self.entries: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.total_size = 0
        
    def _calculate_size(self, data: Any) -> int:
        """Estimate memory size of data"""
        try:
            return len(pickle.dumps(data))
        except:
            return len(str(data).encode('utf-8'))
    
    def _evict_if_needed(self):
        """Evict entries based on strategy"""
        while len(self.entries) >= self.max_size or self.total_size > 100 * 1024 * 1024:  # 100MB limit
            if not self.entries:
                break
                
            if self.strategy == CacheStrategy.LRU:
                # Remove least recently used
                if self.access_order:
                    key_to_remove = self.access_order.pop(0)
                    if key_to_remove in self.entries:
                        self._remove_entry(key_to_remove)
            
            elif self.strategy == CacheStrategy.LFU:
                # Remove least frequently used
                min_frequency = min(entry.access_frequency for entry in self.entries.values())
                for key, entry in self.entries.items():
                    if entry.access_frequency == min_frequency:
                        self._remove_entry(key)
                        break
            
            elif self.strategy == CacheStrategy.TTL:
                # Remove expired entries first
                expired_keys = [key for key, entry in self.entries.items() if entry.is_expired]
                if expired_keys:
                    for key in expired_keys:
                        self._remove_entry(key)
                else:
                    # Remove oldest if no expired entries
                    oldest_key = min(self.entries.keys(), key=lambda k: self.entries[k].created_at)
                    self._remove_entry(oldest_key)
            
            elif self.strategy == CacheStrategy.ADAPTIVE:
                # Adaptive strategy: prioritize frequently accessed, recent data
                scores = {}
                for key, entry in self.entries.items():
                    # Score based on recency and frequency
                    recency_score = 1.0 / (1.0 + entry.age / 3600)  # Favor recent
                    frequency_score = entry.access_frequency
                    scores[key] = recency_score * frequency_score
                
                if scores:
                    worst_key = min(scores.keys(), key=lambda k: scores[k])
                    self._remove_entry(worst_key)
    
    def _remove_entry(self, key: str):
        """Remove entry and update metadata"""
        if key in self.entries:
            entry = self.entries[key]
            self.total_size -= entry.size_bytes
            del self.entries[key]
            
            if key in self.access_order:
                self.access_order.remove(key)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.entries:
            return None
        
        entry = self.entries[key]
        
        # Check expiration
        if entry.is_expired:
            self._remove_entry(key)
            return None
        
        # Update access metadata
        entry.accessed_at = time.time()
        entry.access_count += 1
        
        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry.data
    
    def set(self, key: str, value: Any, ttl: float = 0):
        """Set value in cache"""
        # Remove existing entry if present
        if key in self.entries:
            self._remove_entry(key)
        
        # Calculate size
        size_bytes = self._calculate_size(value)
        
        # Create entry
        entry = CacheEntry(
            key=key,
            data=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            ttl=ttl,
            size_bytes=size_bytes
        )
        
        # Add to cache
        self.entries[key] = entry
        self.access_order.append(key)
        self.total_size += size_bytes
        
        # Evict if needed
        self._evict_if_needed()
    
    def clear(self):
        """Clear all entries"""
        self.entries.clear()
        self.access_order.clear()
        self.total_size = 0
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        if not self.entries:
            return {
                "entries": 0,
                "total_size_mb": 0,
                "hit_rate": 0,
                "avg_age": 0
            }
        
        total_accesses = sum(entry.access_count for entry in self.entries.values())
        avg_age = sum(entry.age for entry in self.entries.values()) / len(self.entries)
        
        return {
            "entries": len(self.entries),
            "total_size_mb": self.total_size / (1024 * 1024),
            "total_accesses": total_accesses,
            "avg_age_seconds": avg_age,
            "strategy": self.strategy.value
        }

class RedisCache:
    """Redis-based cache (L2)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.namespace = "alphastrat:cache:"
        
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _make_key(self, key: str) -> str:
        """Add namespace to key"""
        return f"{self.namespace}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            await self.connect()
            redis_key = self._make_key(key)
            
            # Get data and metadata
            pipe = self.redis_client.pipeline()
            pipe.hget(redis_key, "data")
            pipe.hget(redis_key, "compressed")
            pipe.hincrby(redis_key, "access_count", 1)
            pipe.hset(redis_key, "accessed_at", time.time())
            
            results = await pipe.execute()
            data_bytes = results[0]
            
            if data_bytes is None:
                return None
            
            # Decompress if needed
            compressed = results[1] == b"1"
            if compressed:
                data_bytes = gzip.decompress(data_bytes)
            
            # Deserialize
            return pickle.loads(data_bytes)
            
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in Redis cache"""
        try:
            await self.connect()
            redis_key = self._make_key(key)
            
            # Serialize data
            data_bytes = pickle.dumps(value)
            
            # Compress if large
            compressed = False
            if len(data_bytes) > 1024:  # Compress if > 1KB
                data_bytes = gzip.compress(data_bytes)
                compressed = True
            
            # Store with metadata
            cache_data = {
                "data": data_bytes,
                "created_at": time.time(),
                "accessed_at": time.time(),
                "access_count": 1,
                "compressed": "1" if compressed else "0",
                "size_bytes": len(data_bytes)
            }
            
            await self.redis_client.hset(redis_key, mapping=cache_data)
            
            if ttl > 0:
                await self.redis_client.expire(redis_key, ttl)
                
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from Redis cache"""
        try:
            await self.connect()
            redis_key = self._make_key(key)
            await self.redis_client.delete(redis_key)
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
    
    async def clear_namespace(self):
        """Clear all keys in namespace"""
        try:
            await self.connect()
            pattern = f"{self.namespace}*"
            
            # Use scan for memory efficiency
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
                    
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")

class MultiLevelCache:
    """Multi-level cache combining memory and Redis"""
    
    def __init__(self, 
                 memory_size: int = 1000,
                 redis_url: str = "redis://localhost:6379"):
        self.l1_cache = MemoryCache(max_size=memory_size, strategy=CacheStrategy.ADAPTIVE)
        self.l2_cache = RedisCache(redis_url)
        self.stats_counters = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "sets": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try L1 cache first
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats_counters["l1_hits"] += 1
            return value
        
        self.stats_counters["l1_misses"] += 1
        
        # Try L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            self.stats_counters["l2_hits"] += 1
            # Promote to L1 cache
            self.l1_cache.set(key, value, ttl=300)  # 5 minute L1 TTL
            return value
        
        self.stats_counters["l2_misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in multi-level cache"""
        self.stats_counters["sets"] += 1
        
        # Set in both levels
        self.l1_cache.set(key, value, ttl=min(ttl, 300))  # Max 5 min in L1
        await self.l2_cache.set(key, value, ttl=ttl)
    
    async def delete(self, key: str):
        """Delete from all cache levels"""
        if key in self.l1_cache.entries:
            self.l1_cache._remove_entry(key)
        await self.l2_cache.delete(key)
    
    async def clear(self):
        """Clear all cache levels"""
        self.l1_cache.clear()
        await self.l2_cache.clear_namespace()
    
    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.stats()
        
        total_requests = (
            self.stats_counters["l1_hits"] + 
            self.stats_counters["l1_misses"]
        )
        
        l1_hit_rate = (
            self.stats_counters["l1_hits"] / total_requests 
            if total_requests > 0 else 0
        )
        
        l2_requests = self.stats_counters["l1_misses"]
        l2_hit_rate = (
            self.stats_counters["l2_hits"] / l2_requests 
            if l2_requests > 0 else 0
        )
        
        overall_hit_rate = (
            (self.stats_counters["l1_hits"] + self.stats_counters["l2_hits"]) / 
            total_requests if total_requests > 0 else 0
        )
        
        return {
            "l1_cache": l1_stats,
            "counters": self.stats_counters,
            "hit_rates": {
                "l1_hit_rate": l1_hit_rate,
                "l2_hit_rate": l2_hit_rate,
                "overall_hit_rate": overall_hit_rate
            }
        }

class MarketDataCache:
    """Specialized cache for market data"""
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
        
    def _make_market_key(self, ticker: str, timeframe: str, start_date: str, end_date: str) -> str:
        """Generate cache key for market data"""
        key_data = f"{ticker}:{timeframe}:{start_date}:{end_date}"
        return f"market_data:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get_market_data(self, ticker: str, timeframe: str, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Get cached market data"""
        key = self._make_market_key(ticker, timeframe, start_date, end_date)
        return await self.cache.get(key)
    
    async def set_market_data(self, ticker: str, timeframe: str, start_date: str, end_date: str, data: List[Dict]):
        """Cache market data"""
        key = self._make_market_key(ticker, timeframe, start_date, end_date)
        # Market data cache for 1 hour (frequently changing)
        await self.cache.set(key, data, ttl=3600)
    
    def _make_scan_key(self, config_hash: str) -> str:
        """Generate cache key for scan results"""
        return f"scan_results:{config_hash}"
    
    async def get_scan_results(self, scan_config: Dict) -> Optional[List[Dict]]:
        """Get cached scan results"""
        config_str = json.dumps(scan_config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        key = self._make_scan_key(config_hash)
        return await self.cache.get(key)
    
    async def set_scan_results(self, scan_config: Dict, results: List[Dict]):
        """Cache scan results"""
        config_str = json.dumps(scan_config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()
        key = self._make_scan_key(config_hash)
        # Scan results cache for 5 minutes (somewhat volatile)
        await self.cache.set(key, results, ttl=300)

# Cache decorator for functions
def cached(ttl: int = 3600, cache_instance: Optional[MultiLevelCache] = None):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = f"func:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Use provided cache or default
            cache = cache_instance or global_cache
            
            # Try to get cached result
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator

# Global cache instances
global_cache = MultiLevelCache()
market_cache = MarketDataCache(global_cache)