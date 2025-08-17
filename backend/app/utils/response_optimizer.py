"""
API response optimization utilities for faster response times
"""
import asyncio
import time
import gzip
import json
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ResponseMetrics:
    """Metrics for API response optimization"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    response_size_bytes: int
    cache_hit: bool = False
    compressed: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class ResponseOptimizer:
    """Optimize API responses for performance"""
    
    def __init__(self):
        self.metrics_history: List[ResponseMetrics] = []
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.response_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes default
        
    def optimize_response(self, 
                         data: Any,
                         request: Request,
                         cache_key: str = None,
                         ttl: int = None) -> JSONResponse:
        """Optimize API response with caching and compression"""
        start_time = time.time()
        
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = self._generate_cache_key(request)
        
        # Check cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            response_time = (time.time() - start_time) * 1000
            
            # Log metrics
            self._log_metrics(
                request=request,
                response_time_ms=response_time,
                response_size_bytes=len(cached_response),
                cache_hit=True,
                compressed=False
            )
            
            return JSONResponse(
                content=json.loads(cached_response),
                headers={"X-Cache": "HIT"}
            )
        
        # Serialize data
        json_data = self._serialize_data(data)
        response_size = len(json_data.encode('utf-8'))
        
        # Determine if compression is beneficial
        should_compress = (
            response_size > self.compression_threshold and
            self._supports_compression(request)
        )
        
        # Create response
        if should_compress:
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            response = Response(
                content=compressed_data,
                media_type="application/json",
                headers={
                    "Content-Encoding": "gzip",
                    "X-Cache": "MISS",
                    "X-Compressed": "true"
                }
            )
        else:
            response = JSONResponse(
                content=json.loads(json_data),
                headers={
                    "X-Cache": "MISS",
                    "X-Compressed": "false"
                }
            )
        
        # Cache response
        if ttl is None:
            ttl = self.cache_ttl
        
        self._cache_response(cache_key, json_data, ttl)
        
        # Log metrics
        response_time = (time.time() - start_time) * 1000
        self._log_metrics(
            request=request,
            response_time_ms=response_time,
            response_size_bytes=response_size,
            cache_hit=False,
            compressed=should_compress
        )
        
        return response
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data to JSON with optimizations"""
        return json.dumps(
            data,
            separators=(',', ':'),  # Remove whitespace
            ensure_ascii=False,     # Smaller size for unicode
            default=self._json_serializer
        )
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include method, path, and sorted query params
        query_string = str(sorted(request.query_params.items()))
        cache_key = f"{request.method}:{request.url.path}:{query_string}"
        
        # Hash long keys
        if len(cache_key) > 200:
            import hashlib
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        return cache_key
    
    def _supports_compression(self, request: Request) -> bool:
        """Check if client supports gzip compression"""
        accept_encoding = request.headers.get("accept-encoding", "")
        return "gzip" in accept_encoding.lower()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if valid"""
        if cache_key not in self.response_cache:
            return None
        
        cached_data, expiry_time = self.response_cache[cache_key]
        
        if datetime.now() > expiry_time:
            # Cache expired
            del self.response_cache[cache_key]
            return None
        
        return cached_data
    
    def _cache_response(self, cache_key: str, data: str, ttl: int):
        """Cache response data"""
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        self.response_cache[cache_key] = (data, expiry_time)
        
        # Clean up expired entries (simple cleanup)
        if len(self.response_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.response_cache.items()
            if now > expiry
        ]
        
        for key in expired_keys:
            del self.response_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _log_metrics(self, 
                    request: Request,
                    response_time_ms: float,
                    response_size_bytes: int,
                    cache_hit: bool,
                    compressed: bool):
        """Log response metrics"""
        metrics = ResponseMetrics(
            endpoint=request.url.path,
            method=request.method,
            status_code=200,  # Assume success for now
            response_time_ms=response_time_ms,
            response_size_bytes=response_size_bytes,
            cache_hit=cache_hit,
            compressed=compressed
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics (last 1000)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Log slow responses
        if response_time_ms > 1000:  # > 1 second
            logger.warning(
                f"Slow response: {request.method} {request.url.path} "
                f"took {response_time_ms:.1f}ms"
            )
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_entries = len(self.response_cache)
        
        # Calculate cache size
        total_size = sum(
            len(data.encode('utf-8'))
            for data, _ in self.response_cache.values()
        )
        
        return {
            "total_entries": total_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "compression_threshold": self.compression_threshold,
            "default_ttl": self.cache_ttl
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        if not self.metrics_history:
            return {"message": "No metrics available"}
        
        # Calculate statistics from recent metrics
        recent_metrics = self.metrics_history[-100:]  # Last 100 requests
        
        response_times = [m.response_time_ms for m in recent_metrics]
        response_sizes = [m.response_size_bytes for m in recent_metrics]
        
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        compressions = sum(1 for m in recent_metrics if m.compressed)
        
        return {
            "total_requests": len(recent_metrics),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "max_response_time_ms": max(response_times),
            "min_response_time_ms": min(response_times),
            "avg_response_size_bytes": sum(response_sizes) / len(response_sizes),
            "cache_hit_rate": (cache_hits / len(recent_metrics)) * 100,
            "compression_rate": (compressions / len(recent_metrics)) * 100
        }

class DataPaginator:
    """Efficient pagination for large datasets"""
    
    @staticmethod
    def paginate_data(data: List[Any],
                     page: int = 1,
                     page_size: int = 20,
                     max_page_size: int = 100) -> Dict:
        """Paginate data efficiently"""
        # Validate and limit page size
        page_size = min(page_size, max_page_size)
        page = max(1, page)
        
        total_items = len(data)
        total_pages = (total_items + page_size - 1) // page_size
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get page data
        page_data = data[offset:offset + page_size]
        
        return {
            "data": page_data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }
    
    @staticmethod
    def cursor_paginate(data: List[Dict],
                       cursor_field: str = "id",
                       cursor_value: Any = None,
                       limit: int = 20,
                       direction: str = "forward") -> Dict:
        """Cursor-based pagination for better performance"""
        # Filter data based on cursor
        if cursor_value is not None:
            if direction == "forward":
                filtered_data = [
                    item for item in data
                    if item.get(cursor_field, 0) > cursor_value
                ]
            else:  # backward
                filtered_data = [
                    item for item in data
                    if item.get(cursor_field, 0) < cursor_value
                ]
                filtered_data = filtered_data[::-1]  # Reverse for backward
        else:
            filtered_data = data
        
        # Get page data
        page_data = filtered_data[:limit + 1]  # Get one extra to check if there's more
        
        has_more = len(page_data) > limit
        if has_more:
            page_data = page_data[:-1]  # Remove the extra item
        
        # Get next/previous cursors
        next_cursor = None
        previous_cursor = None
        
        if page_data:
            if direction == "forward":
                next_cursor = page_data[-1].get(cursor_field) if has_more else None
                previous_cursor = page_data[0].get(cursor_field)
            else:
                next_cursor = page_data[0].get(cursor_field)
                previous_cursor = page_data[-1].get(cursor_field) if has_more else None
        
        return {
            "data": page_data,
            "pagination": {
                "cursor_field": cursor_field,
                "current_cursor": cursor_value,
                "next_cursor": next_cursor,
                "previous_cursor": previous_cursor,
                "has_more": has_more,
                "limit": limit,
                "direction": direction
            }
        }

class ResponseCompressor:
    """Advanced response compression utilities"""
    
    @staticmethod
    def compress_json(data: Dict, level: int = 6) -> bytes:
        """Compress JSON data with specified compression level"""
        json_str = json.dumps(data, separators=(',', ':'))
        return gzip.compress(json_str.encode('utf-8'), compresslevel=level)
    
    @staticmethod
    def should_compress(data_size: int, 
                       threshold: int = 1024,
                       accept_encoding: str = "") -> bool:
        """Determine if response should be compressed"""
        return (
            data_size > threshold and
            "gzip" in accept_encoding.lower()
        )

class ResponseFormatter:
    """Format responses consistently"""
    
    @staticmethod
    def success_response(data: Any, 
                        message: str = None,
                        metadata: Dict = None) -> Dict:
        """Format successful response"""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        if message:
            response["message"] = message
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def error_response(error_code: str,
                      message: str,
                      details: Any = None,
                      status_code: int = 400) -> Dict:
        """Format error response"""
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    @staticmethod
    def paginated_response(data: List[Any],
                          pagination: Dict,
                          message: str = None) -> Dict:
        """Format paginated response"""
        response = {
            "success": True,
            "data": data,
            "pagination": pagination,
            "timestamp": datetime.now().isoformat()
        }
        
        if message:
            response["message"] = message
        
        return response

class StreamingResponse:
    """Utilities for streaming large responses"""
    
    @staticmethod
    async def stream_json_array(data_generator: Callable,
                               chunk_size: int = 100) -> AsyncGenerator[str, None]:
        """Stream JSON array in chunks"""
        yield '{"data": ['
        
        first_item = True
        chunk = []
        
        async for item in data_generator():
            chunk.append(item)
            
            if len(chunk) >= chunk_size:
                # Yield chunk
                chunk_json = json.dumps(chunk, separators=(',', ':'))
                
                if first_item:
                    yield chunk_json[1:-1]  # Remove array brackets
                    first_item = False
                else:
                    yield f',{chunk_json[1:-1]}'
                
                chunk = []
        
        # Yield remaining items
        if chunk:
            chunk_json = json.dumps(chunk, separators=(',', ':'))
            
            if first_item:
                yield chunk_json[1:-1]
            else:
                yield f',{chunk_json[1:-1]}'
        
        yield ']}'
    
    @staticmethod
    async def stream_csv(data_generator: Callable,
                        headers: List[str]) -> AsyncGenerator[str, None]:
        """Stream CSV data"""
        # Yield headers
        yield ','.join(headers) + '\n'
        
        # Yield data rows
        async for item in data_generator():
            if isinstance(item, dict):
                row = [str(item.get(header, '')) for header in headers]
            else:
                row = [str(field) for field in item]
            
            yield ','.join(row) + '\n'

# Global response optimizer
response_optimizer = ResponseOptimizer()

# Middleware function
async def response_optimization_middleware(request: Request, call_next):
    """Middleware for automatic response optimization"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Add performance headers
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response